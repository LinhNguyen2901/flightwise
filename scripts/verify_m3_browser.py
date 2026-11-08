"""Check that the M3 dashboard renders the real API data in Chrome."""
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True,
        executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:5173/', wait_until='networkidle')
    page.get_by_text('1,785,449', exact=True).wait_for()
    assert page.locator('svg[role="group"]').count() == 4
    assert page.locator('.airport').count() == 340
    assert page.locator('.cell').count() == 168
    assert page.locator('svg[aria-label="Airport map"]').get_by_text('50%+').count() == 1
    assert page.locator('svg[aria-label="Departure hour and weekday heatmap"]').get_by_text('100%').count() == 1
    assert page.locator('.carrier-row').count() == 14
    assert page.locator('svg[aria-label="Scheduled flights and arrival-late rate by local hour"] .hour-bar').count() == 24
    assert not errors, errors

    main_map = page.locator('g[data-region="main"] g[clip-path] > g').first
    alaska_map = page.locator('g[data-region="AK"] g[clip-path] > g').first
    alaska_before = alaska_map.get_attribute('transform')
    main_labels = page.locator('g[data-region="main"] .airport-label')
    initial_labels = main_labels.count()
    atl = page.locator('.airport[data-origin="ATL"]')
    initial_radius = float(atl.get_attribute('r'))
    panel = page.locator('g[data-region="main"] > rect').bounding_box()
    x, y = panel['x'] + panel['width'] / 2, panel['y'] + panel['height'] / 2
    page.mouse.move(x, y)
    page.mouse.wheel(0, -500)
    page.wait_for_function("() => document.querySelector('g[data-region=main] g[clip-path] > g').getAttribute('transform').includes('scale(') && !document.querySelector('g[data-region=main] g[clip-path] > g').getAttribute('transform').includes('scale(1)')")
    assert float(atl.get_attribute('r')) < initial_radius
    assert main_labels.count() > initial_labels
    assert alaska_map.get_attribute('transform') == alaska_before
    page.mouse.wheel(0, -500)
    assert all(label.isalnum() and len(label) == 3 for label in main_labels.all_text_contents())
    zoomed = main_map.get_attribute('transform')
    page.locator('.chart-card').first.screenshot(path=str(ROOT / 'docs/figures/m3_map_zoom.png'))
    page.mouse.move(panel['x'] + 100, panel['y'] + 12)
    page.mouse.down()
    page.mouse.move(panel['x'] + 140, panel['y'] + 12, steps=5)
    page.mouse.up()
    assert main_map.get_attribute('transform') != zoomed
    page.locator('.airport[data-origin="ATL"]').focus()
    assert 'Scheduled:' in page.locator('.fw-tooltip:not([hidden])').inner_text()
    page.get_by_role('button', name='Reset map').click()
    assert main_map.get_attribute('transform') == 'translate(0,0) scale(1)'

    page.locator('.airport[data-origin="ATL"]').focus()
    assert 'Scheduled:' in page.locator('.fw-tooltip:not([hidden])').inner_text()
    page.locator('.cell[data-cell="1:8"]').focus()
    assert 'eligible flights' in page.locator('.fw-tooltip:not([hidden])').inner_text()
    page.locator('h1').click()
    output = ROOT / 'docs/figures/m3_dashboard.png'
    page.screenshot(path=str(output), full_page=True)

    page.set_viewport_size({'width': 420, 'height': 800})
    page.screenshot(path=str(ROOT / 'docs/figures/m3_narrow.png'), full_page=True)
    assert not errors, errors

    page.route('http://127.0.0.1:8000/api/**', lambda route: route.abort())
    page.reload(wait_until='networkidle')
    page.get_by_role('alert').wait_for()
    page.unroute('http://127.0.0.1:8000/api/**')
    page.get_by_role('button', name='Retry').click()
    page.locator('.airport').first.wait_for()
    assert page.locator('.airport').count() == 340
    assert not errors, errors

    page.route('http://127.0.0.1:8000/api/airports',
        lambda route: route.fulfill(status=200, content_type='application/json', body='[]'))
    page.reload(wait_until='networkidle')
    page.get_by_text('No chart data is available for this period.').wait_for()
    assert page.locator('svg[role="group"]').count() == 0
    browser.close()

print(f'M3 browser checks passed. Screenshot: {output}')
