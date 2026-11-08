import test from 'node:test';
import assert from 'node:assert/strict';
import {initialSelection, selectionReducer} from '../../frontend/src/selection.ts';
import {airlineCounts, playbackAirlineCounts} from '../../frontend/src/charts/metrics.js';
import {frameAirports} from '../../frontend/src/chartData.ts';

test('airport and time selections are independent and reversible', () => {
  let state = selectionReducer(initialSelection, {type: 'cell', cell: [1, 8]});
  state = selectionReducer(state, {type: 'airport', originId: 42});
  assert.deepEqual(state, {originId: 42, cells: [[1, 8]], animationHour: null, isPlaying: false});
  state = selectionReducer(state, {type: 'airport', originId: 7});
  assert.deepEqual(state.cells, [[1, 8]]);
  state = selectionReducer(state, {type: 'clearAirport'});
  assert.equal(state.originId, null);
  state = selectionReducer(state, {type: 'cell', cell: [1, 8]});
  assert.deepEqual(state.cells, []);
  assert.deepEqual(selectionReducer(state, {type: 'reset'}), initialSelection);
});

test('exact disjoint tuples do not admit their cross-product', () => {
  const rows = [
    {carrier: 'AA', weekday: 1, hour: 8, scheduled_count: 1, arrival_eligible_count: 1, late_count: 1},
    {carrier: 'AA', weekday: 5, hour: 17, scheduled_count: 2, arrival_eligible_count: 2, late_count: 0},
    {carrier: 'AA', weekday: 1, hour: 17, scheduled_count: 100, arrival_eligible_count: 100, late_count: 0},
    {carrier: 'AA', weekday: 5, hour: 8, scheduled_count: 100, arrival_eligible_count: 100, late_count: 0},
  ];
  assert.equal(airlineCounts(rows, [[1, 8], [5, 17]])[0].scheduled_count, 3);
  assert.equal(airlineCounts(rows, [])[0].scheduled_count, 203);
  assert.equal(airlineCounts(rows, [[2, 12]]).length, 0);
});

test('replaceCells supports full and empty brush results', () => {
  const all = Array.from({length: 168}, (_, i) => [Math.floor(i / 24) + 1, i % 24]);
  const full = selectionReducer(initialSelection, {type: 'replaceCells', cells: all});
  assert.equal(full.cells.length, 168);
  assert.deepEqual(selectionReducer(full, {type: 'replaceCells', cells: []}), initialSelection);
});

test('playback suspends manual cells, pauses on airport change and restores on exit', () => {
  let state = selectionReducer(initialSelection, {type: 'cell', cell: [1, 8]});
  state = selectionReducer(state, {type: 'enterPlayback', autoPlay: true});
  assert.equal(state.animationHour, 0);
  assert.equal(state.isPlaying, true);
  assert.deepEqual(state.cells, [[1, 8]]);
  state = selectionReducer(state, {type: 'seek', hour: 22});
  assert.equal(state.isPlaying, false);
  state = selectionReducer(state, {type: 'play'});
  state = selectionReducer(state, {type: 'tick'});
  assert.equal(state.animationHour, 23);
  assert.equal(state.isPlaying, false);
  assert.deepEqual(selectionReducer(state, {type: 'tick'}), state);
  state = selectionReducer(state, {type: 'play'});
  assert.equal(state.animationHour, 0);
  assert.equal(state.isPlaying, true);
  state = selectionReducer(state, {type: 'airport', originId: 42});
  assert.equal(state.isPlaying, false);
  assert.equal(state.animationHour, 0);
  assert.deepEqual(state.cells, [[1, 8]]);
  state = selectionReducer(state, {type: 'exitPlayback'});
  assert.equal(state.animationHour, null);
  assert.deepEqual(state.cells, [[1, 8]]);
  assert.deepEqual(selectionReducer(state, {type: 'reset'}), initialSelection);
});

test('editing time during playback exits, while pause and seek cannot advance a stopped timer', () => {
  let state = selectionReducer(initialSelection, {type: 'play'});
  state = selectionReducer(state, {type: 'seek', hour: 7});
  assert.equal(state.isPlaying, false);
  assert.equal(selectionReducer(state, {type: 'tick'}).animationHour, 7);
  state = selectionReducer(state, {type: 'cell', cell: [5, 17]});
  assert.equal(state.animationHour, null);
  assert.deepEqual(state.cells, [[5, 17]]);
  state = selectionReducer(state, {type: 'enterPlayback', autoPlay: false});
  assert.equal(state.isPlaying, false);
  state = selectionReducer(state, {type: 'replaceCells', cells: [[2, 9]]});
  assert.equal(state.animationHour, null);
  assert.deepEqual(state.cells, [[2, 9]]);
});

test('hourly airline rows match seven exact weekday tuples and retain empty carrier rows', () => {
  const rows = [
    {carrier: 'AA', weekday: 1, hour: 8, scheduled_count: 3, arrival_eligible_count: 3, late_count: 1},
    {carrier: 'AA', weekday: 2, hour: 8, scheduled_count: 2, arrival_eligible_count: 2, late_count: 0},
    {carrier: 'AA', weekday: 1, hour: 9, scheduled_count: 50, arrival_eligible_count: 50, late_count: 0},
    {carrier: 'DL', weekday: 1, hour: 9, scheduled_count: 4, arrival_eligible_count: 4, late_count: 1},
  ];
  const actual = playbackAirlineCounts(rows, 8);
  assert.deepEqual(actual.map(row => row.carrier), ['AA', 'DL']);
  assert.equal(actual[0].scheduled_count, 5);
  assert.equal(actual[1].scheduled_count, 0);
  assert.equal(airlineCounts(rows, Array.from({length: 7}, (_, i) => [i + 1, 8]))[0].scheduled_count, 5);
});

test('map frames retain all airport IDs and zero missing-hour counts', () => {
  const airports = [
    {origin_id: 1, origin_code: 'AAA', scheduled_count: 10, arrival_eligible_count: 9, late_count: 2},
    {origin_id: 2, origin_code: 'BBB', scheduled_count: 4, arrival_eligible_count: 4, late_count: 1},
  ];
  const frame = frameAirports(airports, [{origin_id: 1, scheduled_count: 3,
    cancellation_eligible_count: 3, arrival_eligible_count: 2, late_count: 1}]);
  assert.deepEqual(frame.map(row => row.origin_code), ['AAA', 'BBB']);
  assert.equal(frame[0].late_rate, 0.5);
  assert.equal(frame[1].scheduled_count, 0);
  assert.equal(frame[1].late_rate, null);
});
