"""Exercise historical-hour playback against the local API and Chrome."""
import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('FLIGHTWISE_TEST_BASE', 'http://127.0.0.1:5173/')
API = os.environ.get('FLIGHTWISE_TEST_API', 'http://127.0.0.1:8000')


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True,
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
        page = await browser.new_page(viewport={'width': 1280, 'height': 900})
        errors = []
        frame_requests = []
        context_requests = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: frame_requests.append(request.url)
                if '/api/airport-hours' in request.url else context_requests.append(request.url)
                if '/api/context?origin_id=' in request.url else None)
        await page.goto(BASE, wait_until='networkidle')
        await page.get_by_role('button', name='Start playback').wait_for()
        assert await page.get_by_role('button', name='Start playback').is_enabled()
        assert len(frame_requests) == 1
        all_context = await (await page.request.get(API + '/api/context')).json()
        frames = await (await page.request.get(API + '/api/airport-hours')).json()
        assert len(frames['frames']) == 24

        # Manual selection is suspended, then restored when playback exits.
        await page.locator('.cell[data-cell="1:8"]').focus()
        await page.keyboard.press('Enter')
        assert await page.locator('.cell[aria-pressed="true"]').count() == 1
        await page.get_by_role('button', name='Start playback').click()
        assert await page.get_by_role('button', name='Pause').count() == 1
        await page.wait_for_function("() => document.querySelector('#playback-hour')?.value === '1'", timeout=3000)
        await page.get_by_role('button', name='Pause').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0
        assert 'Suspended manual' in await page.locator('.selection-summary').inner_text()
        assert 'temporarily suspended' not in await page.locator('.playback').inner_text()
        exit_box = await page.get_by_role('button', name='Exit').bounding_box()
        play_box = await page.get_by_role('button', name='Play').bounding_box()
        hour_box = await page.get_by_label('Local departure hour:').bounding_box()
        assert abs(exit_box['y'] - play_box['y']) <= 2
        assert abs(play_box['y'] - hour_box['y']) <= 8
        assert await page.locator('.active-hour-column').count() == 1
        assert await page.locator('.airport').count() == 340
        assert '50%+' in await page.locator('svg[aria-label="Airport map"]').text_content()

        hour = 8
        await page.get_by_label('Local departure hour:').fill(str(hour))
        expected_map = sum(row['scheduled_count'] for row in frames['frames'][hour]['rows'])
        expected_bars = sum(row['arrival_eligible_count'] for row in all_context['rows'] if row['hour'] == hour)
        assert f'{expected_map:,} scheduled flights' in await page.locator('svg[aria-label="Airport map"] desc').text_content()
        assert f'{expected_bars:,} eligible flights' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        assert 'Local hour 08:00' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        assert len(frame_requests) == 1
        await page.locator('h1').click()
        await page.screenshot(path=str(ROOT / 'docs/figures/m6_hour08.png'), full_page=True)
        main_map = page.locator('g[data-region="main"] g[clip-path] > g').first
        await page.locator('g[data-region="main"] > rect').scroll_into_view_if_needed()
        panel = await page.locator('g[data-region="main"] > rect').bounding_box()
        await page.mouse.move(panel['x'] + panel['width'] / 2, panel['y'] + panel['height'] / 2)
        await page.mouse.wheel(0, -500)
        await page.wait_for_function("() => document.querySelector('g[data-region=main] g[clip-path] > g')?.getAttribute('transform') !== 'translate(0,0) scale(1)'")
        zoomed = await main_map.get_attribute('transform')
        assert zoomed != 'translate(0,0) scale(1)'
        await page.get_by_label('Local departure hour:').fill('9')
        assert await main_map.get_attribute('transform') == zoomed
        await page.get_by_role('button', name='Exit').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 1
        assert await page.locator('.active-hour-column').count() == 0

        # A seven-weekday manual selection is equivalent to the matching hour frame.
        await page.get_by_role('button', name='Clear time').click()
        for day in range(1, 8):
            await page.locator(f'.cell[data-cell="{day}:8"]').focus()
            await page.keyboard.press('Enter')
        manual_title = await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        assert f'{expected_bars:,} eligible flights' in manual_title
        await page.get_by_role('button', name='Start playback').click()
        await page.get_by_role('button', name='Pause').click()
        await page.get_by_label('Local departure hour:').fill('8')
        assert f'{expected_bars:,} eligible flights' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()

        # Play, pause, stop at 23 and replay from 00; no API request per tick.
        await page.get_by_role('button', name='Play', exact=True).click()
        await page.wait_for_function("() => document.querySelector('#playback-hour')?.value === '9'", timeout=3000)
        await page.get_by_role('button', name='Pause').click()
        await asyncio.sleep(1.2)
        assert await page.locator('#playback-hour').input_value() == '9'
        await page.get_by_label('Local departure hour:').fill('22')
        await page.get_by_role('button', name='Play', exact=True).click()
        await page.wait_for_function("() => document.querySelector('#playback-hour')?.value === '23'", timeout=3000)
        assert await page.get_by_role('button', name='Replay').count() == 1
        assert 'End of day. Replay starts at 00:00.' not in await page.locator('.playback').inner_text()
        await asyncio.sleep(1.2)
        assert await page.locator('#playback-hour').input_value() == '23'
        await page.get_by_role('button', name='Replay').click()
        assert await page.locator('#playback-hour').input_value() == '0'
        await page.get_by_role('button', name='Pause').click()
        assert len(frame_requests) == 1
        assert len(context_requests) == 0

        # Changing airports pauses but retains the hour; editing a cell exits playback.
        await page.get_by_role('button', name='Play', exact=True).click()
        await page.locator('.airport[data-origin="ATL"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('ATL')")
        assert await page.get_by_role('button', name='Play', exact=True).count() == 1
        kept_hour = await page.locator('#playback-hour').input_value()
        assert kept_hour.isdigit()
        await page.locator('.cell[data-cell="5:17"]').focus()
        await page.keyboard.press('Enter')
        assert await page.get_by_role('button', name='Start playback').count() == 1
        assert await page.locator('.cell[aria-pressed="true"]').count() == 8
        await page.get_by_role('button', name='Reset all').click()
        assert await page.locator('.cell[aria-pressed="true"]').count() == 0
        assert await page.locator('.airport[aria-pressed="true"]').count() == 0

        # Reset while a timer is active leaves no playback frame behind.
        await page.get_by_role('button', name='Start playback').click()
        assert await page.get_by_role('button', name='Pause').count() == 1
        await page.get_by_role('button', name='Reset all').click()
        await asyncio.sleep(1.2)
        assert await page.get_by_role('button', name='Start playback').count() == 1
        assert await page.locator('.active-hour-column').count() == 0

        # A sparse airport can have no flights in a chosen local hour.
        airports = await (await page.request.get(API + '/api/airports')).json()
        sparse = min(airports, key=lambda row: row['scheduled_count'])
        sparse_context = await (await page.request.get(
            f'{API}/api/context?origin_id={sparse["origin_id"]}')).json()
        occupied = {row['hour'] for row in sparse_context['rows'] if row['scheduled_count']}
        empty_hour = next(hour for hour in range(24) if hour not in occupied)
        await page.locator(f'.airport[data-origin="{sparse["origin_code"]}"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function(f"() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('{sparse['origin_code']}')")
        await page.get_by_role('button', name='Start playback').click()
        await page.get_by_role('button', name='Pause').click()
        await page.get_by_label('Local departure hour:').fill(str(empty_hour))
        assert 'No flights in this selection' in await page.locator('svg[aria-label="Airline comparison"]').text_content()
        assert await page.locator('.airport').count() == 340
        await page.get_by_role('button', name='Reset all').click()

        # Reduced motion still permits manual seeking but disables automatic play.
        await page.emulate_media(reduced_motion='reduce')
        await page.get_by_role('button', name='Explore hours manually').click()
        assert await page.get_by_role('button', name='Play', exact=True).is_disabled()
        await page.get_by_label('Local departure hour:').fill('12')
        assert await page.locator('#playback-hour').input_value() == '12'
        await page.get_by_role('button', name='Exit').click()
        assert not errors, errors

        # Core A and B links still work after leaving playback.
        await page.locator('.cell[data-cell="1:8"]').focus()
        await page.keyboard.press('Enter')
        assert await page.locator('.cell[aria-pressed="true"]').count() == 1
        await page.locator('.airport[data-origin="ATL"]').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("() => document.querySelector('svg[aria-label=\"Departure hour and weekday heatmap\"] desc')?.textContent.includes('ATL')")
        assert await page.locator('.cell[aria-pressed="true"]').count() == 1
        assert '1 selected time cell' in await page.locator('svg[aria-label="Airline comparison"] desc').text_content()
        await page.get_by_role('button', name='Reset all').click()

        # A failed optional frame request leaves core charts usable and can retry.
        await page.route(API + '/api/airport-hours', lambda route: route.abort())
        await page.reload(wait_until='networkidle')
        await page.get_by_role('button', name='Retry frames').wait_for()
        assert await page.locator('svg[role="group"]').count() == 4
        await page.unroute(API + '/api/airport-hours')
        await page.get_by_role('button', name='Retry frames').click()
        await page.wait_for_function("() => [...document.querySelectorAll('button')].some(button => button.textContent === 'Explore hours manually' && !button.disabled)")
        assert await page.get_by_role('button', name='Explore hours manually').is_enabled()
        await browser.close()
    print('M6 browser checks passed: one-click start, end-of-day stop/replay, playback lifecycle, airport/time conflicts, reduced motion, retry.')


if __name__ == '__main__':
    asyncio.run(main())
