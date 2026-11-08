import type {Airport, AirportHourFrames, Context, Metadata} from './types';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function getJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {signal});
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export function loadDashboard(signal: AbortSignal) {
  return Promise.all([
    getJson<Metadata>('/api/metadata', signal),
    getJson<Airport[]>('/api/airports', signal),
    getJson<Context>('/api/context', signal),
  ]);
}

export function loadContext(originId: number, signal: AbortSignal) {
  return getJson<Context>(`/api/context?origin_id=${originId}`, signal);
}

export function loadAirportHours(signal: AbortSignal) {
  return getJson<AirportHourFrames>('/api/airport-hours', signal);
}
