import {sumCounts} from './charts/metrics.js';
import type {Airport, AirportHourRow, ContextRow} from './types';

export function mapAirports(airports: Airport[]) {
  return airports.map(airport => ({
    ...airport,
    LATITUDE: airport.latitude,
    LONGITUDE: airport.longitude,
  }));
}

export function hourlyCounts(rows: ContextRow[]) {
  return Array.from({length: 24}, (_, hour) => ({
    hour,
    ...sumCounts(rows.filter(row => row.hour === hour)),
  }));
}

export function frameAirports(airports: Airport[], rows: AirportHourRow[]): Airport[] {
  const byId = new Map(rows.map(row => [row.origin_id, row]));
  return airports.map(airport => {
    const row = byId.get(airport.origin_id);
    if (!row) return {...airport, scheduled_count: 0, cancelled_count: 0, diverted_count: 0,
      cancellation_eligible_count: 0, arrival_eligible_count: 0, late_count: 0,
      excluded_arrival_count: 0, invalid_time_count: 0, unmapped_count: 0,
      late_rate: null, cancellation_rate: null};
    return {...airport, ...row,
      late_rate: row.arrival_eligible_count ? row.late_count / row.arrival_eligible_count : null,
      cancellation_rate: row.scheduled_count && row.cancellation_eligible_count === row.scheduled_count
        ? row.cancelled_count / row.scheduled_count : null};
  });
}
