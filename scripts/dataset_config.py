import calendar
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def active_dataset():
    path = ROOT / 'data/active_dataset.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    raise FileNotFoundError('Missing data/active_dataset.json; restore the active dataset configuration')


def period_label(quality):
    months = sorted(quality['months'])
    year = quality['year']
    return f'{year}-{months[0]:02}-01/{year}-{months[-1]:02}-{calendar.monthrange(year, months[-1])[1]}'


def check_output_period(directory, year, months, filename):
    path = directory / filename
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        if previous['year'] != year or previous['months'] != sorted(set(months)):
            raise ValueError(f'{directory} contains another period; choose a separate directory')
