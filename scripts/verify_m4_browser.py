"""Exercise M4's two links against the local API in Chrome."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:5173/'
API = 'http://127.0.0.1:8000'


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True,
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
        page = await browser.new_page(viewport={'width': 1280, 'height': 900})
        errors = []
        context_requests = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: context_requests.append(request.url)
                if '/api/context?origin_id=' in request.url else None)
        await page.goto(BASE, wait_until='networkidle')
        await page.locator('.airport').first.wait_for()
        assert await page.locator('.airport').count() == 340
        assert await page.locator('.cell').count() == 168
        assert await page.locator('.carrier-row').count() == 14
        assert await page.get_by_role('button', name='Clear time').is_disabled()

        # Pair B alone: exact disjoint tuples; heatmap stays a full overview.
        for cell in ('1:8', '5:17'):
            await page.locator(f'.cell[data-cell="{cell}"]').focus()
            await page.keyboard.press('Space')
        assert await page.locator('.cell[aria-pressed="true"]').count() == 2
        assert await page.locator('.cell').count() == 168
        assert '2 selected time cells' in await page.locator('.selection-summary').inner_text()
        assert await page.get_by_role('button', name='Clear time').is_enabled()
        all_context = await (await page.request.get(API + '/api/context')).json()
        expected = sum(row['arrival_eligible_count'] for row in all_context['rows']
                       if (row['weekday'], row['hour']) in {(1, 8), (5, 17)})
        assert f'{expected:,} eligible flights' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        await page.get_by_role('button', name='Clear time').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0
        assert await page.get_by_role('button', name='Clear time').is_disabled()

        # Pair A alone: selected map airport changes the heatmap.
        atl = page.locator('.airport[data-origin="ATL"]')
        await atl.focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('ATL')")
        assert await page.locator('.airport[aria-pressed="true"]').count() == 1
        assert await page.locator('.airport').count() == 340
        airports = await (await page.request.get(API + '/api/airports')).json()
        atl_id = next(row['origin_id'] for row in airports if row['origin_code'] == 'ATL')
        atl_context = await (await page.request.get(f'{API}/api/context?origin_id={atl_id}')).json()
        assert f"{atl_context['totals']['arrival_eligible_count']:,} eligible arrivals" in await page.locator('svg[aria-label="Departure hour and weekday heatmap"] desc').text_content()

        # A and B together: same exact tuples, now within ATL.
        for cell in ('1:8', '5:17'):
            await page.locator(f'.cell[data-cell="{cell}"]').click()
        expected = sum(row['arrival_eligible_count'] for row in atl_context['rows']
                       if (row['weekday'], row['hour']) in {(1, 8), (5, 17)})
        assert f'{expected:,} eligible flights' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        await page.locator('h1').click()
        await page.screenshot(path=str(ROOT / 'docs/figures/m4_linked.png'), full_page=True)
        await page.get_by_role('button', name='Clear airport').click()
        assert await page.locator('.airport[aria-pressed="true"]').count() == 0
        assert await page.locator('.cell[aria-pressed="true"]').count() == 2
        await page.get_by_role('button', name='Reset all').click()
        assert 'All origins' in await page.locator('.selection-summary').inner_text()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0

        # Rectangular brushing replaces the set and issues no context request.
        before = len(context_requests)
        await page.get_by_role('button', name='Brush time cells').click()
        first = await page.locator('.cell[data-cell="1:8"]').bounding_box()
        last = await page.locator('.cell[data-cell="2:9"]').bounding_box()
        await page.mouse.move(first['x'] + 2, first['y'] + 2)
        await page.mouse.down()
        await page.mouse.move(last['x'] + last['width'] - 2, last['y'] + last['height'] - 2, steps=8)
        await page.mouse.up()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 4
        assert len(context_requests) == before
        await page.get_by_role('button', name='Clear time').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0
        assert 'All valid times' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()

        # Rapid airport changes: delayed first response cannot replace the second.
        sfo_id = next(row['origin_id'] for row in airports if row['origin_code'] == 'SFO')
        async def delay_sfo(route):
            await asyncio.sleep(0.5)
            await route.continue_()
        await page.route(f'{API}/api/context?origin_id={sfo_id}', delay_sfo)
        await page.locator('.airport[data-origin="SFO"]').focus()
        async with page.expect_request(f'{API}/api/context?origin_id={sfo_id}'):
            await page.keyboard.press('Enter')
        await page.locator('.airport[data-origin="LAX"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('LAX')")
        await asyncio.sleep(0.7)
        assert 'LAX' in await page.locator('svg[aria-label="Departure hour and weekday heatmap"] desc').text_content()
        await page.unroute(f'{API}/api/context?origin_id={sfo_id}')
        await page.get_by_role('button', name='Reset all').click()

        # A valid sparse airport/time combination produces an explicit empty chart message.
        sparse = next(row for row in airports if row['scheduled_count'] < 1000)
        await page.locator(f'.airport[data-origin="{sparse["origin_code"]}"]').focus()
        await page.keyboard.press('Enter')
        await page.locator('svg[aria-label="Departure hour and weekday heatmap"]').wait_for()
        sparse_context = await (await page.request.get(f'{API}/api/context?origin_id={sparse["origin_id"]}')).json()
        occupied = {(row['weekday'], row['hour']) for row in sparse_context['rows'] if row['scheduled_count']}
        empty = next((day, hour) for day in range(1, 8) for hour in range(24) if (day, hour) not in occupied)
        await page.locator(f'.cell[data-cell="{empty[0]}:{empty[1]}"]').click()
        assert 'No flights in this selection' in await page.locator('svg[aria-label="Airline comparison"]').text_content()
        await page.get_by_role('button', name='Reset all').click()

        # A failed selected-context request is visible and retryable.
        sea_id = next(row['origin_id'] for row in airports if row['origin_code'] == 'SEA')
        await page.route(f'{API}/api/context?origin_id={sea_id}', lambda route: route.abort())
        await page.locator('.airport[data-origin="SEA"]').focus()
        await page.keyboard.press('Enter')
        await page.get_by_role('alert').get_by_text('Could not load SEA context', exact=False).wait_for()
        assert await page.locator('svg[aria-label="Departure hour and weekday heatmap"]').count() == 0
        await page.unroute(f'{API}/api/context?origin_id={sea_id}')
        await page.get_by_role('button', name='Retry airport').click()
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('SEA')")
        assert not errors, errors
        await browser.close()
    print('M4 browser checks passed: A, B, combined exact tuples, keyboard, brush, clear/reset, stale response, empty state.')


if __name__ == '__main__':
    asyncio.run(main())

