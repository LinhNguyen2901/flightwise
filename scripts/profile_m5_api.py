"""Measure current local context payloads and HTTP response times."""
import json
import statistics
import time
from pathlib import Path

import pandas as pd
import requests

from backend.app.config import DATA_DIR


ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000'
cube = pd.read_parquet(DATA_DIR / 'cube.parquet', columns=['origin_id'])
largest_id = int(cube.groupby('origin_id').size().idxmax())
largest_rows = int(cube.groupby('origin_id').size().max())
session = requests.Session()
airports = session.get(BASE + '/api/airports', timeout=10).json()
largest_code = next(row['origin_code'] for row in airports if row['origin_id'] == largest_id)


def measure(path):
    session.get(BASE + path, timeout=10).raise_for_status()  # Warm the local path.
    durations = []
    byte_size = 0
    for _ in range(20):
        start = time.perf_counter()
        response = session.get(BASE + path, timeout=10)
        durations.append((time.perf_counter() - start) * 1000)
        response.raise_for_status()
        byte_size = len(response.content)
    return {'bytes': byte_size, 'median_ms': round(statistics.median(durations), 1),
            'max_ms': round(max(durations), 1), 'samples': len(durations)}


result = {
    'scope': 'local HTTP request plus body read; 20 warmed samples per path',
    'largest_origin': {'code': largest_code, 'origin_id': largest_id, 'context_rows': largest_rows},
    'all_origins': measure('/api/context'),
    'largest_origin_context': measure(f'/api/context?origin_id={largest_id}'),
}
output = ROOT / 'docs/m5_api_profile.json'
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
