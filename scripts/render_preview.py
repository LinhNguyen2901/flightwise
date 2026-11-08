"""Render the M1.6 D3 review harness in a real browser and export its SVGs."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from notebooks.preview_support import preview_document
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=True)
    document = preview_document(payload)
    html_path = args.output / 'dashboard_preview.html'
    html_path.write_text(document, encoding='utf-8')
    with sync_playwright() as p:
        installed = [Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),
                     Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')]
        executable = next((str(path) for path in installed if path.exists()), None)
        browser = p.chromium.launch(headless=True, executable_path=executable)
        page = browser.new_page(viewport={'width': 1160, 'height': 1000}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(html_path.resolve().as_uri())
        page.wait_for_function('window.previewReady === true')
        assert page.locator('#map .airport').count() == len(payload['airports'])
        assert page.locator('#heatmap .cell').count() == 168
        scenarios = page.evaluate('window.preview.scenarios')
        checks = []
        for scenario in scenarios:
            page.select_option('#scenario', scenario['id'])
            assert page.locator('#heatmap .cell').count() == 168
            assert page.locator('#map .airport').count() == len(payload['airports'])
            kinds = ['map'] if scenario.get('hour') is not None else ['heatmap', 'bars']
            if scenario['id'] in ['overview', 'jfk']:
                kinds = ['map', *kinds]
            for kind in kinds:
                svg = page.locator(f'#{kind} svg').evaluate('(svg) => new XMLSerializer().serializeToString(svg)')
                (args.output / f'{scenario["id"]}_{kind}.svg').write_text(svg, encoding='utf-8')
                if scenario['id'] == 'overview':
                    page.locator(f'#{kind}').screenshot(path=str(args.output / f'overview_{kind}.png'))
            if scenario['id'] in ['overview', 'jfk_mon08', 'abe_fri17', 'bqn_empty']:
                page.locator('.preview').screenshot(path=str(args.output / f'{scenario["id"]}.png'))
            checks.append({'scenario': scenario['id'], 'airports': len(payload['airports']), 'heatmap_cells': 168})
        for kind in ['layout', 'coordination', 'architecture', 'states', 'playback']:
            svg = page.locator(f'[data-diagram="{kind}"] svg').evaluate('(svg) => new XMLSerializer().serializeToString(svg)')
            (args.output / f'{kind}.svg').write_text(svg, encoding='utf-8')
        # Inspect tooltip behavior, not only screenshot presence.
        if payload.get('no_eligible'):
            page.select_option('#scenario', 'no_eligible')
            day, hour = payload['no_eligible']['cells'][0]
            empty_rate = page.locator(f'[data-cell="{day}:{hour}"]')
            assert empty_rate.get_attribute('data-status') == 'no_eligible_arrivals'
            assert empty_rate.get_attribute('fill').startswith('url(')
        page.select_option('#scenario', 'abe_fri17')
        assert page.locator('#bars [data-status="low_n"]').count() > 0
        assert '0.0%' in page.locator('#bars').inner_text()
        page.select_option('#scenario', 'bqn_empty')
        assert 'No flights in this selection' in page.locator('#bars').inner_text()
        page.select_option('#scenario', 'jfk_mon08')
        cell = page.locator('[data-cell="1:8"]')
        cell.focus()
        tooltip = page.locator('#heatmap .fw-tooltip')
        assert tooltip.is_visible()
        assert 'Cancelled:' in tooltip.inner_text() and 'eligible' in tooltip.inner_text()
        cell.press('Tab')
        assert page.locator('#heatmap .cell:focus').count() == 1
        page.set_viewport_size({'width': 420, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(args.output / 'narrow_viewport.png'))
        # Repeated updates must not accumulate SVGs/tooltips.
        for _ in range(3):
            page.select_option('#scenario', 'abe')
            page.select_option('#scenario', 'overview')
        assert page.locator('.fw-chart').count() == 3
        assert page.locator('.fw-tooltip').count() == 3
        page.evaluate('window.preview.destroy()')
        assert page.locator('.fw-chart').count() == 0
        assert not errors, errors
        report = {'browser': browser.version, 'scenarios': checks, 'console_errors': errors,
                  'checks': ['all airports represented', '168 cells in every context',
                             'keyboard tooltip includes counts and cancellations', 'keyboard traversal',
                             '420px page has no horizontal overflow (charts scroll internally)',
                             'updates do not accumulate surfaces', 'destroy removes chart surfaces'],
                  'scope': 'D3 preview harness only; no API, React, brushing or animation validation'}
        (args.output / 'browser_checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        browser.close()
    print(f'Exported {len(scenarios)} D3 review contexts and 5 diagrams to {args.output}')


if __name__ == '__main__':
    main()
