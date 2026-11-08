"""Check the notebook's visible cleaning choices on small, separate test data."""
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / 'notebooks/dashboard_preview.ipynb'


def notebook_cleaners():
    book = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    namespace = {'pd': pd, 'YEAR': 2025, 'display': lambda frame: None}
    for cell in book['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        if source.startswith(('def parse_month(', 'def show_month_issues(',
                              'def inspect_month(', 'def clean_month(')):
            exec(source, namespace)
    return namespace['inspect_month'], namespace['clean_month']


def sample():
    return pd.read_csv(ROOT / 'data/sample/2025-q3/flights_2025_07.csv', dtype='string').head(1)


def test_invalid_2400_is_removed_from_cleaned_rows():
    raw = sample().copy()
    raw['CRSDepTime'] = '2400'
    inspect, clean = notebook_cleaners()
    parsed, bad_time, unexplained, checks = inspect(raw, 7)
    assert checks['invalid_or_missing_times'] == 1
    assert checks['missing_arrival_unexplained'] == 0
    assert len(clean(raw, parsed, bad_time, unexplained)) == 0


def test_unexplained_arrival_is_removed_but_cancelled_flight_is_retained():
    raw = pd.concat([sample()] * 2, ignore_index=True)
    raw['ArrDelay'] = pd.NA
    raw['ArrDel15'] = pd.NA
    raw['Cancelled'] = pd.Series(['0', '1'], dtype='string')
    raw['Diverted'] = '0'
    inspect, clean = notebook_cleaners()
    parsed, bad_time, unexplained, checks = inspect(raw, 7)
    assert checks['missing_arrival_unexplained'] == 1
    assert checks['missing_arrival_cancelled'] == 1
    result = clean(raw, parsed, bad_time, unexplained)
    assert len(result) == 1
    assert result.cancelled.tolist() == [1]
    assert result.late_flag.isna().all()


def test_missing_flag_uses_minutes_and_15_minute_boundary():
    raw = pd.concat([sample()] * 2, ignore_index=True)
    raw['ArrDelay'] = pd.Series(['14', '15'], dtype='string')
    raw['ArrDel15'] = pd.NA
    raw['Cancelled'] = '0'
    raw['Diverted'] = '0'
    inspect, clean = notebook_cleaners()
    parsed, bad_time, unexplained, checks = inspect(raw, 7)
    assert checks['flags_derived_from_minutes'] == 2
    result = clean(raw, parsed, bad_time, unexplained)
    assert result.late_flag.tolist() == [0, 1]


def test_submitted_notebook_reads_raw_files_and_uses_current_tables():
    book = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    source = '\n'.join(''.join(cell['source']) for cell in book['cells'] if cell['cell_type'] == 'code')
    assert 'pd.read_csv(csv_file, usecols=FLIGHT_COLUMNS' in source
    assert 'pd.read_parquet' not in source
    assert 'SVG(filename=' not in source
    assert "show_d3('heatmap', heatmap_data" in source
    assert "show_d3('bars', airline_bars" in source
    assert 'matplotlib.pyplot' in source
