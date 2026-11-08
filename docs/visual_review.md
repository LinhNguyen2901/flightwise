# FlightWise M1.6 visual review

**The user accepted this package as good enough to begin M2, with possible later refinements.** The [executed notebook](../notebooks/dashboard_preview.ipynb) is the current visual reference. It has 67 cells, including 32 code cells, and reads the original July–September 2025 BTS ZIPs. The larger cell count reflects short steps and brief explanations rather than more analysis stages. It does not need a previously processed table or load exported chart images. [README](../README.md#m16-notebook-and-visual-review) gives exact setup and run commands; [decision record](design_decisions.md) explains the choices made during review.

The older standalone gallery and SVG exports from the 348-origin design were removed as superseded generated files. The linked screenshots under [figures/process/](figures/process/) show current browser rendering. The notebook keeps its own visible chart outputs and does not read exported figures.

## What the notebook now shows

| Section | Review question |
| --- | --- |
| 1–2 | Which raw files and airport reference are used? What is missing or invalid in the coordinate reference, and why is the `ZZZ` row removed from the working copy? |
| 3 | What is missing/invalid in each month? Which raw records are removed, retained for disruptions or outside the chosen origin geography? How do raw, cleaned, scoped and eligible-arrival counts reconcile? |
| 4 | How do the three months become named count summaries without a saved baseline dependency? |
| 5–6 | What do delay minutes, monthly late/cancellation/diversion rates, airline disruption shares and scheduled-hour patterns look like? The aligned hourly chart is proposed as a fourth dashboard view; the other plots remain notebook exploration. |
| 7 | How do the revised D3 map, two heatmap contexts and sorted airline bars look? Can selected, sparse, empty and no-eligible contexts be understood? |
| 8–9 | Do layout, coordination, architecture, UI-state and optional playback sketches match the intended app? What limitations should the report disclose? |

The preparation cells report issue counts and percentages, show affected source records, then show the selected treatment and before/after totals. The same processing steps are applied to July, August and September. Short helper functions repeat those steps without three copied pipelines or holding all raw months in memory at once.

## Revised data scope and actual results

The dashboard preview covers **origin airports in the contiguous U.S., Alaska and Hawaii**. It does not restrict destination airports. The raw sources remain unchanged. The notebook's working data removes one July scheduled-time `2400` flight and one September flight with an unexplained missing arrival outcome. The working airport reference excludes `ZZZ`, which has no coordinates and matches no quarter origin.

| Population | Flights |
| --- | ---: |
| Raw July–September source rows | 1,796,245 |
| Removed for invalid scheduled HHMM | 1 |
| Removed for unexplained missing arrival outcome | 1 |
| Outside selected origin geography | 10,794 |
| Dashboard analysis rows | 1,785,449 |
| Eligible ordinary arrivals | 1,754,276 |

Among dashboard rows there are **24,725 cancellations, 6,448 diversions and 401,327 arrivals at least 15 minutes late**. There are **340 origin airports** and **77,051 grouped origin × reporting-airline × weekday × hour rows**. These numbers intentionally differ from the older all-origin M1 files, which remain historical evidence and must be regenerated under the revised scope before API integration.

The cancellation and diversion exploration uses scheduled flights as its denominator. The late-arrival rate uses eligible arrivals. The rates are kept distinct. July has the highest observed monthly late, cancellation and diversion rates within this quarter; three monthly points do not establish annual seasonality or a cause.

## Chart and diagram approval inventory

The current designs were accepted to proceed to M2 and M3. M3 mounts the four D3 views in the web app; see the current [dashboard screenshot](figures/m3_dashboard.png). The student also accepted the later map zoom, code-label and color refinements; their rationale is in [design decisions](design_decisions.md#m3-airport-map-refinements--november-5). Saved notebook outputs and process screenshots show their earlier rendered state until those cells are rerun with the rebuilt preview bundle.

| Item | Current review evidence |
| --- | --- |
| Airport map: state outlines, bubble sizes/colors, Alaska and Hawaii insets, 340-origin scope | [current web map](figures/m3_dashboard.png), [zoomed map](figures/m3_map_zoom.png); [earlier notebook output](figures/process/map.png), notebook section 7 |
| Named comparison of 15 busiest airports: separate volume/rate scales and hover details | [comparison screenshot](figures/process/airport_compare.png), notebook section 7 |
| Main hourly overview: scheduled-flight-share bars and arrival-late-rate line overlaid in one plot, with left and right percentage axes | [current web dashboard](figures/m3_dashboard.png); [notebook preview](figures/process/hourly_overview.png), section 6 |
| Weekday × scheduled-hour heatmap: selected JFK context and all-origin comparison | [heatmap screenshot](figures/process/heatmap.png), notebook section 7 |
| Airline bars: full names, rate ordering, compact layout, keyboard/hover details | [bar screenshot](figures/process/bars.png), notebook section 7 |
| Sparse, no-flight and no-eligible contexts | Notebook section 7; ABE Friday 17, ABE Tuesday 04, BTV Tuesday 13 |
| Static 04:00, 08:00 and 17:00 local-hour map states | Notebook section 7 |
| Dashboard layout with proposed hourly view and two selection relationships | [layout sketch](figures/process/diagram.png), notebook section 8 `layout` and `coordination` sketches |
| Planned frontend/API/data flow, loading/error/empty states | Notebook section 8, `architecture` and `states` sketches |
| Optional playback storyboard | Notebook section 8, `playback` sketch; implementation still requires M6 approval |

The notebook displays dashboard previews via the same D3 modules now mounted in React. Editing `CONTEXT_AIRPORT` or `SELECTED_CELLS` recomputes the preview from notebook aggregates. Live cross-view clicking/dragging, HTTP requests, stale-response handling and playback are **not implemented by this notebook**; web API loading is implemented in M2/M3, while linked selection remains M4.

## Verification and limitations

- The revised notebook executed from a clean local kernel with no cell errors. Its saved outputs contain raw/cleaned counts, Matplotlib exploration and the D3 previews.
- Four focused notebook cleaning tests passed. Four JavaScript count/selection tests passed.
- [Browser checks](figures/process/browser_checks.json) rendered **17 direct D3 outputs** from the saved notebook, checked input-to-mark counts, keyboard details, lack of external requests and a synthetic changed-input update. Screenshots of the current map, airport comparison, hourly overview, heatmap and airline bars were inspected. The synthetic update is test-only and is not part of the source data.
- Earlier JupyterLab viewer checks applied to the prior notebook layout. The revised outputs use the same local iframe mechanism and passed actual browser rendering; a separate JupyterLab-specific visual check has not been repeated yet.
- The older feasibility results concern the all-origin historical M1 aggregates. They support the architecture but are not performance measurements for the revised notebook or future HTTP API.
- Observed airline/airport differences reflect route mix and selected period as well as performance. Sparse groups need their eligible-flight counts. Scheduled local hour is neither actual departure time nor synchronized UTC time.

The student accepted M1.6 to begin M2 and later authorized M3. M4 and optional animation remain separate milestones requiring authorization.
