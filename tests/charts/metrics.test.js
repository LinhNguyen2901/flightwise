import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {COUNT_FIELDS, airlineCounts, heatmapCounts, lateRate, cancellationRate, sampleStatus, emptyCounts} from '../../frontend/src/charts/metrics.js';

const inputs = JSON.parse(readFileSync(fileURLToPath(new URL('../../docs/feasibility/2025-q3/client_inputs.json', import.meta.url)), 'utf8'));

test('new chart reducers match all 42 independently saved feasibility scenarios', () => {
  for (const [origin, context] of Object.entries(inputs.contexts)) {
    for (const [selection, cells] of Object.entries(inputs.filters)) {
      const actual = airlineCounts(context, cells);
      const expected = inputs.expected_bars.filter(row => row.context === origin && row.selection === selection);
      assert.equal(actual.length, expected.length, `${origin}/${selection}`);
      for (const row of actual) {
        const saved = expected.find(d => d.carrier === row.carrier);
        for (const key of COUNT_FIELDS) assert.equal(row[key], saved[key] ?? 0, `${origin}/${selection}/${row.carrier}/${key}`);
      }
    }
  }
});

test('full heatmap padding preserves no-flight cells and a true zero rate', () => {
  const cells = heatmapCounts(inputs.contexts.ABE);
  assert.equal(cells.length, 168);
  const empty = cells.find(d => d.scheduled_count === 0);
  assert.equal(lateRate(empty), null);
  assert.equal(sampleStatus(empty), 'no_flights');
  const zero = cells.find(d => d.weekday === 5 && d.hour === 17);
  assert.equal(lateRate(zero), 0);
  assert.equal(zero.arrival_eligible_count, 2);
  assert.equal(sampleStatus(zero), 'low_n');
});

test('weighted rates and exact tuples never average percentages or form Cartesian products', () => {
  // Explicitly synthetic records: only testing chart-side aggregation.
  const rows = [[1, 8, 1, 1], [5, 17, 99, 0], [1, 17, 100, 100]].map(([weekday, hour, n, late]) => ({
    ...emptyCounts(), carrier: 'TEST', weekday, hour, scheduled_count: n,
    arrival_eligible_count: n, late_count: late, cancellation_eligible_count: n,
  }));
  const [result] = airlineCounts(rows, [[1, 8], [5, 17]]);
  assert.equal(lateRate(result), 0.01);
  assert.equal(result.scheduled_count, 100);
});

test('unknown cancellation coverage and scheduled-but-no-eligible remain null', () => {
  const row = {...emptyCounts(), scheduled_count: 10, cancellation_eligible_count: 9};
  assert.equal(cancellationRate(row), null);
  assert.equal(lateRate(row), null);
  assert.equal(sampleStatus(row), 'no_eligible_arrivals');
});
