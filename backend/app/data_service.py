import json
from pathlib import Path

import pandas as pd


COUNT_FIELDS = ['scheduled_count', 'cancelled_count', 'diverted_count', 'cancellation_eligible_count', 'arrival_eligible_count', 'late_count', 'excluded_arrival_count', 'invalid_time_count', 'unmapped_count']

CARRIER_NAMES = {
    'AA': 'American Airlines', 'AS': 'Alaska Airlines', 'B6': 'JetBlue Airways',
    'DL': 'Delta Air Lines', 'F9': 'Frontier Airlines', 'G4': 'Allegiant Air',
    'HA': 'Hawaiian Airlines', 'MQ': 'Envoy Air', 'NK': 'Spirit Airlines',
    'OH': 'PSA Airlines', 'OO': 'SkyWest Airlines', 'UA': 'United Airlines',
    'WN': 'Southwest Airlines', 'YX': 'Republic Airways',
}


def with_rates(row):
    result = {key: int(row[key]) for key in COUNT_FIELDS}
    eligible = result['arrival_eligible_count']
    scheduled = result['scheduled_count']
    result['late_rate'] = result['late_count'] / eligible if eligible else None
    if scheduled and result['cancellation_eligible_count'] == scheduled:
        result['cancellation_rate'] = result['cancelled_count'] / scheduled
    else:
        result['cancellation_rate'] = None
    return result


def totals(frame):
    if frame.empty:
        return with_rates({key: 0 for key in COUNT_FIELDS})
    return with_rates(frame[COUNT_FIELDS].sum())


def load_data(directory: Path):
    required = ['metadata.json', 'cube.parquet', 'airports.parquet']
    missing = [name for name in required if not (directory / name).is_file()]
    if missing:
        raise FileNotFoundError(f'Missing dashboard data in {directory}: {missing}. Run build_dashboard_data.py')
    metadata = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    cube = pd.read_parquet(directory / 'cube.parquet')
    airports = pd.read_parquet(directory / 'airports.parquet')
    if cube[COUNT_FIELDS].isna().any().any() or airports[COUNT_FIELDS].isna().any().any():
        raise ValueError('Prepared count fields contain null values')
    airport_totals = totals(airports)
    cube_totals = totals(cube)
    for key in COUNT_FIELDS:
        if airport_totals[key] != metadata['totals'][key] or cube_totals[key] != metadata['totals'][key]:
            raise ValueError(f'Prepared {key} disagrees with metadata')
    all_context = cube.groupby(['carrier', 'weekday', 'hour'], as_index=False)[COUNT_FIELDS].sum()
    airport_hours = cube.groupby(['origin_id', 'hour'], as_index=False)[COUNT_FIELDS].sum()
    hour_frames = [[] for _ in range(24)]
    for record in airport_hours.to_dict('records'):
        hour_frames[int(record['hour'])].append({'origin_id': int(record['origin_id']), **{key: int(record[key]) for key in COUNT_FIELDS},})
    return {'metadata': metadata, 'cube': cube, 'airports': airports, 'all_context': all_context, 'hour_frames': hour_frames}


def airport_rows(data):
    rows = []
    for record in data['airports'].to_dict('records'):
        rows.append({**with_rates(record), 'origin_id': int(record['origin_id']), 'origin_code': record['origin_code'],
                     'name': record['DISPLAY_AIRPORT_NAME'], 'region': record['AIRPORT_STATE_CODE'],
                     'latitude': float(record['LATITUDE']), 'longitude': float(record['LONGITUDE'])})
    return rows


def context(data, origin_id=None):
    metadata = data['metadata']
    if origin_id is None:
        frame = data['all_context']
        origin_code = None
    else:
        frame = data['cube'].loc[data['cube'].origin_id.eq(origin_id)]
        airport = data['airports'].loc[data['airports'].origin_id.eq(origin_id)]
        origin_code = airport.origin_code.iloc[0] if len(airport) else None
    rows = []
    for record in frame.to_dict('records'):
        rows.append({**with_rates(record), 'carrier': record['carrier'],
                     'weekday': int(record['weekday']), 'hour': int(record['hour'])})
    return {'period': metadata['period'], 'version': metadata['version'], 'origin_id': origin_id, 'origin_code': origin_code, 'totals': totals(frame), 'rows': rows}


def airport_hour_frames(data):
    metadata = data['metadata']
    return {'period': metadata['period'], 'version': metadata['version'],
            'frames': [{'hour': hour, 'rows': rows} for hour, rows in enumerate(data['hour_frames'])]}


def metadata_response(data):
    source = data['metadata']
    exclusions = {
        'invalid_time_rows': sum(row['removed_invalid_time'] for row in source['monthly']),
        'unexplained_arrival_rows': sum(row['removed_unexplained_arrival'] for row in source['monthly']),
        'outside_origin_geography': sum(row['outside_origin_geography'] for row in source['monthly']),
        'airport_reference_rows_removed': source['airport_reference_rows_removed'],
    }
    return {'period': source['period'], 'version': source['version'],
            'origin_scope': source['origin_scope'], 'metric_rule': source['metric_rule'],
            'origins': source['origins'], 'cube_rows': source['cube_rows'],
            'totals': with_rates(source['totals']), 'exclusions': exclusions,
            'carrier_names': CARRIER_NAMES, 'source_hashes': source['source_hashes']}
