"""Check the actual direct-from-DataFrame outputs saved in the executed notebook."""
from html.parser import HTMLParser
import json
from pathlib import Path

import nbformat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/figures/process'


class ChartFrames(HTMLParser):
    def __init__(self):
        super().__init__()
        self.frames = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'iframe' and values.get('title', '').startswith('FlightWise cell:'):
            self.frames.append(values['srcdoc'])


def main():
    notebook = nbformat.read(ROOT / 'notebooks/dashboard_preview.ipynb', as_version=4)
    parser = ChartFrames()
    for cell in notebook.cells:
        if cell.cell_type != 'code':
            continue
        assert cell.execution_count is not None
        assert not any(output.output_type == 'error' for output in cell.outputs)
        for output in cell.outputs:
            parser.feed(output.get('data', {}).get('text/html', ''))
    assert parser.frames, 'No direct D3 outputs saved in notebook'
    OUT.mkdir(parents=True, exist_ok=True)
    results, seen = [], set()
    with sync_playwright() as p:
        installed = [Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),
                     Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')]
        executable = next((str(path) for path in installed if path.exists()), None)
        browser = p.chromium.launch(headless=True, executable_path=executable)
        page = browser.new_page(viewport={'width': 1100, 'height': 850})
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        heatmap_document = None
        for index, document in enumerate(parser.frames):
            page.set_content(document)
            page.wait_for_function('window.chartReady === true')
            data = page.evaluate('window.chartInput')
            kind, rows = data['kind'], data['rows']
            assert page.locator('svg').count() == 1
            assert 'NaN' not in page.locator('svg').inner_html()
            if kind == 'map':
                assert page.locator('.airport').count() == len(rows)
            elif kind == 'heatmap':
                assert page.locator('.cell').count() == len(rows) == 168
                heatmap_document = heatmap_document or document
            elif kind == 'bars':
                actual = page.locator('.bar-detail').count()
                expected = sum(row['scheduled_count'] > 0 for row in rows)
                assert actual == expected, f'Output {index}: expected {expected} airline bars, found {actual}; errors={errors}'
            elif kind == 'histogram':
                assert page.locator('.bin').count() == len(rows)
            elif kind == 'lines':
                assert page.locator('.rate-point').count() == sum(row['y'] is not None for row in rows)
            elif kind == 'scatter':
                assert page.locator('.airport-scatter').count() == sum(row['x'] > 0 and row['y'] is not None for row in rows)
            elif kind == 'hourly_overview':
                assert page.locator('.hour-bar').count() == 24
                assert page.locator('.hour-rate').count() == sum(row['arrival_eligible_count'] > 0 for row in rows)
                assert page.locator('.share-axis').count() == 1
                assert page.locator('.rate-axis').count() == 1
                # Both marks occupy the same vertical plotting area, rather than stacked panels.
                assert page.evaluate('''() => {
                    const bars = [...document.querySelectorAll('.hour-bar')];
                    const points = [...document.querySelectorAll('.hour-rate')];
                    return bars.some(bar => points.some(point =>
                        Number(point.getAttribute('cy')) >= Number(bar.getAttribute('y')) &&
                        Number(point.getAttribute('cy')) <= Number(bar.getAttribute('y')) + Number(bar.getAttribute('height'))));
                }''')
            # Check marks actually expose the data, including keyboard-accessible details.
            if page.locator('.mark').count():
                mark = page.locator('.mark').first
                mark.focus()
                assert page.locator('.fw-tooltip').is_visible()
                assert page.locator('.fw-tooltip').inner_text() == mark.get_attribute('aria-label')
                mark.evaluate('(element) => element.blur()')
            if kind not in seen or (kind == 'lines' and 'hour' in data['options'].get('xLabel', '').lower()):
                name = 'hour_lines' if kind == 'lines' and kind in seen else kind
                page.locator('svg').screenshot(path=str(OUT / f'{name}.png'))
            seen.add(kind)
            results.append({'output': index, 'kind': kind, 'input_rows': len(rows),
                            'origin': data['options'].get('origin')})
        # Changing the supplied values must change the rendered values, not reuse a saved image.
        page.set_content(heatmap_document)
        page.wait_for_function('window.chartReady === true')
        page.evaluate('''() => {
            const input = window.chartInput;
            const changed = input.rows.map((row, i) => i === 0
                ? {...row, scheduled_count: 100, cancellation_eligible_count: 100,
                   cancelled_count: 0, late_count: 50, arrival_eligible_count: 100} : row);
            window.chart.update({...input.options, cells: changed});
        }''')
        assert '50 / 100 eligible flights (50.0%)' in page.locator('.cell').first.get_attribute('aria-label')
        assert page.locator('.cell').count() == 168
        # Mutation above is an explicitly synthetic browser check, never persisted into figures/data.
        assert not errors, errors
        assert not requests, f'Notebook charts requested external resources: {requests}'
        report = {'browser': browser.version, 'outputs': results, 'console_errors': errors,
                  'external_requests': requests, 'direct_data_update_check': True,
                  'note': 'Each document is extracted from a saved notebook output. No exported SVG inputs or running API.'}
        (OUT / 'browser_checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        browser.close()
    print(f'Passed: {len(results)} direct D3 outputs, input counts, keyboard details, and changed-data rendering.')


if __name__ == '__main__':
    main()
