"""Independently count JFK flights in raw ZIPs and compare with dashboard data."""
from pathlib import Path
import zipfile

import pandas as pd

root = Path(__file__).resolve().parents[1]
scheduled = cancelled = diverted = eligible = late = 0
for month in [7, 8, 9]:
    path = root / f'data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_{month}.zip'
    with zipfile.ZipFile(path) as archive:
        name = next(name for name in archive.namelist() if name.lower().endswith('.csv'))
        with archive.open(name) as source:
            rows = pd.read_csv(source, usecols=['Origin', 'CRSDepTime', 'ArrDel15',
                                                 'ArrDelay', 'Cancelled', 'Diverted'])
    jfk = rows.loc[rows.Origin.eq('JFK')].copy()
    time = pd.to_numeric(jfk.CRSDepTime, errors='coerce')
    valid_time = time.between(0, 2359) & (time % 100).lt(60)
    unexplained = (jfk.ArrDel15.isna() & jfk.ArrDelay.isna() &
                   jfk.Cancelled.eq(0) & jfk.Diverted.eq(0))
    jfk = jfk.loc[valid_time & ~unexplained]
    scheduled += len(jfk)
    cancelled += int(jfk.Cancelled.eq(1).sum())
    diverted += int(jfk.Diverted.eq(1).sum())
    has_arrival = jfk.ArrDel15.notna() | jfk.ArrDelay.notna()
    arrived = jfk.Cancelled.eq(0) & jfk.Diverted.eq(0) & has_arrival
    eligible += int(arrived.sum())
    late += int((arrived & (jfk.ArrDel15.eq(1) |
                            (jfk.ArrDel15.isna() & jfk.ArrDelay.ge(15)))).sum())

airports = pd.read_parquet(root / 'data/processed/2025-q3/dashboard/airports.parquet')
jfk_result = airports.loc[airports.origin_code.eq('JFK')].iloc[0]
observed = (scheduled, cancelled, diverted, eligible, late)
prepared = tuple(int(jfk_result[key]) for key in ['scheduled_count', 'cancelled_count',
                                                 'diverted_count', 'arrival_eligible_count',
                                                 'late_count'])
print('Independent raw JFK counts:', observed)
print('Prepared JFK counts:', prepared)
assert observed == prepared
