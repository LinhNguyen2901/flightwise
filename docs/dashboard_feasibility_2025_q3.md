# Dashboard feasibility — July–September 2025

**CONDITIONAL GO.** The approved July-September 2025 scope supports the existing architecture and safeguards. This check introduces no production API/UI, feature or milestone changes.

## Inputs and reproduction

Only the prepared July–September tables were used. The current [data audit](data_audit_2025_q3.md) explains one `2400` scheduled-time exclusion: map totals include 1,796,245 flights; time-based views include 1,796,244. The remaining selected data joins and count checks passed.

```powershell
.\.venv\Scripts\python.exe scripts/dashboard_feasibility.py --data-dir data/processed/2025-q3 --output docs/feasibility/2025-q3
node scripts/dashboard_feasibility_client.cjs docs/feasibility/2025-q3
```

These remain feasibility scripts, not the application. The same representative contexts were used: ALL, ATL, JFK, LAX, ABE and BQN, plus the lowest-volume origin in the new scope, STC (12 records). It replaces ITH only as the automatically selected stress case; neither name is a production filter restriction. The same six selections produce 42 scenarios.

Evidence links: [airport map](feasibility/2025-q3/airport_map.csv), [heatmaps](feasibility/2025-q3/heatmaps.csv), [airline bars](feasibility/2025-q3/airline_bars.csv), [filter scenarios](feasibility/2025-q3/filter_scenarios.csv), [all hourly frames](feasibility/2025-q3/airport_hour_frames.csv), [hour coverage](feasibility/2025-q3/hour_coverage.csv), [Python results](feasibility/2025-q3/results.json), [JavaScript results](feasibility/2025-q3/client_results.json).

## Three views and linked selections

The map has **348 airports**, 345 with at least 30 eligible arrivals and three below 30. Map JSON is 126,636 bytes, including coordinates, counts, rates/status and a small period envelope.

Each heatmap preserves 168 cells, with explicit null rates for no eligible arrivals. Actual coverage is:

| Context | Cells n≥30 | Cells n=1–29 | No-flight cells |
| --- | ---: | ---: | ---: |
| ALL | 154 | 14 | 0 |
| ATL | 133 | 0 | 35 |
| JFK | 119 | 8 | 41 |
| LAX | 140 | 7 | 21 |
| ABE | 0 | 83 | 85 |
| BQN | 0 | 73 | 95 |
| STC | 0 | 2 | 166 |

**Relationship A:** the national Monday 08 cell has 17,898 eligible arrivals and 2,534 late arrivals. Selecting JFK changes that same cell to 316 eligible /37 late; selecting ATL gives 915/91. BQN has no flights in that cell. The geographic selection therefore changes the time-pattern overview as intended.

**Relationship B:** at JFK, all-time carrier bars contain 26,128 eligible arrivals across seven carriers. Selecting Monday 08 changes them to 316 eligible arrivals across four carriers, all with n≥30. Selecting Friday 17 gives 250 eligible arrivals across five carriers, one below 30. The origin remains fixed.

All 42 Python bar outputs match sums of their selected heatmap cells; independent cached JavaScript reductions match every carrier/count field in all 42 outputs. Clear-time and select-all produce identical bars. Exact disjoint tuples remain essential: ATL Monday 08 + Friday 17 includes **1,532 scheduled flights**, while the incorrect Cartesian product would include **3,094**.

## Narrow filters and sparse results

| Origin / filter | Eligible n | Carrier bars | Bars n≥30 | Meaning |
| --- | ---: | ---: | ---: | --- |
| ATL, weekdays 06–09 | 13,065 | 12 | 12 | Broad window supports multiple carrier comparisons |
| ATL, Monday 08 | 915 | 9 | 3 | Six carrier bars still sparse despite a large cell total |
| LAX, Monday 08 | 634 | 10 | 6 | Four sparse carrier bars |
| JFK, Monday 08 | 316 | 4 | 4 | Useful narrow interaction demonstration |
| ABE, weekdays 06–09 | 215 | 3 | 2 | One sparse carrier remains |
| ABE, Friday 17 | 2 | 1 | 0 | 0/2 late is not evidence of superior reliability |
| BQN, weekdays 06–09 | 89 | 1 | 1 | Valid result, but no multi-carrier comparison |
| BQN, Monday 08 or Friday 17 | 0 | 0 | 0 | Explicit empty state required |
| STC, all times | 12 | 1 | 0 | Limited reporting-dataset coverage; no useful ranking |

There are 65,686 finest-level cube groups with fewer than 30 eligible arrivals (about 84%). Every populated weekday/hour cell at ABE and BQN remains below 30. The same safeguards are required: per-mark n, visible low-sample styling, separate no-flight/no-eligible states, and no winner labels. n≥30 remains a presentation caution rather than statistical assurance. Neither quarter is a basis for attributing differences to weather or carrier quality.

## Hourly animation

All **24 states** were generated with a stable 348-airport roster: **8,352 airport-hour rows**. All 168 sampled context/hour checks match equivalent all-weekday time selections. The proposed compact prefetched count-array format is **245,977 bytes uncompressed** (51,040 bytes using offline gzip), with geometry shared from the base map.

| Local hour | Scheduled nationally | Origins with flights | Origins n≥30 |
| --- | ---: | ---: | ---: |
| 00 | 3,000 | 17 | 14 |
| 01 | 764 | 11 | 7 |
| 02 | 346 | 4 | 4 |
| 03 | 189 | 2 | 2 |
| 04 | 11 | 1 | 0 |
| 06 | 123,769 | 243 | 227 |
| 12 | 106,668 | 232 | 193 |
| 18 | 105,626 | 248 | 210 |
| 23 | 15,490 | 35 | 28 |

Across all frames, 4,434 airport-hours have no flights and 713 have 1–29 eligible arrivals. Three populated airport-hours have zero eligible arrivals. All states are computationally practical, but 04:00 has only 11 records at one origin and cannot support a national reliability story. Keep that state explicit rather than silently treating it as universally reliable or carrying over earlier colors. These are historical local-hour profiles, not simultaneous UTC snapshots or flights moving through time.

## Measured local performance

Measurement approach: prepared tables loaded once; Python query + serialization repeated 50 times after one warm-up (20 for all-frame generation); JavaScript reductions repeated 200 times after 20 warm-ups. Windows, Python 3.13.5, pandas 2.3.3, Node v24.18.0. Load time was 230.0 ms with uncontrolled filesystem cache state. Several independent checks ran during this migration, so timings are not a controlled quarter-to-quarter performance comparison.

| Python query + JSON | Median ms | p95 ms | Payload bytes |
| --- | ---: | ---: | ---: |
| ALL context | 24.15 | 35.41 | 459,430 |
| ATL context | 9.47 | 13.58 | 248,475 |
| JFK context | 9.32 | 13.87 | 125,793 |
| LAX context | 11.02 | 17.92 | 265,983 |
| ABE context | 9.83 | 12.60 | 24,080 |
| BQN context | 4.86 | 8.93 | 16,478 |
| STC context | 6.15 | 10.45 | 487 |

All sampled contexts remain below the proposed 1 MB uncompressed target. National cached JavaScript timings (median /p95 ms): context JSON parsing 1.044/2.034; populated heatmap reduction 0.733/0.924; single-cell bars 0.097/0.201; disjoint-cell bars 0.174/0.291. Full verbose animation generation/serialization has median 75.27 ms and p95 114.39 ms; cached 17:00 frame serialization has median 3.84 ms and p95 5.31 ms. Prefetch the compact version once instead of requesting each tick.

These measurements exclude HTTP, FastAPI validation, React/D3 rendering, empty-grid padding in JavaScript, and transitions. They support architecture feasibility but do not certify end-to-end response or animation smoothness. No production implementation was added.

## Outcome

The month switch is viable. Proceed with the same existing design after M2 approval, retaining sample-size/empty-state safeguards and disclosing the one scheduled-time exclusion. Scope is **July–September 2025 only**; no seasonal comparison feature or other feature expansion is implied.
