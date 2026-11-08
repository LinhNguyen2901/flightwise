"""Check the three-view first screen and full-width hourly context below."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:5173/'


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',
        )
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(BASE, wait_until='networkidle')
        await page.locator('.cell').first.wait_for()
        assert await page.locator('.fw-chart svg title').count() == 0
        await page.locator('.cell[data-cell="1:8"]').hover()
        hover_detail = page.locator('.heatmap-card .fw-tooltip:not([hidden])')
        assert 'Diverted:' in await hover_detail.inner_text()
        assert 'scheduled (' in await hover_detail.inner_text()
        await page.locator('.heatmap-card h2').hover()

        cards = [await page.locator(name).bounding_box() for name in
                 ('.map-card', '.heatmap-card', '.airline-card', '.hourly-card')]
        assert cards[0]['x'] < cards[1]['x'] == cards[2]['x']
        assert cards[1]['y'] < cards[2]['y']
        assert abs(cards[0]['height'] - 1080) <= 2
        assert (await page.locator('.map-card [data-region="main"] > rect').bounding_box())['width'] >= 550
        assert (await page.locator('.heatmap-card .cell').first.bounding_box())['width'] >= 25
        assert cards[3]['y'] >= max(card['y'] + card['height'] for card in cards[:3])
        assert cards[3]['width'] > cards[0]['width'] + cards[1]['width']
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        mainland = await page.locator('.map-card [data-region="main"] > rect').bounding_box()
        alaska = await page.locator('.map-card [data-region="AK"] > rect').bounding_box()
        hawaii = await page.locator('.map-card [data-region="HI"] > rect').bounding_box()
        assert mainland['width'] > alaska['width'] + hawaii['width'] - 30
        assert alaska['y'] >= mainland['y'] + mainland['height']
        assert hawaii['y'] == alaska['y'] and hawaii['x'] > alaska['x']
        assert await page.locator('.heatmap-card .view-question').inner_text() == 'When are late-arrival rates highest?'
        assert await page.locator('.heatmap-card .chart-title').count() == 0
        assert await page.locator('.airline-card .chart-title').count() == 0
        assert await page.locator('.map-card .eyebrow').count() == 0
        for name in ('.map-card', '.heatmap-card', '.airline-card'):
            card = page.locator(name)
            assert await card.evaluate('(element) => element.scrollHeight <= element.clientHeight + 1')
            card_box = await card.bounding_box()
            legend_box = await card.locator('.rate-legend').bounding_box()
            assert legend_box['y'] + legend_box['height'] <= card_box['y'] + card_box['height']
        await page.locator('.map-card').scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / 'docs/figures/three_view_1920.png'))

        await page.locator('.airport[data-origin="ATL"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('ATL')")
        await page.locator('.cell[data-cell="1:8"]').focus()
        await page.keyboard.press('Enter')
        assert 'ATL' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        assert '1 selected time cell' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        await page.wait_for_timeout(350)
        selected_cards = [await page.locator(name).bounding_box() for name in
                          ('.map-card', '.heatmap-card', '.airline-card')]
        assert abs(selected_cards[0]['height'] - 1080) <= 2
        await page.locator('.map-card').scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / 'docs/figures/three_view_selected.png'))
        await page.get_by_role('button', name='Reset all').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0

        await page.get_by_role('button', name='Brush time cells').click()
        first = await page.locator('.cell[data-cell="1:0"]').bounding_box()
        last = await page.locator('.cell[data-cell="7:23"]').bounding_box()
        await page.mouse.move(first['x'] + 1, first['y'] + 1)
        await page.mouse.down()
        await page.mouse.move(last['x'] + last['width'] - 1,
                              last['y'] + last['height'] - 1, steps=12)
        await page.mouse.up()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 168
        await page.get_by_role('button', name='Reset all').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0

        await page.set_viewport_size({'width': 1366, 'height': 768})
        laptop_cards = [await page.locator(name).bounding_box() for name in
                        ('.map-card', '.heatmap-card', '.airline-card', '.hourly-card')]
        assert laptop_cards[0]['x'] < laptop_cards[1]['x'] == laptop_cards[2]['x']
        assert abs(laptop_cards[0]['height'] - 768) <= 2
        assert (await page.locator('.map-card [data-region="main"] > rect').bounding_box())['width'] >= 400
        assert (await page.locator('.heatmap-card .cell').first.bounding_box())['width'] >= 18
        for name in ('.map-card', '.heatmap-card', '.airline-card'):
            card = page.locator(name)
            assert await card.evaluate('(element) => element.scrollHeight <= element.clientHeight + 1')
            card_box = await card.bounding_box()
            legend_box = await card.locator('.rate-legend').bounding_box()
            assert legend_box['y'] + legend_box['height'] <= card_box['y'] + card_box['height']
        await page.locator('.map-card').scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / 'docs/figures/three_view_laptop.png'))
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.set_viewport_size({'width': 420, 'height': 800})
        await page.screenshot(path=str(ROOT / 'docs/figures/three_view_narrow.png'), full_page=True)
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        boxes = [await page.locator(name).bounding_box() for name in
                 ('.map-card', '.heatmap-card', '.airline-card', '.hourly-card')]
        assert [box['y'] for box in boxes] == sorted(box['y'] for box in boxes)
        assert not errors, errors
        await browser.close()
    print('Screen-height three-view section passed: larger chart widths, both links, full brush, reset and narrow layout.')


if __name__ == '__main__':
    asyncio.run(main())
