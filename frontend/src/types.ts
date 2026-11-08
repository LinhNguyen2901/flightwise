export type Counts = {
  scheduled_count: number;
  cancelled_count: number;
  diverted_count: number;
  cancellation_eligible_count: number;
  arrival_eligible_count: number;
  late_count: number;
  excluded_arrival_count: number;
  invalid_time_count: number;
  unmapped_count: number;
  late_rate: number | null;
  cancellation_rate: number | null;
};

export type Metadata = {
  period: string;
  version: string;
  origin_scope: string;
  metric_rule: string;
  origins: number;
  cube_rows: number;
  totals: Counts;
  exclusions: Record<string, number>;
  carrier_names: Record<string, string>;
};

export type Airport = Counts & {
  origin_id: number;
  origin_code: string;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
};

export type ContextRow = Counts & {
  carrier: string;
  weekday: number;
  hour: number;
};

export type Context = {
  period: string;
  version: string;
  origin_id: number | null;
  origin_code: string | null;
  totals: Counts;
  rows: ContextRow[];
};

export type AirportHourRow = Omit<Counts, 'late_rate' | 'cancellation_rate'> & {origin_id: number};
export type AirportHourFrames = {
  period: string;
  version: string;
  frames: {hour: number; rows: AirportHourRow[]}[];
};
