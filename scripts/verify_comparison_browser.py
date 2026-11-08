"""Check the optional two-airport comparison against the live local dashboard."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]


async def select_airport(page, code):
    await page.locator(f'.airport[data-origin="{code}"]').focus()
    await page.keyboard.press('Enter')
    await page.wait_for_function(
        "code => document.querySelector('.selection-values')?.textContent.includes(code)", arg=code
    )


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True, executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'
        )
        page = await browser.new_page(viewport={'width': 1366, 'height': 768})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:5173/', wait_until='networkidle')
        await page.locator('.airport[data-origin="ATL"]').wait_for()
        await select_airport(page, 'ATL')
        await page.get_by_role('button', name='Pin airport to compare').click()
        assert 'ATL' in await page.locator('.comparison-prompt').inner_text()
        assert await page.locator('.comparison-ring[data-origin="ATL"][data-role="pinned"]').count() == 1
        await select_airport(page, 'LAX')
        assert await page.locator('.comparison-ring[data-origin="LAX"][data-role="current"]').count() == 1
        assert await page.locator('.comparison-ring').count() == 2
        await page.locator('.map-card').scroll_into_view_if_needed()
        await page.locator('.map-card .view-intro h2').hover()
        await page.screenshot(path=str(ROOT / 'docs/figures/airport_comparison_map.png'))
        ring = page.locator('.comparison-ring[data-origin="ATL"]')
        width_before = (await ring.bounding_box())['width']
        map_box = await page.locator('.map-card [data-region="main"] > rect').bounding_box()
        await page.mouse.move(map_box['x'] + map_box['width'] / 2,
                              map_box['y'] + map_box['height'] / 2)
        await page.mouse.wheel(0, -400)
        await page.wait_for_timeout(350)
        assert abs((await ring.bounding_box())['width'] - width_before) < 2
        comparison = page.locator('svg[aria-label="Two airport late-arrival profiles by local departure hour"]')
        await comparison.wait_for()
        assert 'ATL' in await comparison.text_content()
        assert 'LAX' in await comparison.text_content()
        assert await comparison.locator('.hour-bar').count() == 48
        assert await comparison.locator('.hour-rate').count() > 30
        assert await comparison.locator('.share-axis').count() == 2
        assert await comparison.locator('.rate-axis').count() == 2
        await comparison.locator('.hour-bar').nth(5).hover()
        assert 'of ATL total' in await page.locator('.hourly-card .fw-tooltip:not([hidden])').inner_text()
        await page.locator('.hourly-card h2').hover()
        before = await comparison.text_content()
        await page.locator('.cell[data-cell="1:8"]').focus()
        await page.keyboard.press('Enter')
        assert await comparison.text_content() == before
        assert 'LAX' in await page.locator('.heatmap-card svg desc').text_content()
        await page.get_by_role('button', name='Start playback').click()
        assert await comparison.text_content() == before
        await page.get_by_role('button', name='Exit', exact=True).click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 1
        await page.locator('.hourly-card').scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / 'docs/figures/airport_comparison.png'))
        await page.get_by_role('button', name='Clear comparison').click()
        assert await page.locator('.comparison-ring').count() == 0
        await page.locator('svg[aria-label="Scheduled flights and arrival-late rate by local hour"]').wait_for()
        await page.get_by_role('button', name='Pin airport to compare').click()
        await page.get_by_role('button', name='Reset all').click()
        assert await page.locator('.comparison-prompt').count() == 0
        summary = await page.locator('.selection-values').inner_text()
        assert 'All origins' in summary and 'All valid times' in summary and 'Comparison pin' not in summary
        await page.set_viewport_size({'width': 420, 'height': 800})
        await select_airport(page, 'ATL')
        await page.get_by_role('button', name='Pin airport to compare').click()
        await select_airport(page, 'LAX')
        await comparison.wait_for()
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert await page.locator('.hourly-card').evaluate('(card) => card.scrollWidth > card.clientWidth')
        await page.locator('.hourly-card').scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / 'docs/figures/airport_comparison_narrow.png'))
        assert not errors, errors
        await browser.close()
    print('PASS: pin, compare, time/playback independence, clear, reset, and no browser errors')


if __name__ == '__main__':
    asyncio.run(main())
