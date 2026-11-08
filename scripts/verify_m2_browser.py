"""Open the running M2 app and check real data plus retry behavior."""
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True,
        executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
    page = browser.new_page(viewport={'width': 1100, 'height': 800})
    page.goto('http://127.0.0.1:5173/', wait_until='networkidle')
    page.get_by_text('1,785,449').wait_for()
    assert page.get_by_text('340', exact=True).is_visible()
    assert page.get_by_text('1,937', exact=True).is_visible()
    output = ROOT / 'docs/figures/m2_foundation.png'
    page.screenshot(path=str(output), full_page=True)

    page.route('http://127.0.0.1:8000/api/**', lambda route: route.abort())
    page.reload(wait_until='networkidle')
    page.get_by_role('alert').wait_for()
    page.unroute('http://127.0.0.1:8000/api/**')
    page.get_by_role('button', name='Retry').click()
    page.get_by_text('1,785,449').wait_for()
    assert not page.get_by_role('alert').count()
    browser.close()

print(f'Passed real-data load, visible API failure, and retry. Screenshot: {output}')
