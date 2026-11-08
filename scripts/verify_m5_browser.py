"""M5 presentation and edge-state audit against the running local app."""
import asyncio
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:5173/'


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True,
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        await page.goto(BASE, wait_until='networkidle')
        await page.get_by_role('heading', name='Explore Flight Reliability: Late arrivals').wait_for()
        assert await page.locator('svg[role="group"]').count() == 4
        assert await page.locator('.airport').count() == 340
        assert await page.locator('.cell').count() == 168
        assert await page.locator('.carrier-row').count() == 14
        assert await page.locator('.hour-bar').count() == 24
        assert await page.locator('body').evaluate('(el) => el.scrollWidth <= innerWidth')
        assert '50%+' in await page.locator('svg[aria-label="Airport map"]').text_content()
        assert '50%+' in await page.locator('svg[aria-label="Departure hour and weekday heatmap"]').text_content()
        assert 'Late-arrival rate (% of eligible flights)' in await page.locator('svg[aria-label="Airline comparison"]').text_content()
        await page.screenshot(path=str(ROOT / 'docs/figures/m5_desktop.png'), full_page=True)

        # Edge tooltips stay within the viewport, including keyboard focus.
        for selector in ('.airport[data-origin="JFK"]', '.cell[data-cell="7:23"]'):
            await page.locator(selector).focus()
            tooltip = page.locator('.fw-tooltip:not([hidden])')
            await tooltip.wait_for()
            box = await tooltip.bounding_box()
            assert box['x'] >= 0 and box['y'] >= 0
            assert box['x'] + box['width'] <= 1920 and box['y'] + box['height'] <= 1080
            assert 'Scheduled:' in await tooltip.inner_text()
        await page.locator('h1').click()

        # Largest tested airport context and a cached repeat interaction.
        await page.locator('.airport[data-origin="LAX"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('LAX')")
        assert 'LAX' in await page.locator('svg[aria-label="Scheduled flights and arrival-late rate by local hour"] desc').text_content()
        await page.get_by_role('button', name='Clear airport').click()
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('All origins')")
        start = time.perf_counter()
        await page.locator('.airport[data-origin="LAX"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('LAX')")
        cached_ui_ms = round((time.perf_counter() - start) * 1000, 1)

        # Select everything with the D3 brush; summary stays compact.
        await page.get_by_role('button', name='Brush time cells').click()
        first = await page.locator('.cell[data-cell="1:0"]').bounding_box()
        last = await page.locator('.cell[data-cell="7:23"]').bounding_box()
        await page.mouse.move(first['x'] + 1, first['y'] + 1)
        await page.mouse.down()
        await page.mouse.move(last['x'] + last['width'] - 1, last['y'] + last['height'] - 1, steps=12)
        await page.mouse.up()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 168
        assert 'All 168 weekday/hour cells selected' in await page.locator('.selection-summary').inner_text()
        await page.get_by_role('button', name='Reset all').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0

        await page.set_viewport_size({'width': 420, 'height': 800})
        await page.screenshot(path=str(ROOT / 'docs/figures/m5_narrow.png'), full_page=True)
        assert await page.locator('body').evaluate('(el) => el.scrollWidth <= innerWidth')
        assert await page.locator('.chart-card').first.evaluate('(el) => el.scrollWidth > el.clientWidth')
        assert not errors, errors
        await browser.close()
    print(json.dumps({'status': 'passed', 'cached_ui_repeat_ms': cached_ui_ms,
                      'desktop_viewport': '1920x1080', 'narrow_viewport': '420x800',
                      'console_errors': len(errors)}))


if __name__ == '__main__':
    asyncio.run(main())
