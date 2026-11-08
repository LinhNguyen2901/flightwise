"""Data serialization and HTML embedding for M1.6; chart rendering is JavaScript."""
import html
import json
from pathlib import Path

import pandas as pd

from scripts.prepare_data import COUNTS, aggregate

ROOT = Path(__file__).resolve().parents[1]


def records(frame):
    return json.loads(frame.to_json(orient='records'))


def preview_payload(cube, origins, airports, period, note):
    """Pass count aggregates to D3. No raw-record cleaning or rate calculation here."""
    labels = airports[['origin_id', 'origin_code', 'DISPLAY_AIRPORT_NAME',
                       'LATITUDE', 'LONGITUDE', 'AIRPORT_STATE_CODE']].rename(
        columns={'DISPLAY_AIRPORT_NAME': 'name', 'AIRPORT_STATE_CODE': 'region'})
    if labels.origin_id.duplicated().any():
        raise ValueError('Multiple coordinate versions in this experiment; resolve explicitly before plotting')
    map_rows = origins.merge(labels, on='origin_id', validate='one_to_one')
    contexts = {'ALL': records(aggregate(cube, ['carrier', 'weekday', 'hour']))}
    # The review harness uses these representative contexts, not an application-wide cache.
    for code in ['ATL', 'JFK', 'LAX', 'ABE', 'BQN', 'STC']:
        ids = labels.loc[labels.origin_code.eq(code), 'origin_id']
        contexts[code] = records(aggregate(cube.loc[cube.origin_id.isin(ids)], ['carrier', 'weekday', 'hour']))
    # Pick an actual scheduled-but-no-eligible cell, rather than inventing an example.
    time_cells = aggregate(cube, ['origin_id', 'weekday', 'hour'])
    candidates = time_cells.loc[time_cells.scheduled_count.gt(0) & time_cells.arrival_eligible_count.eq(0)]
    no_eligible = None
    if len(candidates):
        row = candidates.iloc[0]
        code = labels.loc[labels.origin_id.eq(row.origin_id), 'origin_code'].iloc[0]
        contexts[code] = records(aggregate(cube.loc[cube.origin_id.eq(row.origin_id)], ['carrier', 'weekday', 'hour']))
        no_eligible = {'origin': code, 'cells': [[int(row.weekday), int(row.hour)]]}
    frames = {}
    for hour in [4, 8, 17]:
        counts = aggregate(cube.loc[cube.hour.eq(hour)], ['origin_id'])
        frame = origins[['origin_id']].merge(counts, on='origin_id', how='left').fillna(0)
        frame[COUNTS] = frame[COUNTS].astype('int64')
        frames[hour] = records(frame)
    return {'period': period, 'note': note, 'airports': records(map_rows), 'contexts': contexts,
            'frames': frames, 'no_eligible': no_eligible}


def preview_document(payload, options=None):
    bundle_path = ROOT / 'notebooks/build/preview.js'
    if not bundle_path.exists():
        raise FileNotFoundError('Run npm --prefix frontend run build:preview first')
    # Bundle and counts are embedded: no CDN, file-origin fetch or notebook server paths.
    bundle = bundle_path.read_text(encoding='utf-8').replace('</script', '<\\/script')
    data = json.dumps(payload, allow_nan=False).replace('<', '\\u003c')
    settings = json.dumps(options or {}, allow_nan=False).replace('<', '\\u003c')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>FlightWise — M1.6 visual review</title></head><body><div id="root"></div>'
            f'<script>{bundle}</script><script>'
            f'window.previewData={data}; window.preview=FlightWisePreview.mount('
            f'document.getElementById("root"),window.previewData,{settings});'
            'window.previewReady=true;</script></body></html>')


def show_d3(chart_type, frame=None, **options):
    """Render this cell's current DataFrame directly; never load an exported figure.

    The local bundle contains the same dashboard chart functions used by the review
    harness. Only serialization happens here; filters/grouping belong in the cell.
    """
    from IPython.display import HTML, display
    bundle = (ROOT / 'notebooks/build/cellCharts.js').read_text(encoding='utf-8')
    rows = [] if frame is None else records(frame)
    data = json.dumps({'kind': chart_type, 'rows': rows, 'options': options}, allow_nan=False).replace('<', '\\u003c')
    height = {'map': 770, 'heatmap': 480, 'hourly_overview': 610, 'diagram': 410}.get(chart_type, 530)
    if chart_type == 'diagram' and options.get('kind') == 'layout':
        height = 520
    if chart_type == 'bars':
        height = 240 + 31 * len(options.get('carrierOrder', rows))
    document = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                '<style>body{margin:0;background:white}#chart{min-width:700px;max-width:1000px;margin:auto}'
                'svg{display:block;max-width:100%;height:auto}*{box-sizing:border-box}</style>'
                '<body><div id="chart"></div>'
                f'<script>{bundle.replace("</script", "<\\/script")}</script>'
                f'<script>window.chartInput={data};'
                'window.chart=FlightWiseCell.render(document.getElementById("chart"),'
                'chartInput.kind,chartInput.rows,chartInput.options);'
                'window.chartReady=true;</script></body></html>')
    display(HTML(f'<div class="flightwise-cell-output"><iframe title="FlightWise cell: {html.escape(chart_type)}" sandbox="allow-scripts" '
                 f'style="width:100%;height:{height}px;border:1px solid #dce5ea;border-radius:8px" '
                 f'srcdoc="{html.escape(document, quote=True)}"></iframe></div>'))
