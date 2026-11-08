"""M2 HTTP contract checks against the prepared July–September dashboard data."""
from pathlib import Path
import json
import shutil

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.data_service import COUNT_FIELDS, with_rates
from backend.app.main import create_app


DATA_DIR = Path(__file__).resolve().parents[2] / 'data/processed/2025-q3/dashboard'


def test_real_metadata_airports_and_context_reconcile():
    with TestClient(create_app(DATA_DIR)) as client:
        health = client.get('/api/health').json()
        metadata = client.get('/api/metadata').json()
        airports = client.get('/api/airports').json()
        context = client.get('/api/context').json()

    assert health == {'status': 'ready', 'version': metadata['version']}
    assert metadata['period'] == '2025-07-01/2025-09-30'
    assert metadata['origins'] == len(airports) == 340
    assert metadata['totals']['scheduled_count'] == 1_785_449
    assert metadata['totals']['arrival_eligible_count'] == 1_754_276
    assert metadata['totals']['late_count'] == 401_327
    assert metadata['exclusions']['invalid_time_rows'] == 1
    assert metadata['exclusions']['unexplained_arrival_rows'] == 1
    assert metadata['exclusions']['outside_origin_geography'] == 10_794
    assert sum(row['scheduled_count'] for row in airports) == 1_785_449
    assert sum(row['scheduled_count'] for row in context['rows']) == 1_785_449
    assert context['totals'] == metadata['totals']
    assert context['origin_id'] is None
    assert all(row['latitude'] is not None and row['longitude'] is not None for row in airports)


def test_selected_and_empty_contexts_and_validation():
    with TestClient(create_app(DATA_DIR)) as client:
        airports = client.get('/api/airports').json()
        jfk = next(row for row in airports if row['origin_code'] == 'JFK')
        chosen = client.get('/api/context', params={'origin_id': jfk['origin_id']})
        empty = client.get('/api/context', params={'origin_id': 999999})
        bad_text = client.get('/api/context?origin_id=JFK')
        bad_number = client.get('/api/context?origin_id=-1')

    assert chosen.status_code == 200
    assert chosen.json()['origin_code'] == 'JFK'
    assert chosen.json()['totals']['scheduled_count'] == jfk['scheduled_count']
    assert sum(row['late_count'] for row in chosen.json()['rows']) == jfk['late_count']
    assert empty.status_code == 200
    assert empty.json()['rows'] == []
    assert empty.json()['totals']['late_rate'] is None
    assert empty.json()['totals']['cancellation_rate'] is None
    assert 'NaN' not in empty.text and 'Infinity' not in empty.text
    assert bad_text.status_code == bad_number.status_code == 422


def test_missing_prepared_files_stop_startup(tmp_path):
    with pytest.raises(FileNotFoundError, match='Missing dashboard data'):
        with TestClient(create_app(tmp_path)):
            pass


def test_mismatched_prepared_counts_stop_startup(tmp_path):
    for name in ['metadata.json', 'cube.parquet', 'airports.parquet']:
        shutil.copyfile(DATA_DIR / name, tmp_path / name)
    path = tmp_path / 'metadata.json'
    metadata = json.loads(path.read_text(encoding='utf-8'))
    metadata['totals']['late_count'] += 1
    path.write_text(json.dumps(metadata), encoding='utf-8')
    with pytest.raises(ValueError, match='late_count'):
        with TestClient(create_app(tmp_path)):
            pass


def test_rates_use_counts_and_unknown_cancellation_stays_null():
    row = {key: 0 for key in COUNT_FIELDS}
    row.update(scheduled_count=10, cancelled_count=1, cancellation_eligible_count=9,
               arrival_eligible_count=4, late_count=1)
    result = with_rates(row)
    assert result['late_rate'] == 0.25
    assert result['cancellation_rate'] is None


def test_scheduled_group_without_eligible_arrivals_serializes_null():
    cube = pd.read_parquet(DATA_DIR / 'cube.parquet')
    example = cube.loc[cube.scheduled_count.gt(0) & cube.arrival_eligible_count.eq(0)].iloc[0]
    with TestClient(create_app(DATA_DIR)) as client:
        rows = client.get('/api/context', params={'origin_id': int(example.origin_id)}).json()['rows']
    row = next(row for row in rows if row['carrier'] == example.carrier and
               row['weekday'] == example.weekday and row['hour'] == example.hour)
    assert row['scheduled_count'] > 0
    assert row['late_rate'] is None


def test_local_frontend_origin_is_allowed():
    with TestClient(create_app(DATA_DIR)) as client:
        response = client.options('/api/metadata', headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET',
        })
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'


def test_airport_hour_frames_match_context_counts():
    with TestClient(create_app(DATA_DIR)) as client:
        response = client.get('/api/airport-hours')
        all_context = client.get('/api/context').json()
        airports = client.get('/api/airports').json()
        lax = next(row for row in airports if row['origin_code'] == 'LAX')
        lax_context = client.get('/api/context', params={'origin_id': lax['origin_id']}).json()

    assert response.status_code == 200
    result = response.json()
    assert result['period'] == all_context['period']
    assert result['version'] == all_context['version']
    assert [frame['hour'] for frame in result['frames']] == list(range(24))
    for frame in result['frames']:
        hour = frame['hour']
        for key in COUNT_FIELDS:
            assert sum(row[key] for row in frame['rows']) == sum(
                row[key] for row in all_context['rows'] if row['hour'] == hour)
            assert sum(row[key] for row in frame['rows'] if row['origin_id'] == lax['origin_id']) == sum(
                row[key] for row in lax_context['rows'] if row['hour'] == hour)
    assert 'NaN' not in response.text and 'Infinity' not in response.text
