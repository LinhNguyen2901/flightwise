"""Smoke-check a fresh install on alternate local ports (8001 and 5175)."""
from playwright.sync_api import sync_playwright


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True,
        executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:5175/', wait_until='networkidle')
    page.get_by_text('1,785,449', exact=True).wait_for()
    assert page.locator('svg[role="group"]').count() == 4
    assert page.locator('.airport').count() == 340
    page.locator('.airport[data-origin="ATL"]').focus()
    page.keyboard.press('Enter')
    page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('ATL')")
    page.locator('.cell[data-cell="1:8"]').focus()
    page.keyboard.press('Enter')
    assert page.locator('.cell[aria-pressed="true"]').count() == 1
    assert '1 selected time cell' in page.locator('svg[aria-label="Airline comparison"] desc').text_content()
    page.get_by_role('button', name='Reset all').click()
    assert page.locator('.cell[aria-pressed="true"]').count() == 0
    assert not errors, errors
    browser.close()

print('Fresh-install API and frontend smoke check passed on ports 8001/5175.')
