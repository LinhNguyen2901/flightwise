"""Local paths and browser origin used by the M2 API."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
active = json.loads((ROOT / 'data/active_dataset.json').read_text(encoding='utf-8'))
DATA_DIR = Path(os.environ.get('FLIGHTWISE_DATA_DIR',
                               ROOT / active['processed_dir'] / 'dashboard'))
FRONTEND_ORIGIN = os.environ.get('FLIGHTWISE_FRONTEND_ORIGIN', 'http://localhost:5173')
