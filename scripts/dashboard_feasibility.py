"""M1.5 disposable analysis: processed counts only, no API or application code."""
import hashlib
import argparse
import json
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
try:
    from .dataset_config import active_dataset, period_label
except ImportError:
    from dataset_config import active_dataset, period_label

ROOT = Path(__file__).resolve().parents[1]
active = active_dataset()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path, default=ROOT / active['processed_dir'])
parser.add_argument('--output', type=Path, default=ROOT / active['feasibility_dir'])
args = parser.parse_args()
DATA = args.data_dir
quality = json.loads((DATA / 'quality_report.json').read_text())
PERIOD = period_label(quality)
OUT = args.output
if (OUT / 'results.json').exists():
    previous_period = json.loads((OUT / 'results.json').read_text())['period'].replace(' through ', '/')
    if previous_period != PERIOD:
        raise ValueError('Feasibility output contains another period; choose separate --output')
OUT.mkdir(parents=True, exist_ok=True)
start = time.perf_counter()
cube = pd.read_parquet(DATA / 'cube.parquet')
origins = pd.read_parquet(DATA / 'origin_counts.parquet')
airports = pd.read_parquet(DATA / 'airports.parquet')
load_ms = (time.perf_counter() - start) * 1000
COUNTS = [c for c in cube if c.endswith('_count')]
DIMS = ['carrier', 'weekday', 'hour']
codes = airports.set_index('origin_code').origin_id.to_dict()


def grouped(frame, dims):
    return frame.groupby(dims, as_index=False, observed=True)[COUNTS].sum()


def annotated(frame):
    frame = frame.copy()
    n = frame.arrival_eligible_count
    frame['late_rate'] = frame.late_count.div(n.where(n.gt(0)))
    frame['cancellation_rate'] = frame.cancelled_count.div(frame.scheduled_count.where(
        frame.scheduled_count.gt(0) & frame.cancellation_eligible_count.eq(frame.scheduled_count)))
    frame['sample_status'] = np.select([frame.scheduled_count.eq(0), n.eq(0), n.lt(30)],
                                       ['no_flights', 'no_eligible_arrivals', 'low_n'], default='n_ge_30')
    return frame


def payload(frame):
    # Records-oriented aggregate JSON; includes modest period/scope metadata.
    return ('{"period":' + json.dumps(PERIOD) + ',"data":' + frame.to_json(orient='records', double_precision=10) + '}').encode()


def bench(fn, repeats=50):
    fn()  # warm-up excluded; first disk load is measured separately
    times = []
    for _ in range(repeats):
        then = time.perf_counter()
        fn()
        times.append((time.perf_counter() - then) * 1000)
    return {'iterations': repeats, 'median_ms': round(float(np.median(times)), 3),
            'p95_ms': round(float(np.percentile(times, 95)), 3), 'max_ms': round(max(times), 3)}


def context(code):
    if code == 'ALL':
        return grouped(cube, DIMS)
    return cube.loc[cube.origin_id.eq(codes[code]), DIMS + COUNTS].reset_index(drop=True)


def heatmap(ctx):
    grid = pd.MultiIndex.from_product([range(1, 8), range(24)], names=['weekday', 'hour'])
    cells = grouped(ctx, ['weekday', 'hour']).set_index(['weekday', 'hour']).reindex(grid, fill_value=0).reset_index()
    return annotated(cells)


def select(ctx, cells):
    if not cells:
        return ctx
    keys = set(cells)
    return ctx.loc[[(int(d), int(h)) in keys for d, h in zip(ctx.weekday, ctx.hour)]]


def bars(ctx, cells):
    return annotated(grouped(select(ctx, cells), ['carrier']))


def save(frame, name):
    frame.to_csv(OUT / name, index=False, lineterminator='\n')


map_data = annotated(origins.merge(airports[['origin_id', 'origin_code', 'LATITUDE', 'LONGITUDE']], on='origin_id'))
save(map_data, 'airport_map.csv')
selected_codes = ['ALL', 'ATL', 'JFK', 'LAX', 'ABE', 'BQN']
# Add the lowest-volume actual origin as an explicitly labelled stress case.
smallest = map_data.sort_values(['scheduled_count', 'origin_code']).iloc[0].origin_code
if smallest not in selected_codes:
    selected_codes.append(smallest)
contexts = {code: context(code) for code in selected_codes}
filters = {
    'all_times': [],
    'weekday_morning_06_09': [(d,h) for d in range(1,6) for h in range(6,10)],
    'monday_08': [(1,8)],
    'friday_17': [(5,17)],
    'disjoint_mon08_fri17': [(1,8),(5,17)],
    'all_days_03': [(d,3) for d in range(1,8)],
}
summary = {'period': PERIOD, 'load_ms': round(load_ms,3),
           'environment': {'python': platform.python_version(), 'pandas': pd.__version__,
                           'platform': platform.platform()},
           'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA/'cube.parquet',DATA/'origin_counts.parquet',DATA/'airports.parquet']},
           'map': {'rows':len(map_data), 'json_bytes':len(payload(map_data)),
                   'sample_status_counts':map_data.sample_status.value_counts().to_dict()},
           'smallest_origin_stress_case': str(smallest), 'contexts': {}, 'benchmarks': {},
           'checks': []}
scenarios, all_bars, all_heatmaps = [], [], []
for code, ctx in contexts.items():
    hm = heatmap(ctx)
    all_heatmaps.append(hm.assign(context=code))
    summary['contexts'][code] = {'rows':len(ctx), 'json_bytes':len(payload(ctx)),
        'scheduled':int(ctx.scheduled_count.sum()), 'eligible':int(ctx.arrival_eligible_count.sum()),
        'heatmap_json_bytes':len(payload(hm)), 'heatmap_status':hm.sample_status.value_counts().to_dict()}
    summary['benchmarks']['context_'+code] = bench(lambda code=code: payload(context(code)))
    for name, cells in filters.items():
        result = bars(ctx, cells)
        all_bars.append(result.assign(context=code, selection=name))
        scheduled = int(result.scheduled_count.sum())
        eligible = int(result.arrival_eligible_count.sum())
        scenarios.append({'context':code,'selection':name,'scheduled':scheduled,'eligible':eligible,
            'late':int(result.late_count.sum()), 'carriers':len(result),
            'carriers_n_ge_30':int(result.arrival_eligible_count.ge(30).sum()),
            'low_n_carriers':int(result.arrival_eligible_count.between(1,29).sum()),
            'no_eligible_carriers':int(result.arrival_eligible_count.eq(0).sum()),
            'min_carrier_n':int(result.arrival_eligible_count.min()) if len(result) else None,
            'max_carrier_n':int(result.arrival_eligible_count.max()) if len(result) else None,
            'bar_json_bytes':len(payload(result))})
        # Check B against summed selected heatmap cells: no raw data validation repeated.
        expected = select(hm, cells)[COUNTS].sum()
        assert all(int(result[c].sum()) == int(expected[c]) for c in COUNTS)
    # Clear/select-everything preserve the full context.
    assert bars(ctx, []).equals(bars(ctx, [(d,h) for d in range(1,8) for h in range(24)]))
    summary['benchmarks']['heatmap_'+code] = bench(lambda ctx=ctx: payload(heatmap(ctx)))
    summary['benchmarks']['bars_narrow_'+code] = bench(lambda ctx=ctx: payload(bars(ctx, [(1,8)])))
save(pd.concat(all_heatmaps), 'heatmaps.csv')
save(pd.concat(all_bars), 'airline_bars.csv')
save(pd.DataFrame(scenarios), 'filter_scenarios.csv')
summary['checks'].append(f'B: all {len(scenarios)} context/filter combinations match selected heatmap counts; clear/select-all match')
# A changes the heatmap at a fixed time; compare a specific real cell, not just global totals.
summary['relationship_A_mon08'] = [{**{'context':code}, **heatmap(ctx).query('weekday == 1 and hour == 8')[
    ['scheduled_count','arrival_eligible_count','late_count','late_rate']].iloc[0].to_dict()} for code,ctx in contexts.items()]
atl = contexts['ATL']
correct = bars(atl, [(1,8),(5,17)])
cartesian = bars(atl, [(1,8),(1,17),(5,8),(5,17)])
assert int(correct.scheduled_count.sum()) != int(cartesian.scheduled_count.sum())
summary['tuple_guard'] = {'exact_selected_scheduled':int(correct.scheduled_count.sum()),
                          'incorrect_cartesian_scheduled':int(cartesian.scheduled_count.sum())}
summary['checks'].append('Exact disjoint tuples demonstrably differ from Cartesian-product filtering')
# Animation: stable full airport roster for each hour, including no-flight entries.
def animation():
    base = grouped(cube, ['origin_id','hour']).set_index(['origin_id','hour'])
    grid = pd.MultiIndex.from_product([origins.origin_id,range(24)], names=['origin_id','hour'])
    return annotated(base.reindex(grid, fill_value=0).reset_index())
frames = animation()
save(frames, 'airport_hour_frames.csv')
hours = []
for hour, frame in frames.groupby('hour'):
    hours.append({'hour':int(hour), 'scheduled':int(frame.scheduled_count.sum()),
                  'eligible':int(frame.arrival_eligible_count.sum()),
                  **{k:int(frame.sample_status.eq(k).sum()) for k in ['no_flights','no_eligible_arrivals','low_n','n_ge_30']},
                  'json_bytes':len(payload(frame))})
    for code, ctx in contexts.items():
        expected = frame if code=='ALL' else frame[frame.origin_id.eq(codes[code])]
        actual = bars(ctx, [(d,int(hour)) for d in range(1,8)])
        assert all(int(actual[c].sum())==int(expected[c].sum()) for c in COUNTS)
save(pd.DataFrame(hours), 'hour_coverage.csv')
summary['animation'] = {'rows':len(frames), 'json_bytes_full':len(payload(frames)),
                        'json_bytes_counts_only':len(payload(frames[['origin_id','hour']+COUNTS])),
                        'hours':hours}
summary['benchmarks']['animation_build_and_serialize_24'] = bench(lambda:payload(animation()), repeats=20)
summary['benchmarks']['cached_frame_serialize'] = bench(lambda:payload(frames[frames.hour.eq(17)]))
summary['checks'].append(f'All 24 animation hours match equivalent all-weekday bar selections in all {len(contexts)} contexts')
# Persist only contexts needed to benchmark JavaScript cached selections, not a frontend.
client = {'counts':COUNTS,'contexts':{k:json.loads(v.to_json(orient='records')) for k,v in contexts.items()},
          'filters':filters,'expected_bars':json.loads(pd.concat(all_bars).to_json(orient='records'))}
(OUT/'client_inputs.json').write_text(json.dumps(client,separators=(',',':')),encoding='utf-8')
# Null-safe conversion for empty heatmap example rates.
summary = json.loads(pd.Series(summary).to_json())
(OUT/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
import gzip
columns = ['origin_id','hour'] + COUNTS
compact = {'period':PERIOD,'columns':columns,'data':frames[columns].values.tolist()}
encoded = json.dumps(compact,separators=(',',':'),allow_nan=False).encode()
(OUT/'animation_compact.json').write_bytes(encoded)
(OUT/'supplement.json').write_text(json.dumps({
    'compact_animation_bytes':len(encoded), 'compact_animation_gzip_bytes':len(gzip.compress(encoded,mtime=0)),
    'frame_rows':len(frames), 'animation_sparse_rows':int(frames.arrival_eligible_count.between(1,29).sum()),
    'animation_empty_rows':int(frames.scheduled_count.eq(0).sum()),
},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'map':summary['map'],'contexts':summary['contexts'],'checks':summary['checks']},indent=2))
