export const COUNT_FIELDS = [
  'scheduled_count', 'cancelled_count', 'diverted_count', 'cancellation_eligible_count',
  'arrival_eligible_count', 'late_count', 'excluded_arrival_count',
  'invalid_time_count', 'unmapped_count',
];
export const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
export const cellKey = (weekday, hour) => `${weekday}:${hour}`;
export const emptyCounts = () => Object.fromEntries(COUNT_FIELDS.map(key => [key, 0]));

export function sumCounts(rows) {
  const total = emptyCounts();
  for (const row of rows) for (const key of COUNT_FIELDS) total[key] += row[key] ?? 0;
  return total;
}

export function lateRate(row) {
  return row.arrival_eligible_count > 0 ? row.late_count / row.arrival_eligible_count : null;
}

export function cancellationRate(row) {
  return row.scheduled_count > 0 && row.cancellation_eligible_count === row.scheduled_count
    ? row.cancelled_count / row.scheduled_count : null;
}

export function sampleStatus(row) {
  if (!row.scheduled_count) return 'no_flights';
  if (!row.arrival_eligible_count) return 'no_eligible_arrivals';
  return row.arrival_eligible_count < 30 ? 'low_n' : 'n_ge_30';
}

export function heatmapCounts(context) {
  const cells = Array.from({length: 168}, (_, i) => ({
    weekday: Math.floor(i / 24) + 1, hour: i % 24, ...emptyCounts(),
  }));
  for (const row of context) {
    const cell = cells[(row.weekday - 1) * 24 + row.hour];
    for (const key of COUNT_FIELDS) cell[key] += row[key] ?? 0;
  }
  return cells;
}

export function airlineCounts(context, selectedCells = []) {
  const keys = new Set(selectedCells.map(([day, hour]) => cellKey(day, hour)));
  const carriers = new Map();
  for (const row of context) {
    // Exact tuples: Mon 08 + Fri 17 never includes Mon 17 or Fri 08.
    if (keys.size && !keys.has(cellKey(row.weekday, row.hour))) continue;
    if (!carriers.has(row.carrier)) carriers.set(row.carrier, {carrier: row.carrier, ...emptyCounts()});
    const total = carriers.get(row.carrier);
    for (const key of COUNT_FIELDS) total[key] += row[key] ?? 0;
  }
  return [...carriers.values()].sort((a, b) => a.carrier.localeCompare(b.carrier));
}

export function playbackAirlineCounts(context, hour) {
  const selected = airlineCounts(context, DAYS.map((_, i) => [i + 1, hour]));
  const byCarrier = new Map(selected.map(row => [row.carrier, row]));
  const codes = [...new Set(context.map(row => row.carrier))].sort();
  return codes.map(carrier => byCarrier.get(carrier) ?? {carrier, ...emptyCounts()});
}
