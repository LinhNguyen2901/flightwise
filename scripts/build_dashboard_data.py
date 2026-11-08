"""Build API-ready July–September aggregates using the reviewed notebook rules."""
import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.dataset_config import active_dataset, check_output_period
from scripts.download_data import ROOT, sha256
from scripts.prepare_data import (AIRPORT_FIELDS, COUNTS, FLIGHT_FIELDS, DIMS,
                                  departure_hour, join_airports, prepare_airports,
                                  prepare_flights, read_zip)


def main():
    active = active_dataset()
    year = active['year']
    months = active['months']
    default_output = ROOT / active['processed_dir'] / 'dashboard'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=default_output)
    args = parser.parse_args()
    check_output_period(args.output, year, months, 'metadata.json')

    raw_paths = [ROOT / f'data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{m}.zip'
                 for m in months]
    airport_path = ROOT / 'data/raw/airport_coordinates.zip'
    manifest = json.loads((ROOT / 'data/manifest.json').read_text(encoding='utf-8'))
    for path in [airport_path, *raw_paths]:
        actual_hash = sha256(path)
        expected_hash = manifest['files'][path.relative_to(ROOT).as_posix()]['sha256']
        if actual_hash != expected_hash:
            raise ValueError(f'Source hash differs from manifest: {path.name}')

    raw_airports, _ = read_zip(airport_path, AIRPORT_FIELDS)
    airports = prepare_airports(raw_airports)
    bad_airports = int((~airports.valid_coordinates).sum())
    airports = airports.loc[airports.valid_coordinates].copy()
    count_columns = [*COUNTS, 'diverted_count']
    monthly_groups = []
    monthly_airports = []
    airport_names = []
    monthly_audit = []

    for month, path in zip(months, raw_paths):
        raw, _ = read_zip(path, FLIGHT_FIELDS)
        bad_time = departure_hour(raw.CRSDepTime).isna()
        missing_arrival = (pd.to_numeric(raw.ArrDelay, errors='coerce').isna() &
                           pd.to_numeric(raw.ArrDel15, errors='coerce').isna())
        unexplained = (missing_arrival & pd.to_numeric(raw.Cancelled).eq(0) &
                       pd.to_numeric(raw.Diverted).eq(0))
        removed_missing_arrival = unexplained & ~bad_time
        cleaned = raw.loc[~(bad_time | unexplained)].copy()

        flights, _ = prepare_flights(cleaned, year, month)
        flights['diverted_count'] = pd.to_numeric(cleaned.Diverted).eq(1).astype('int64')
        joined, join_audit = join_airports(flights, airports)
        outside_scope = joined.AIRPORT_STATE_CODE.isin(['PR', 'VI', 'TT'])
        dashboard = joined.loc[~outside_scope].copy()
        if dashboard.AIRPORT_STATE_CODE.isna().any() or dashboard.unmapped_count.any():
            raise ValueError(f'Missing airport mapping in dashboard scope: {month}')
        if dashboard.hour.isna().any():
            raise ValueError(f'Invalid hour remained after cleaning: {month}')

        grouped = dashboard.groupby(DIMS, as_index=False)[count_columns].sum()
        by_airport = dashboard.groupby('origin_id', as_index=False)[count_columns].sum()
        names = dashboard[['origin_id', 'origin_seq_id', 'origin_code',
                           'DISPLAY_AIRPORT_NAME', 'LATITUDE', 'LONGITUDE',
                           'AIRPORT_STATE_CODE']].drop_duplicates()
        monthly_groups.append(grouped)
        monthly_airports.append(by_airport)
        airport_names.append(names)
        monthly_audit.append({
            'month': month, 'raw_rows': len(raw),
            'removed_invalid_time': int(bad_time.sum()),
            'removed_unexplained_arrival': int(removed_missing_arrival.sum()),
            'cleaned_rows': len(cleaned),
            'outside_origin_geography': int(outside_scope.sum()),
            'dashboard_rows': len(dashboard),
            'unmapped_rows': join_audit['unmapped_rows'],
        })
        print(f'{year}-{month:02d}: {len(raw):,} raw -> {len(dashboard):,} dashboard rows')
        del raw, cleaned, flights, joined, dashboard

    cube = pd.concat(monthly_groups).groupby(DIMS, as_index=False)[count_columns].sum()
    origins = pd.concat(monthly_airports).groupby('origin_id', as_index=False)[count_columns].sum()
    names = pd.concat(airport_names).drop_duplicates()
    if names.origin_id.duplicated().any():
        raise ValueError('One origin has multiple coordinate records')
    airports_out = origins.merge(names, on='origin_id', validate='one_to_one')
    cube = cube.sort_values(DIMS).reset_index(drop=True)
    airports_out = airports_out.sort_values('origin_id').reset_index(drop=True)
    origins = origins.sort_values('origin_id').reset_index(drop=True)
    totals = {key: int(origins[key].sum()) for key in count_columns}
    if totals['scheduled_count'] != sum(row['dashboard_rows'] for row in monthly_audit):
        raise ValueError('Dashboard totals did not reconcile')

    args.output.mkdir(parents=True, exist_ok=True)
    cube.to_parquet(args.output / 'cube.parquet', index=False)
    airports_out.to_parquet(args.output / 'airports.parquet', index=False)
    origins.to_parquet(args.output / 'origin_counts.parquet', index=False)
    metadata = {
        'year': year, 'months': months, 'period': active['period'],
        'version': '2025-q3-dashboard-v1',
        'origin_scope': 'Contiguous U.S., Alaska and Hawaii origin airports',
        'metric_rule': 'Arrival late is >=15 minutes among completed non-diverted flights with known status',
        'source_hashes': {path.name: sha256(path) for path in [airport_path, *raw_paths]},
        'airport_reference_rows_removed': bad_airports,
        'monthly': monthly_audit, 'totals': totals,
        'origins': len(airports_out), 'cube_rows': len(cube),
    }
    (args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f"Saved {len(cube):,} groups for {len(airports_out)} origins to {args.output}")


if __name__ == '__main__':
    main()
