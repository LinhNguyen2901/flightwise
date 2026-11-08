"""Check the guided layout at wide and narrow browser sizes."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',
        )
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:5173/', wait_until='networkidle')
        await page.locator('.cell').first.wait_for()

        assert await page.locator('.explore-steps a').all_text_contents() == [
            '1Airport ViewMap updates the heatmap',
            '2Departure Time ViewHeatmap filters airline bars',
            '3Airlines ViewFor this airport and time',
        ]
        assert await page.locator('.map-card .playback').count() == 1
        map_box = await page.locator('.map-card').bounding_box()
        heatmap_box = await page.locator('.heatmap-card').bounding_box()
        bars_box = await page.locator('.airline-card').bounding_box()
        assert map_box['x'] < heatmap_box['x'] == bars_box['x']
        assert map_box['y'] == heatmap_box['y'] < bars_box['y']
        assert map_box['width'] > 800 and heatmap_box['width'] > 800
        hourly_box = await page.locator('.hourly-card').bounding_box()
        assert hourly_box['y'] > bars_box['y']
        assert hourly_box['width'] > map_box['width'] + heatmap_box['width']
        assert abs(map_box['height'] - 1080) <= 2
        assert hourly_box['y'] >= map_box['y'] + map_box['height']
        legends = []
        for card in ('.map-card', '.heatmap-card', '.airline-card'):
            legends.append(await page.locator(f'{card} .rate-legend rect').evaluate_all(
                '(marks) => marks.map(mark => mark.getAttribute("fill"))'))
        assert len(legends[0]) == 100 and legends[0] == legends[1] == legends[2]
        assert len(set(legends[0])) > 50
        assert await page.locator('.hourly-card .hour-bar').first.get_attribute('fill') == '#b5d8d5'
        assert await page.locator('.hourly-card .hour-rate').first.get_attribute('stroke') == '#007f87'
        assert await page.get_by_role('button', name='Clear time').is_disabled()
        await page.screenshot(path=str(ROOT / 'docs/figures/intuitive_desktop.png'), full_page=True)

        # A time selection changes bar widths through a 300 ms D3 transition.
        airport = page.locator('.airport[data-origin="ATL"]')
        await airport.hover()
        assert await airport.evaluate('(mark) => getComputedStyle(mark).stroke') == 'rgb(216, 27, 96)'
        cell = page.locator('.cell[data-cell="1:8"]')
        await cell.hover()
        assert await cell.evaluate('(mark) => getComputedStyle(mark).stroke') == 'rgb(216, 27, 96)'
        bar = page.locator('.carrier-row[data-carrier="AA"] .rate-bar')
        before = float(await bar.get_attribute('width'))
        await cell.click()
        assert await page.get_by_role('button', name='Clear time').is_enabled()
        assert await bar.evaluate('(mark) => Boolean(mark.__transition)')
        await page.wait_for_timeout(400)
        after = float(await bar.get_attribute('width'))
        assert abs(after - before) > 1

        await page.emulate_media(reduced_motion='reduce')
        await page.locator('.cell[data-cell="5:17"]').click()
        assert not await bar.evaluate('(mark) => Boolean(mark.__transition)')
        await page.get_by_role('button', name='Reset all').click()

        await page.set_viewport_size({'width': 420, 'height': 800})
        await page.wait_for_timeout(200)
        assert await page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        boxes = [await page.locator(selector).bounding_box() for selector in
                 ('.map-card', '.heatmap-card', '.airline-card', '.hourly-card')]
        assert [box['y'] for box in boxes] == sorted(box['y'] for box in boxes)
        await page.screenshot(path=str(ROOT / 'docs/figures/intuitive_narrow.png'), full_page=True)
        assert not errors, errors
        await browser.close()
    print('Layout checks passed: shared smooth colors, filter transition, reduced motion, wide/narrow layout.')


if __name__ == '__main__':
    asyncio.run(main())
