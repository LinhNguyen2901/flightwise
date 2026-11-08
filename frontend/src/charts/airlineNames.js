// DOT's 2025 reporting-airline list (Air Travel Consumer Report, June 2025).
// Codes remain the grouping keys; names are for readers.
export const AIRLINE_NAMES = {
  AA: 'American Airlines', AS: 'Alaska Airlines', B6: 'JetBlue Airways',
  DL: 'Delta Air Lines', F9: 'Frontier Airlines', G4: 'Allegiant Air',
  HA: 'Hawaiian Airlines', MQ: 'Envoy Air', NK: 'Spirit Airlines',
  OH: 'PSA Airlines', OO: 'SkyWest Airlines', UA: 'United Airlines',
  WN: 'Southwest Airlines', YX: 'Republic Airways',
};

export function airlineName(code) {
  return AIRLINE_NAMES[code] ?? code;
}
