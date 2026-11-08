"""Validate BTS records and produce deterministic count aggregates (no API/UI)."""
import argparse
import json
from pathlib import Path
import time
import zipfile

import pandas as pd
import psutil

try:
    from .download_data import ROOT, sha256
    from .dataset_config import active_dataset, check_output_period
except ImportError:
    from download_data import ROOT, sha256
    from dataset_config import active_dataset, check_output_period

FLIGHT_FIELDS = ['FlightDate', 'DayOfWeek', 'Reporting_Airline',
                 'Flight_Number_Reporting_Airline', 'OriginAirportID',
                 'OriginAirportSeqID', 'Origin', 'DestAirportID', 'Dest',
                 'CRSDepTime', 'ArrDelay', 'ArrDel15', 'Cancelled', 'Diverted']
AIRPORT_FIELDS = ['AIRPORT_SEQ_ID', 'AIRPORT_ID', 'AIRPORT', 'DISPLAY_AIRPORT_NAME',
                  'LATITUDE', 'LONGITUDE', 'AIRPORT_START_DATE', 'AIRPORT_THRU_DATE',
                  'AIRPORT_STATE_CODE', 'AIRPORT_COUNTRY_CODE_ISO']
COUNTS = ['scheduled_count', 'cancelled_count', 'cancellation_eligible_count',
          'arrival_eligible_count', 'late_count', 'excluded_arrival_count',
          'invalid_time_count', 'unmapped_count']
DIMS = ['origin_id', 'carrier', 'weekday', 'hour']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def read_zip(path, fields):
    with zipfile.ZipFile(path) as archive:
        members = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(members) != 1:
            raise ValueError(f'Expected exactly one CSV in {path}: {members}')
        with archive.open(members[0]) as stream:
            header = pd.read_csv(stream, nrows=0).columns.tolist()
        missing = set(fields) - set(header)
        if missing:
            raise ValueError(f'{path.name}: missing required fields {sorted(missing)}; actual {header}')
        with archive.open(members[0]) as stream:
            frame = pd.read_csv(stream, usecols=fields, dtype='string')
    return frame, header


def departure_hour(values):
    numbers = pd.to_numeric(values, errors='coerce')
    valid = numbers.notna() & numbers.eq(numbers.round()) & numbers.ge(0) & numbers.le(2359) & (numbers % 100).lt(60)
    # 2400 is deliberately quarantined until the source convention is confirmed.
    return (numbers // 100).where(valid).astype('Int64')


def prepare_flights(raw, year, month):
    missing = set(FLIGHT_FIELDS) - set(raw.columns)
    if missing:
        raise ValueError(f'Missing fields: {sorted(missing)}')
    dates = pd.to_datetime(raw.FlightDate, errors='coerce')
    if dates.isna().any() or not (dates.dt.year.eq(year) & dates.dt.month.eq(month)).all():
        raise ValueError('Invalid date or records outside the requested month')
    weekday = pd.to_numeric(raw.DayOfWeek, errors='coerce')
    if not weekday.eq(dates.dt.dayofweek + 1).all():
        raise ValueError('Reported weekday disagrees with FlightDate')
    for field in ['OriginAirportID', 'OriginAirportSeqID', 'DestAirportID']:
        n = pd.to_numeric(raw[field], errors='coerce')
        if n.isna().any() or not (n.gt(0) & n.eq(n.round())).all():
            raise ValueError(f'Invalid identifier: {field}')
    if raw[['Reporting_Airline', 'Origin', 'Dest', 'Flight_Number_Reporting_Airline']].isna().any().any():
        raise ValueError('Missing flight identity field')
    flags = {name: pd.to_numeric(raw[name], errors='coerce').where(
        pd.to_numeric(raw[name], errors='coerce').isin([0, 1]))
        for name in ['Cancelled', 'Diverted', 'ArrDel15']}
    delay = pd.to_numeric(raw.ArrDelay, errors='coerce')
    delay = delay.where(delay.abs().lt(float('inf')))
    classified = flags['ArrDel15'].copy()
    missing_flag = raw.ArrDel15.isna() | raw.ArrDel15.str.strip().eq('')
    fallback = missing_flag & delay.notna()
    classified.loc[fallback] = delay.loc[fallback].ge(15).astype(int)
    conflict = (flags['ArrDel15'].notna() & delay.notna()
                & flags['ArrDel15'].ne(delay.ge(15).astype('Int64'))).fillna(False)
    eligible = (flags['Cancelled'].eq(0) & flags['Diverted'].eq(0)
                & classified.notna() & ~conflict).fillna(False)
    hour = departure_hour(raw.CRSDepTime)
    result = pd.DataFrame({
        'flight_date': dates, 'origin_id': pd.to_numeric(raw.OriginAirportID).astype('int64'),
        'origin_seq_id': pd.to_numeric(raw.OriginAirportSeqID).astype('int64'),
        'origin_code': raw.Origin, 'carrier': raw.Reporting_Airline,
        'weekday': weekday.astype('int64'), 'hour': hour,
        'scheduled_count': 1,
        'cancelled_count': flags['Cancelled'].eq(1).fillna(False).astype('int64'),
        'cancellation_eligible_count': flags['Cancelled'].notna().astype('int64'),
        'arrival_eligible_count': eligible.astype('int64'),
        'late_count': (eligible & classified.eq(1)).fillna(False).astype('int64'),
        'excluded_arrival_count': (~eligible).astype('int64'),
        'invalid_time_count': hour.isna().astype('int64'),
    })
    identity = ['FlightDate', 'Reporting_Airline', 'Flight_Number_Reporting_Airline',
                'OriginAirportID', 'DestAirportID', 'CRSDepTime']
    audit = {
        'rows': len(raw), 'missing_by_field': {c: int(raw[c].isna().sum()) for c in raw},
        'selected_field_duplicate_rows': int(raw.duplicated().sum()),
        'identity_collision_rows': int(raw.duplicated(identity, keep=False).sum()),
        'delay_conflicts': int(conflict.fillna(False).sum()),
        'arrival_flag_derived_from_delay': int(fallback.sum()),
        'cancelled_and_diverted': int((flags['Cancelled'].eq(1) & flags['Diverted'].eq(1)).sum()),
        'invalid_time_rows': int(hour.isna().sum()),
        'time_2400_rows': int(pd.to_numeric(raw.CRSDepTime, errors='coerce').eq(2400).sum()),
        'unknown_or_invalid_flags': {k: int(v.isna().sum()) for k, v in flags.items()},
    }
    # Retain every source row. A selected-field duplicate is not proof of a duplicate flight.
    return result, audit


def prepare_airports(raw):
    frame = raw.rename(columns={'AIRPORT_THRU_DATE': 'AIRPORT_END_DATE'}).copy()
    for col in ['AIRPORT_SEQ_ID', 'AIRPORT_ID']:
        n = pd.to_numeric(frame[col], errors='coerce')
        if n.isna().any() or not (n.gt(0) & n.eq(n.round())).all():
            raise ValueError(f'Invalid airport key: {col}')
        frame[col] = n.astype('int64')
    duplicates = frame.AIRPORT_SEQ_ID.duplicated(keep=False)
    if duplicates.any():
        raise ValueError('Ambiguous airport sequence IDs; resolve source duplicates before joining')
    for col in ['LATITUDE', 'LONGITUDE']:
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    valid = frame.LATITUDE.between(-90, 90) & frame.LONGITUDE.between(-180, 180)
    valid &= ~(frame.LATITUDE.eq(0) & frame.LONGITUDE.eq(0))
    frame['valid_coordinates'] = valid.fillna(False)
    for col in ['AIRPORT_START_DATE', 'AIRPORT_END_DATE']:
        original = frame[col]
        frame[col] = pd.to_datetime(original, errors='coerce', format='mixed')
        if (original.notna() & frame[col].isna()).any():
            raise ValueError(f'Unparseable reference date: {col}')
    return frame


def join_airports(flights, airports):
    joined = flights.merge(airports, how='left', left_on='origin_seq_id',
                           right_on='AIRPORT_SEQ_ID', validate='many_to_one', indicator=True)
    if len(joined) != len(flights):
        raise AssertionError('Coordinate join changed row count')
    matched = joined['_merge'].eq('both')
    if (matched & joined.origin_id.ne(joined.AIRPORT_ID)).any():
        raise ValueError('Matched sequence ID has inconsistent stable airport ID')
    in_date = ((joined.AIRPORT_START_DATE.isna() | joined.flight_date.ge(joined.AIRPORT_START_DATE))
               & (joined.AIRPORT_END_DATE.isna() | joined.flight_date.le(joined.AIRPORT_END_DATE)))
    mapped = matched & joined.valid_coordinates.fillna(False).astype(bool) & in_date
    joined['unmapped_count'] = (~mapped).astype('int64')
    audit = {'unmatched_rows': int((~matched).sum()),
             'outside_reference_dates': int((matched & ~in_date).sum()),
             'invalid_coordinate_rows': int((matched & ~joined.valid_coordinates.fillna(False).astype(bool)).sum()),
             'unmapped_rows': int((~mapped).sum()), 'rows_before': len(flights), 'rows_after': len(joined)}
    return joined, audit


def aggregate(frame, dimensions):
    return frame.groupby(dimensions, dropna=False, observed=True)[COUNTS].sum().reset_index().sort_values(dimensions).reset_index(drop=True)


def rates(counts):
    n = int(counts['arrival_eligible_count'])
    scheduled = int(counts['scheduled_count'])
    return {'late_arrival_rate': int(counts['late_count']) / n if n else None,
            'cancellation_rate': int(counts['cancelled_count']) / scheduled
            if scheduled and int(counts['cancellation_eligible_count']) == scheduled else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    active = active_dataset()
    parser.add_argument('--year', type=int, default=active['year'])
    parser.add_argument('--months', type=int, nargs='+', default=active['months'])
    parser.add_argument('--output', type=Path, default=ROOT / active['processed_dir'])
    parser.add_argument('--sample-dir', type=Path, default=ROOT / active['sample_dir'])
    args = parser.parse_args()
    if any(m not in range(1, 13) for m in args.months):
        parser.error('months must be 1..12')
    started = time.perf_counter()
    check_output_period(args.output, args.year, args.months, 'quality_report.json')
    check_output_period(args.sample_dir, args.year, args.months, 'provenance.json')
    manifest = json.loads((ROOT / 'data/manifest.json').read_text())
    airport_path = ROOT / 'data/raw/airport_coordinates.zip'
    paths = [ROOT / f'data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{args.year}_{m}.zip'
             for m in sorted(set(args.months))]
    for path in [airport_path, *paths]:
        if sha256(path) != manifest['files'][path.relative_to(ROOT).as_posix()]['sha256']:
            raise ValueError(f'Input hash mismatch: {path}')
    raw_airports, airport_header = read_zip(airport_path, AIRPORT_FIELDS)
    airports = prepare_airports(raw_airports)
    audit = {'year': args.year, 'months': sorted(set(args.months)), 'monthly': {},
             'airport_schema': airport_header, 'airport_reference_rows': len(airports),
             'airport_reference_unique_ids': int(airports.AIRPORT_ID.nunique()),
             'airport_reference_invalid_coordinates': int((~airports.valid_coordinates).sum()),
             'input_hashes': {p.name: sha256(p) for p in [airport_path, *paths]}}
    args.output.mkdir(parents=True, exist_ok=True)
    sample_dir = args.sample_dir
    sample_dir.mkdir(parents=True, exist_ok=True)
    cubes, origins, dimensions = [], [], []
    for month, path in zip(sorted(set(args.months)), paths):
        month_start = time.perf_counter()
        raw, header = read_zip(path, FLIGHT_FIELDS)
        flights, quality = prepare_flights(raw, args.year, month)
        joined, join_quality = join_airports(flights, airports)
        cubes.append(aggregate(joined[joined.hour.notna()], DIMS))
        origins.append(aggregate(joined, ['origin_id']))
        dimension_cols = ['origin_id', 'origin_seq_id', 'origin_code', 'DISPLAY_AIRPORT_NAME',
                          'LATITUDE', 'LONGITUDE', 'AIRPORT_STATE_CODE', 'AIRPORT_COUNTRY_CODE_ISO', 'unmapped_count']
        dimensions.append(joined[dimension_cols].drop_duplicates())
        flights['unmapped_count'] = joined.unmapped_count.to_numpy()
        flights.to_parquet(args.output / f'flights_{args.year}_{month:02}.parquet', index=False)
        sample = raw.head(100)
        sample.to_csv(sample_dir / f'flights_{args.year}_{month:02}.csv', index=False, lineterminator='\n')
        quality.update({'join': join_quality, 'schema': header,
                        'totals': {k: int(joined[k].sum()) for k in COUNTS},
                        'processing_seconds': round(time.perf_counter() - month_start, 3)})
        audit['monthly'][str(month)] = quality
        print(f'{args.year}-{month:02}: {len(raw):,} rows, {quality["processing_seconds"]} s', flush=True)
        del joined, flights, raw
    cube = aggregate(pd.concat(cubes, ignore_index=True), DIMS)
    origin_counts = aggregate(pd.concat(origins, ignore_index=True), ['origin_id'])
    airport_dimension = pd.concat(dimensions).drop_duplicates().sort_values(['origin_id', 'origin_seq_id'])
    # Preserve sequence variants for later map design; do not arbitrarily choose one.
    cube.to_parquet(args.output / 'cube.parquet', index=False)
    origin_counts.to_parquet(args.output / 'origin_counts.parquet', index=False)
    airport_dimension.to_parquet(args.output / 'airports.parquet', index=False)
    used_sequences = airport_dimension.origin_seq_id
    raw_airports[pd.to_numeric(raw_airports.AIRPORT_SEQ_ID).isin(used_sequences)].to_csv(
        sample_dir / 'airport_coordinates.csv', index=False, lineterminator='\n')
    totals = {k: int(origin_counts[k].sum()) for k in COUNTS}
    audit.update({'totals': totals, 'rates': rates(totals), 'cube_rows': len(cube),
                  'origins': int(origin_counts.origin_id.nunique()),
                  'carriers': int(cube.carrier.nunique()),
                  'sparse_cube_groups_under_30': int(cube.arrival_eligible_count.lt(30).sum()),
                  'multi_sequence_origin_ids': int(airport_dimension.groupby('origin_id').origin_seq_id.nunique().gt(1).sum()),
                  'processing_seconds': round(time.perf_counter() - started, 3),
                  'peak_process_working_set_bytes': getattr(psutil.Process().memory_info(), 'peak_wset', None),
                  'outputs': {p.name: {'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in sorted(args.output.glob('*.parquet'))}})
    if int(cube.scheduled_count.sum()) + totals['invalid_time_count'] != totals['scheduled_count']:
        raise AssertionError('Time-view counts do not reconcile')
    write_json(args.output / 'quality_report.json', audit)
    write_json(sample_dir / 'provenance.json', {
        'selection': 'First 100 original CSV records per month, selected source columns; not representative',
        'airport_selection': 'All historical sequence records used by the processed flight scope',
        'input_hashes': audit['input_hashes'], 'year': args.year, 'months': audit['months'],
        'files': {p.name: sha256(p) for p in sorted(sample_dir.glob('*.csv'))},
    })
    print(json.dumps({k: audit[k] for k in ['totals', 'rates', 'origins', 'carriers', 'cube_rows', 'processing_seconds']}), flush=True)


if __name__ == '__main__':
    main()
