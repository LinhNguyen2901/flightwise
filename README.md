# FlightWise â€” Exploring US Flight Reliability

M1 provides reproducible acquisition and count aggregates. M1.6 adds the raw-processing notebook and reusable D3 previews. M2 adds a local FastAPI API and React foundation. M3 mounts the same four D3 views in React with real API counts. M4 links airport and exact time selections across views. M5 checks the core dashboard; M6 adds optional historical-hour playback. See PROJECT_SPEC.md and PLAN.md for the milestone boundaries.

Active analysis period: **July-September 2025**. `data/active_dataset.json` controls script defaults. Obsolete datasets, reports and snapshots were removed at the user's request after verification. Architecture, features and milestone sequence are unchanged.

## Setup (PowerShell, from the repository root)

Validated with Python 3.13.5 on Windows. Create a project-local environment; activation is not required:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-data.lock.txt
```

`requirements-data.txt` lists the direct dependencies; the lock file captures all installed versions from the validated environment. The download needs internet access to the official BTS site. Neither source requires an account or API key.

## Acquire and prepare data

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --year 2025 --months 7 8 9
.\.venv\Scripts\python.exe scripts/prepare_data.py --year 2025 --months 7 8 9 --output data/processed/2025-q3 --sample-dir data/sample/2025-q3
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\python.exe scripts/dashboard_feasibility.py
node scripts/dashboard_feasibility_client.cjs
.\.venv\Scripts\python.exe -m pytest tests/data -q
```

The downloader retrieves full reporting-carrier monthly ZIPs and submits the BTS Master Coordinate form for all reference fields. It verifies existing inputs against `data/manifest.json`, refuses untracked or changed inputs, checks ZIP integrity, and records source URLs, retrieval timestamps, sizes and SHA-256 hashes. It never silently replaces existing raw inputs. The public airport reference can change: a fresh download records its actual hash; it is not guaranteed to match an earlier reference snapshot. Preserve the archived raw inputs for exact historical reproduction.

If the BTS site changes or temporarily fails, rerun to resume using verified inputs. If a `.zip.part` remains after an interrupted attempt, the retry writes that incomplete temporary file again. For manual recovery, visit the source links in PROJECT_SPEC.md, choose Reporting Carrier On-Time Performance, year 2025 and each required month, and download the full prezipped file. For Master Coordinate, select all fields and Download. Keep original files and record their provenance; do not invent a manifest entry or bypass checksum validation. The current automated path was tested during M1.

For an optional July-only benchmark, use separate output **and sample** directories:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_data.py --months 7 --output data/verification/july --sample-dir data/verification/july-sample
.\.venv\Scripts\python.exe scripts/verify_data.py --output data/verification/july
```

Processing the same inputs and period twice produces the same Parquet hashes. Runtime/memory measurements in quality reports may differ. Output and sample directories containing another period are rejected: choose separate `--output` and `--sample-dir` paths. Feasibility scripts also refuse to write another period into an existing report directory.

## Outputs and correctness

- `data/raw/`: immutable official ZIPs; ignored by Git.
- `data/manifest.json`: source acquisition provenance.
- `data/active_dataset.json`: active period and directory defaults for future application work.
- `data/processed/2025-q3/flights_2025_MM.parquet`: normalized row-level audit data, including excluded-arrival and mapping flags; source identity/detail remain in original ZIPs.
- `data/processed/2025-q3/cube.parquet`: counts by origin ID, reporting carrier, weekday (Monday=1) and scheduled local departure hour (0â€“23).
- `data/processed/2025-q3/origin_counts.parquet`: all scheduled-flight origin counts, including records without usable departure times.
- `data/processed/2025-q3/airports.parquet`: used historical airport sequences and coordinates. Preserve variants rather than selecting an arbitrary coordinate row.
- `data/processed/2025-q3/quality_report.json`: input hashes, actual headers, missingness, join diagnostics, counts, output hashes and performance.
- `data/processed/2025-q3/independent_verification.json`: independent CSV-based totals, three selected-context checks, source-row examples, and estimated context JSON sizes.
- `data/sample/2025-q3/`: first 100 real records per month with selected source columns, plus used airport reference rows and provenance. This sample demonstrates schema and is **not representative** for estimating flight reliability.
- `docs/data_audit_2025_q3.md` and `docs/dashboard_feasibility_2025_q3.md`: active-quarter audit and feasibility results. Supporting JSON/CSV is in `docs/feasibility/2025-q3/`.

Late arrival means at least 15 minutes late among completed, non-diverted flights with known consistent arrival classification. Cancellation rate uses all scheduled flights; it is null if cancellation statuses are unknown. Aggregate numerators and denominators before calculating rates. Zero denominators are null. Missing values never imply on-time arrival. `2400` is currently quarantined pending confirmation of BTS convention; the observed scope's handling is documented in the audit.

Synthetic fixtures live only in `tests/data/`; production outputs use BTS data. The tests exercise missing values, threshold boundaries, invalid times, historical joins, duplicates, date checks and weighted rates. `verify_data.py` uses Python's CSV reader and arrival-delay minutes independently of preparation helpers to reconcile real totals and selected cells.

## M1.6 notebook and visual review

Open [notebooks/dashboard_preview.ipynb](notebooks/dashboard_preview.ipynb). It reads the original Julyâ€“September ZIPs, shows missing and invalid values for each month, records two flight-row removals and one airport-reference removal, builds the geographic analysis summaries, and renders charts from those summaries. Cancellations and diversions remain available for disruption analysis; eligible arrivals are shown as a separate filtered population. The three original dashboard previews and proposed fourth hourly overview use reusable D3 modules. Matplotlib handles the simpler exploratory plots, while a D3 named-airport comparison retains hover/focus details. The notebook no longer needs previously processed baseline files. See [docs/design_decisions.md](docs/design_decisions.md) for why these choices were made.

Install the notebook environment (the full lock includes data dependencies), then the pinned chart tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-preview.lock.txt
npm --prefix frontend ci
npm --prefix frontend run build:preview
.\.venv\Scripts\python.exe -m jupyterlab notebooks/dashboard_preview.ipynb
```

Choose the project `.venv` Python kernel. Review the code, then **Restart Kernel and Run All**. Alternatively, execute and save from a fresh project-local kernel without opening the UI:

The setup cell accepts Jupyter running from either the project folder or its `notebooks` folder. The local D3 helper is imported only when the first D3 chart is reached. If you use a different kernel environment, install the preview requirements into that kernel first.

```powershell
.\.venv\Scripts\python.exe scripts/execute_preview_notebook.py
```

The notebook uses a few short, visible functions to repeat the same inspection and cleaning for each month without holding all raw months in memory at once. Edit the rules, then restart/run all and inspect the reconciliation table. The notebook does not overwrite the immutable raw ZIPs, active dataset configuration or historical M1 processed files.

For chart exploration, change `CONTEXT_AIRPORT` or `SELECTED_CELLS` in the dashboard-preview section and rerun that cell and its dependent chart cells. A chart-filter change does not require rerunning raw processing. After a cleaning or scope change, restart/run all so downstream outputs are current.

The shared D3 modules in `frontend/src/charts/` are bundled locally and embedded in each chart output. `show_d3` serializes the supplied DataFrame and invokes rendering; filtering and grouping remain visible in notebook cells. No CDN, API or saved chart image is needed for notebook display. JupyterLab is the supported live viewer; static viewers may not execute the D3 figures. Superseded standalone figure exports were removed; the executed notebook and current screenshots are the review package.

`requirements-preview.txt` documents the direct notebook dependencies, including Matplotlib. The lockfile records the validated environment. The saved notebook contains the executed outputs for review. The combined hourly chart overlays scheduled-flight-share bars and a late-rate line in one D3 plot with labelled left and right percentage axes. It is mounted as the fourth M3 web view.

For chart-code edits, rebuild and rerun the desired notebook chart cell. Focused checks are:

```powershell
npm --prefix frontend run build:preview
npm --prefix frontend test
.\.venv\Scripts\python.exe -m pytest tests/notebook -q
```

The notebook provides editable pandas summaries, D3 tooltips and selection styling. Its exploratory figures do not expand the production dashboard scope. M3 mounts the reviewed D3 modules in React, M4 implements live linked selections, and M6 optionally implements playback.

## M2 local application

From the repository root, install the backend and frontend dependencies and build the API-ready aggregates:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
npm --prefix frontend ci
.\.venv\Scripts\python.exe -m scripts.build_dashboard_data
```

The script verifies raw ZIP hashes and writes `data/processed/2025-q3/dashboard/`. Its 340-origin counts use the notebook's reviewed two flight-row removals and contiguous-U.S./Alaska/Hawaii origin scope. Earlier M1 Parquet files in the parent directory remain historical evidence. The API will fail at startup if dashboard files are absent or their totals disagree.

Start these commands in **two PowerShell windows**, both from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173/`. The API is at `http://127.0.0.1:8000/api/health`; interactive API docs are at `http://127.0.0.1:8000/docs`. The frontend's API URL is defined in `frontend/src/api.ts` and can be overridden with `VITE_API_BASE_URL`. The allowed frontend origin defaults to `http://localhost:5173` (plus `127.0.0.1:5173`) and can be changed with `FLIGHTWISE_FRONTEND_ORIGIN`; the prepared-data directory can be changed with `FLIGHTWISE_DATA_DIR`. These are local settings, not deployment instructions.

Run focused M2 checks from the root:

```powershell
.\.venv\Scripts\python.exe scripts/verify_dashboard_sample.py
.\.venv\Scripts\python.exe -m pytest tests/backend -q
npm --prefix frontend run build
```

`docs/design.md` explains the small data/API/React flow. [This screenshot](docs/figures/m2_foundation.png) records the earlier M2 foundation.

## M3 local dashboard

Use the same two start commands above and open `http://127.0.0.1:5173/`. The page shows the airport map, combined hourly bar/line chart, weekday-by-hour heatmap and airline comparison using the M2 API. Scroll over a map panel to zoom and drag its background to pan. Mainland, Alaska and Hawaii zoom independently. Bubbles keep a steady screen size while more airport codes appear where labels fit. Hover or keyboard-focus a mark for its full name, counts and rates. On narrow screens, scroll each chart horizontally to inspect its full axis and legend. The page shows loading, empty-data and retryable API-error states. [Desktop](docs/figures/m3_dashboard.png), [zoomed map](docs/figures/m3_map_zoom.png) and [narrow-screen](docs/figures/m3_narrow.png) screenshots record the earlier M3 view, which still had a local Reset map button.

The map, heatmap and airline bars now share one smooth Viridis late-rate gradient from 0% to **50%+**. The airport rates motivated the cap: 95% of the 340 airports have rates at or below about 33%. Exact rates above 50% remain in hover and keyboard-focus details. Airline bar length still uses a fixed 0â€“100% axis. The shared D3 preview bundle was rebuilt; saved notebook outputs need a rerun to show this later palette change.

Run M3 checks while the backend and frontend are running:

```powershell
npm --prefix frontend test
npm --prefix frontend run build
.\.venv\Scripts\python.exe scripts/verify_m3_browser.py
```

The browser check uses locally installed Chrome. If it is installed elsewhere, adjust `executable_path` in the script. It records the M3 all-origin baseline before M4 linked selections.

## M4 linked selections

Click an airport bubble to select it; click again to clear it. Keyboard users can focus a bubble and press Enter or Space. The map stays an all-airport overview and keeps independent zoom/pan, code-only labels and the 0â€“50%+ Viridis legend. The heatmap and hourly view show the chosen airport's context. Click time cells to toggle exact weekday/hour tuples, or focus a cell and press Enter/Space. **Brush time cells** enables a one-drag rectangle that replaces the current cell set; **Cancel brush** returns to clicking. The global **Clear airport**, **Clear time**, and **Reset all** buttons reverse selections. Pink hover/focus and selection outlines stand apart from the Viridis rate colors. Hovering or keyboard-focusing a mark opens the detail tooltip, including diverted flights as a share of scheduled flights. The thin native SVG title strip has been removed. The heatmap remains a full 168-cell overview while airline bars use the selected airport and union of exact time tuples. Airport changes retain selected times.

The selection summary shows current filters. **Clear airport**, **Clear time** and **Reset all** are available above the charts. Loading, selected-context error/retry and empty-intersection states appear in the chart area. Context responses are cached by airport and version; stale requests are aborted and ignored.

Manual heatmap and airline changes animate over 300 ms to make the changed rates easier to follow. Browsers requesting reduced motion get immediate updates.

With the API and frontend running on ports 8000 and 5173, run:

```powershell
npm --prefix frontend test
npm --prefix frontend run build
.\.venv\Scripts\python.exe scripts/verify_m4_browser.py
```

See `docs/verification.md` for the interaction matrix and actual test results. `docs/figures/m4_linked.png` is a browser screenshot from the verification run.

## M5 core acceptance review

M5 verified the existing four-view dashboard and the two linked selection pairs. For a full 168-cell brush, the summary says that all cells are selected instead of printing 168 tuple labels. The map, heatmap and airline encodings are unchanged. [Desktop](docs/figures/m5_desktop.png) and [narrow](docs/figures/m5_narrow.png) screenshots show the M5 layout. Narrow chart cards scroll horizontally so their axes remain readable.

With the API and frontend running on the documented ports, run:

```powershell
.\.venv\Scripts\python.exe scripts/verify_m4_browser.py
.\.venv\Scripts\python.exe scripts/verify_m5_browser.py
.\.venv\Scripts\python.exe -m scripts.profile_m5_api
npm --prefix frontend test
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m pytest tests/data tests/backend -q
```

The M5 clean-environment check installed `requirements-backend.txt` into a separate virtual environment, ran `npm ci` and `npm run build` in a separate frontend copy, rebuilt data from the verified raw ZIPs to an isolated directory, and started the API/frontend on alternate ports 8001/5175 for a browser smoke check. Results and local payload/timing measurements are in [docs/verification.md](docs/verification.md). [Report](docs/report_outline.md) and [demo](docs/demo_outline.md) outlines are drafts for student review, not final submission artifacts. M6 was authorized afterward; M7 report/video and M8 packaging still require approval.

## M6 historical-hour playback

Restart the backend after pulling these code changes so `/api/airport-hours` is available, then start the frontend using the ordinary commands above. The page prefetches all 24 hourly map frames once. **Start playback** begins at 00:00 immediately; **Pause** and the 00â€“23 slider control it, and **Exit** restores manual time cells. Playback stops at 23:00; **Replay** starts a new pass from 00:00. Each frame pools flights scheduled in the same local departure hour across Julyâ€“September 2025; it is not a live day or common UTC snapshot. The map keeps all origin airports and fixed frame scales, the heatmap outlines the active hour, and airline bars compare that hour across all weekdays at the selected origin.

Manual heatmap cells are visibly suspended during playback and restored on Exit. Clicking or brushing a time cell exits playback first. Changing airports preserves the hour and pauses playback while the selected context loads. Seeking pauses. Reset all stops playback and clears filters. If the browser requests reduced motion, the entry button says **Explore hours manually** and opens the slider without automatic motion. If frame prefetch fails, the original charts still work and **Retry frames** retries the optional response.

With API/Vite running on the ordinary ports, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend -q
npm --prefix frontend test
npm --prefix frontend run build
.\.venv\Scripts\python.exe scripts/verify_m6_browser.py
```

The [hour-08 screenshot](docs/figures/m6_hour08.png) and [verification notes](docs/verification.md) record the checked behavior. The shared notebook preview bundle was rebuilt after chart-source edits; saved notebook outputs were not rerun. The feature is optional advanced work; bonus credit is not guaranteed. M7 report/video and M8 packaging still require separate approval.

## Guided layout review

In comparison mode, a dashed pink map ring marks the pinned airport and a solid pink ring marks the current airport. Each lower profile overlays pale bars for that airport's share of scheduled flights and a teal line for its late-arrival rate. The panels share the same left and right axis scales. The rings stay the same screen size during map zoom. [Map capture](docs/figures/airport_comparison_map.png) and [comparison capture](docs/figures/airport_comparison.png) show this mode.

The optional two-airport comparison uses the existing full-width all-hour section. Select an airport on the map, choose **Pin airport to compare** in Current exploration, then select another airport on the map. The lower section shows both airports' late-arrival rates across 24 scheduled local departure hours on the same percentage axis, with counts and sparse-hour cues. The three linked views continue to follow the current map airport and selected heatmap cells. **Clear comparison** restores the original combined hourly chart; **Reset all** clears the pin too. On narrow screens, swipe sideways within the comparison card to see both profiles. [Desktop](docs/figures/airport_comparison.png), [narrow](docs/figures/airport_comparison_narrow.png), and [restore instructions](docs/revisions/pre_airport_comparison_2026-11-07/RESTORE.md) are available for review. This feature is optional extra-credit material, not a guaranteed bonus award.

The current page has three numbered steps: choose an airport on the map, choose exact weekday/hour cells in the heatmap, then compare airlines for both selections. The header shows three summary cards for scheduled flights, origin airports and reporting airlines above Current exploration. The title is larger with more space around it. On desktop, the map fills the left side, with the wider contiguous-U.S. map above Alaska and Hawaii; the heatmap and airline bars stack on the right. The heatmap question sits beside its section heading, and the airline section no longer repeats a question inside the chart. Scroll past the short introduction to see this full-screen-height section together at 1920Ã—1080 or 1366Ã—768; the three cards have no internal vertical scrolling. The local map reset and heatmap clear buttons, repeated instructions, playback guidance paragraph, and duplicate subtitles were removed to give the charts more room; the global clear/reset buttons remain above the section. The supporting all-hour chart is full width below; it keeps all weekdays even when heatmap cells are selected. Its pale teal bars show scheduled-flight share and its stronger teal line shows arrival-late rate on separate labelled percentage axes. Active playback puts Exit, Play/Pause, the hour label and slider on one row; at 23:00 the action reads Replay. Narrow screens retain the stacked reading order and horizontal chart scrolling. The linked screenshots show the current header and chart layout. The [immediately prior frontend files](docs/revisions/pre_insets_below_2026-11-07/RESTORE.md) can be restored.

To restore the immediately previous map-centered layout, follow [the exact copy commands](docs/revisions/pre_three_view_focus_2026-11-07/RESTORE.md). The older guided and stacked versions remain saved separately. The API, data and selection logic are unchanged.

## Submission

Before submission, include data if practical, or retain the working downloader plus sample. Exclude `.venv`, caches and dependency folders from the ZIP. Follow the four-artifact checklist in ASSIGNMENT_REQUIREMENTS.md. AI assistance with planning and data tooling must be disclosed; the student reviews and owns the submitted work.
