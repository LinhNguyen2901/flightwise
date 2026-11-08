"""Independent streaming CSV reconciliation; does not use preparation metric functions."""
import argparse
import csv
from io import TextIOWrapper
import json
from pathlib import Path
import zipfile

import pandas as pd
try:
    from .dataset_config import active_dataset
except ImportError:
    from dataset_config import active_dataset

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / active_dataset()['processed_dir'])
    args = parser.parse_args()
    quality = json.loads((args.output / 'quality_report.json').read_text())
    cube = pd.read_parquet(args.output / 'cube.parquet')
    # Fixed contexts chosen before checking the results; include a sparse airport/time.
    contexts = [(12478, 1, 8), (10397, 5, 17), (10135, 3, 6)]
    totals = dict(scheduled_count=0, cancelled_count=0, arrival_eligible_count=0, late_count=0)
    subsets = {key: {**totals} for key in contexts}
    examples = {}
    for month in quality['months']:
        path = ROOT / f'data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{quality["year"]}_{month}.zip'
        with zipfile.ZipFile(path) as z:
            member = next(n for n in z.namelist() if n.endswith('.csv'))
            with z.open(member) as raw:
                for row_number, row in enumerate(csv.DictReader(TextIOWrapper(raw, encoding='utf-8-sig')), 1):
                    cancelled = row['Cancelled'] == '1.00' or row['Cancelled'] == '1.0' or row['Cancelled'] == '1'
                    # The real export must have known 0/1 status; fail if that premise changes.
                    assert row['Cancelled'] and float(row['Cancelled']) in (0, 1)
                    assert row['Diverted'] and float(row['Diverted']) in (0, 1)
                    eligible = not cancelled and float(row['Diverted']) == 0 and row['ArrDelay'] != ''
                    late = eligible and float(row['ArrDelay']) >= 15
                    counts = dict(scheduled_count=1, cancelled_count=int(cancelled),
                                  arrival_eligible_count=int(eligible), late_count=int(late))
                    time = int(row['CRSDepTime'])
                    key = (int(row['OriginAirportID']), int(row['DayOfWeek']), time // 100)
                    for name, value in counts.items():
                        totals[name] += value
                        if key in subsets:
                            subsets[key][name] += value
                    category = 'cancelled' if cancelled else 'diverted' if float(row['Diverted']) == 1 else 'late' if late else 'on_time'
                    if category not in examples:
                        examples[category] = {k: row[k] for k in ['FlightDate','Reporting_Airline',
                            'Flight_Number_Reporting_Airline','Origin','Dest','CRSDepTime','ArrDelay','ArrDel15','Cancelled','Diverted']}
                        examples[category].update({'csv_record': row_number, 'source': path.name, 'expected_counts': counts})
    assert totals == {k: quality['totals'][k] for k in totals}, (totals, quality['totals'])
    for (origin, weekday, hour), expected in subsets.items():
        selected = cube[(cube.origin_id == origin) & (cube.weekday == weekday) & (cube.hour == hour)]
        assert expected == {k: int(selected[k].sum()) for k in expected}
    # Compare actual all-origin and largest-airport context payloads before API design.
    dimensions = ['carrier','weekday','hour']
    counts = [c for c in cube if c.endswith('_count')]
    national = cube.groupby(dimensions, as_index=False)[counts].sum()
    sizes = cube.groupby('origin_id').size()
    largest_id = int(sizes.idxmax())
    largest = cube[cube.origin_id.eq(largest_id)].drop(columns=['origin_id'])
    report = {'independent_source_csv_totals': totals,
              'contexts': [{'origin_id': k[0], 'weekday': k[1], 'hour': k[2], **v} for k,v in subsets.items()],
              'source_record_examples': examples,
              'all_origin_context_json_bytes': len(national.to_json(orient='records').encode()),
              'largest_context_origin_id': largest_id,
              'largest_origin_context_json_bytes': len(largest.to_json(orient='records').encode()),
              'result': 'passed'}
    (args.output / 'independent_verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
