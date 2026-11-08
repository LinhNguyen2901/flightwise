# FlightWise — Project Specification

Status: July–September 2025 remains the approved period. The user accepted M1.6 and authorized M2–M6. M2 provides the scoped dashboard data and FastAPI API. M3 mounts four reviewed D3 views with live API counts in React. M4 links map airport selection to the heatmap and exact heatmap time tuples to airline bars. M5 verifies the core dashboard. M6 adds the optional historical-hour playback. The earlier M1 files remain historical. M7 and later milestones remain pending approval.
Planning date: November 4, 2026 (America/New_York).

## Purpose and scope

The later comparison refinement marks pinned/current airports with dashed/solid pink map rings and gives both hourly profiles the original combined bars-and-line encoding. Scheduled-flight shares use each airport's own total, and both panels hold their separate share and late-rate axes to common scales.

After M6, the student explicitly authorized an optional, reversible two-airport comparison. The current airport can be pinned; selecting a second map airport shows their all-weekday, 24-hour late-arrival profiles side by side in the existing full-width supporting section. The profiles share one rate axis and show count/sparse cues. The two required coordination pairs and original combined hourly chart remain available; Clear comparison restores the latter. The prior frontend version is saved under `docs/revisions/pre_airport_comparison_2026-11-07/`.

Build an individual university data visualization project answering: **How do departure time, airport, and airline interact to influence flight reliability?** The audience is a curious traveler or student exploring historical associations, not seeking a prediction for a particular flight. The exploration path is geographic overview → local scheduling pattern → carrier comparison within that context.

Core: three interactive views, two independent selection relationships, a real HTTP backend, reproducible data processing, and all submission artifacts. Historical reliability is not live flight tracking. No causal claims or findings before analysis. Cancellation statistics remain visible alongside late-arrival statistics so completed-flight performance does not conceal cancellations.

## Assignment reconciliation

The original repository contained only the assignment text in PROJECT_SPEC.MD and Git metadata. That text is preserved verbatim in [ASSIGNMENT_REQUIREMENTS.md](ASSIGNMENT_REQUIREMENTS.md); this document replaces its former role as the project specification.

| Requirement | Points | Planned evidence |
| --- | --- | --- |
| Three distinct interactive views | 7 | Map, hour × weekday heatmap, airline bars; titles, labels, legends, captions, tooltips |
| Two genuinely distinct cross-view pairs | 8 | Airport selection → heatmap; heatmap cell selection → airline bars; independently demonstrated and tested |
| Full stack | 4 | FastAPI HTTP responses fetched by React; fresh-start README |
| PDF report | 3 | Approximately 600–1200 words covering required sections |
| Narrated demo | 3 | Target 4–6 minutes, 1080p, user's own voice |
| Declared advanced features | Up to +3 | Optional historical-hour animation; labelled Extra Credit Features report section |

The summary is accurate, with these additions/clarifications from the actual instructions:
- Due Sunday, November 8 at 11:55 p.m. The copied assignment has a 2026 copyright and the weekday aligns with 2026; confirm the course deadline/timezone in the LMS. Plan against November 8, 2026, America/New_York provisionally.
- Four submission items: LastName_FirstName_A2.zip, LastName_FirstName_A2_demo.mp4 (or unlisted video URL in links file), LastName_FirstName_A2_links.txt, and LastName_FirstName_A2_report.pdf. The links file is still required for localhost.
- Localhost is accepted without penalty. Public deployment is optional and not on the critical path.
- ZIP must separate frontend/backend, include data or acquisition script plus sample, and contain exact install/start instructions and ports. Exclude dependencies, environments, and credentials.
- Include the design sketch as development evidence. The report needs design alternatives, both coordination pairs, architecture, sources, hours/process, and AI disclosure because AI is being used.
- Video should name the student and assignment at the start, demonstrate every implemented feature, and narrate evidence-based exploration and a limitation.
- Four to six minutes is a recommended target, not a strict duration stated as mandatory by the assignment.
- Bonus is conservative, not guaranteed; an undeclared bonus feature earns nothing. A linked map alone is not a reason to assume bonus points.
- AI help is permitted with disclosure; the student must understand, own, and review design, code, and writing.

## Proposed architecture

Use React + TypeScript + Vite, FastAPI, pandas preprocessing, and Parquet via pyarrow. Use reusable D3 JavaScript modules for all three SVG charts, first previewed in Jupyter and later imported by thin React wrappers. React owns the app shell and shared state; each D3 module owns the descendants of its isolated chart container, including marks and brushes. Modules receive plain data and callbacks and support updates and cleanup. Avoid two systems mutating the same DOM nodes. No Redux, database service, authentication, or paid services.

D3 is recommended for precise heatmap selection and coordinated SVG views. Plotly is a viable alternative, but custom selection semantics and one rendering model favor D3 here. pandas suffices for a limited period using selected columns and monthly/chunked processing; introduce DuckDB only if measured memory or runtime warrants an approved architectural change. Lock dependency versions when implementation begins.

Project structure (M1–M4 data tooling, notebook, API, chart wrappers and selection state now exist; playback remains planned):
- notebooks/dashboard_preview.ipynb; docs/visual_review.md; docs/figures/
- frontend/src/charts/{airportMap,departureHeatmap,airlineBars,hourlyOverview}.js (shared notebook/app source)
- frontend/src/components/{AirportMap,DepartureHeatmap,AirlineBarChart,SelectionSummary,HourPlayback}.tsx
- frontend/src/{api,types,selection,metrics}.ts; frontend/src/App.tsx
- backend/app/{main,schemas,data_service}.py; backend/tests/
- scripts/{download_data,prepare_data}.py; tests/data/
- data/{raw,processed,sample}/ and data/manifest.json
- docs/{data_audit,design,verification,report,demo_outline}.md
- README.md, frontend dependency lockfile, backend pinned dependencies

Prepare counts grouped by origin airport, reporting carrier, weekday, and scheduled local departure hour for a fixed published period. Retain numerator/denominator counts, not just percentages. Keep cleaned row-level data offline for audit. Load processed data once during FastAPI lifespan, not per request. API returns aggregate data only, never millions of raw flight rows.

Proposed API contract:
- GET /api/health: startup/readiness status and data version.
- GET /api/metadata: dates, source manifest/version, metric definitions, coverage, airport/carrier labels, quality exclusions.
- GET /api/airports: all-origin counts/rates and coordinates; optionally hour=0..23 for bonus, or a compact 24-frame response.
- GET /api/context?origin_id=<id>: count cube for one origin; omitted origin means server-aggregated all-origin context. Dimensions: carrier, weekday, hour. Includes airport context, period, version, and quality counts.
- GET /api/airport-hours: one versioned 24-frame response of origin/hour count rows for M6. The browser joins stable airport labels/coordinates and fills absent airport/hour rows with zero counts. It fetches once, never on each tick.
- Each aggregate carries scheduled_count, cancelled_count, cancellation_eligible_count, late_count, arrival_eligible_count, and excluded/missing counts. Rates are fractions or null, consistently documented; UI displays percent.
- Invalid filters: 422; valid empty context: 200 with empty data and totals; absent/corrupt processed data: explicit startup failure. No NaN/Infinity JSON.

The backend performs coarse filtering/aggregation; the browser sums context counts for heatmap and selected-cell airline totals. Cache context by origin/data version. Cancel or ignore stale fetches when airport selection changes. Show loading/error/retry/empty states. Initial targets: context payload under 1 MB uncompressed, cached selection response under 100 ms, local coarse request under 500 ms on the student's machine. These are targets to measure, not existing results. If exceeded, compact aggregates before considering additional services.

## D3 chart implementation and visual review before app integration

November 5 visual-review addition and clarification: the student proposed a fourth main dashboard view that overlays scheduled-flight-share bars and an arrival-late-rate line in **one plotting area**, sharing the local-hour axis. The bars use the labelled left percentage axis; the line uses the labelled right percentage axis. The earlier two-panel preview misunderstood the request and was replaced. The reviewed D3 view is now mounted in M3; airport selection can supply its context alongside the heatmap in M4. The map → heatmap and heatmap → airline relationships remain the two required independent pairs. This original design proposal did not itself authorize API/React work; those milestones were approved separately.

Latest user clarification: the notebook must be a complete, readable raw-to-chart analysis. It reads the local July–September ZIPs, reports missing/invalid counts and examples for each month, shows the chosen removals and population changes, joins airport coordinates, builds summaries and explores patterns. It no longer needs historical processed tables as a baseline. D3 renders the three reusable dashboard previews and one hover-enabled named-airport exploration; Matplotlib renders simpler exploratory figures. Design diagrams remain proposals, not data-derived findings. These notebook changes do not authorize M2.

Before M2, complete chart and diagram design and obtain user approval in M1.6. Use one Jupyter notebook that processes the raw files into summaries for the airport map, hour/weekday heatmap and airline bars, including filtered, sparse/empty cases and static hourly map frames. Include the dashboard layout, coordination, architecture and optional playback sketches. Review encodings, labels, legends, tooltips and selection indicators together. Build the reusable dashboard D3 charts in M1.6 and display them through notebook HTML/JavaScript outputs. Keep those chart modules outside notebook cells so the later app can reuse their source. Use simple Matplotlib plots for notebook-only exploration, with D3 retained where airport hover details help. Avoid a generic chart framework or a second Python version of the three dashboard charts.

November 5 revision: the user wants executable raw processing and editable cleaning choices in the notebook, not only prepared-data previews. Read existing raw ZIPs without downloading; show per-month inspection, conversion, two approved flight-row removals and the one unusable coordinate-reference removal, then summarize the contiguous U.S./Alaska/Hawaii origin population. Retain cancelled and diverted flights for disruption analysis and explicitly filter the eligible-arrival population. Preserve raw inputs, active configuration and historical M1 outputs. Verify clean-kernel execution and actual JavaScript rendering, record the visual inventory and wait for explicit visual approval before M2. The full decision history is in docs/design_decisions.md and docs/notebook_review_notes.md.

After the user's authorization, M2 built the API and React shell. The user then authorized M3, which mounted the reviewed D3 modules through thin React wrappers and supplies all-origin API responses. The user authorized M4, which added the two cross-view links, exact time tuples, clear/reset controls, context caching and stale-response protection. Later milestones reuse the chart source and design package without rebuilding charts. Material visual departures return to the user for review. Optional animation still requires M6 approval; approving its storyboard does not authorize implementation.

Notebook previews do not establish browser performance, brushing correctness in D3, accessibility or animation behavior. The full-stack HTTP API and both live cross-view relationships remain mandatory and are verified in the existing web milestones.

## Data sources, validation, and reproducibility

Use only these two free analytical sources:
1. [BTS Reporting Carrier On-Time Performance](https://transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ).
2. [BTS airport coordinate reference](https://transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=N8vn6v10+f722146+gnoyr_VQ=FLL).

M1 evidence: both official sources were validated for July-September 2025. Flight headers match the selected names below. AirportName is DISPLAY_AIRPORT_NAME and AirportEndDate is AIRPORT_THRU_DATE in the reference export. See docs/data_audit_2025_q3.md, data/manifest.json and docs/feasibility/2025-q3/quality_report.json for actual schemas, quality and provenance.

Target **July-September 2025**, using all qualifying reporting-carrier flights rather than a random sample. This bounded historical quarter does not describe year-round reliability or establish weather causation. Architecture and features remain unchanged.

The historical M1 scope contains 1,796,245 scheduled records, 348 origins and 14 reporting carriers. The M2 dashboard data under `data/processed/2025-q3/dashboard/` applies the reviewed notebook cleaning and geography: 1,785,449 scheduled flights and 340 origins. Current reports are docs/data_audit_2025_q3.md, docs/dashboard_feasibility_2025_q3.md and docs/design.md. data/active_dataset.json identifies the quarter. The user authorized M2, M3 and M4; M5 and later milestones remain separate approval gates.

Candidate flight fields: FlightDate, DayOfWeek, Reporting_Airline (or documented reporting-carrier identifier), OriginAirportID, OriginAirportSeqID, Origin, destination identifiers for quality checks, CRSDepTime, ArrDelay, ArrDel15, Cancelled, Diverted, and flight number for duplicate diagnostics. Do not conflate reporting carrier with marketing carrier. Carrier codes are sufficient if official full names are unavailable from these sources; no invented label mappings.

Candidate coordinate fields to inspect: airport ID/sequence ID, airport code/name, latitude/longitude, and effective dates or historical status. Prefer exact origin sequence-ID joins if supported. Otherwise use stable airport ID with documented effective-date matching. Never assume IATA codes are unique or take an arbitrary first historical row. Verify many-to-one cardinality and unchanged flight row/count totals after joining. Reject ambiguous coordinate matches until resolved; retain unmatched flights in non-map aggregates and disclose unmapped volume. Validate coordinates numerically and geographically; zeroes are not automatically valid locations.

Pipeline requirements:
1. Record source URLs, retrieval date, period, exact selected fields, file sizes, SHA-256 hashes, acquisition method and schema mapping. Do not overwrite raw inputs.
2. Provide scripted download where supported; if BTS interactive access blocks automation, document exact manual acquisition and ship the permitted input data or a reliable acquisition path plus sample. Do not claim a manual-only path satisfies a promised automated download script.
3. Normalize actual headers explicitly; fail on missing required fields. Parse dates, identifiers and flags with nullable types. Check dates against requested months and weekday agreement.
4. Validate HHMM strings/numbers, minutes 00–59, hours 00–23. Historical M1 data quarantined one `2400` row (July 24, OO 6512, DSM–ORD), retaining it in map totals but excluding it from hour views. The reviewed notebook and M2 dashboard data remove that row from their working analysis population after showing the evidence. Do not assume a date rollover rule; report any other invalid times and their treatment.
5. Audit exact duplicates and candidate flight identity collisions. Do not drop flights simply because origin/carrier/date/time matches. Document confirmed duplicate policy and counts.
6. Audit missingness, flag values, delay threshold agreement, diversion/cancellation overlap, coordinate joins, and excluded counts. Write a reconciliation from raw to analysis outputs.
7. Produce sorted deterministic aggregates and a machine-readable quality summary; rerunning identical inputs/config must yield identical counts. Keep a small real-data sample with provenance and separate clearly synthetic test fixtures.

## Metric definitions

- Scheduled count: all retained reporting-carrier flight records within the declared period/scope, including cancelled and diverted flights. Coverage is the BTS reporting dataset, not all possible US aviation.
- Arrival-eligible: Cancelled=0, Diverted=0, and a valid observed arrival-delay classification. Prefer valid ArrDel15 and cross-check ArrDelay>=15 when both exist; use ArrDelay to derive missing ArrDel15 only with a documented rule. Contradictions are audited and excluded pending resolution, never silently overridden.
- Late-arrival rate: late_count / arrival_eligible_count; late means arrival delay >=15 minutes. A missing delay is not on time. A zero denominator yields null/“No eligible arrivals,” not 0%.
- Cancellation rate: cancelled_count / scheduled_count when cancellation flags are fully known. If unknown flags exist, retain scheduled counts, display coverage, and return null for the full-scope cancellation rate; an explicitly labelled known-status rate may additionally use cancellation_eligible_count. Do not quietly change the denominator.
- Missing diversion/cancellation status cannot qualify for arrival eligibility. Diverted flights stay in scheduled/cancellation denominators but not the late-arrival denominator.
- Rates over combined groups are sums of numerators divided by sums of denominators, never averages of percentages.
- Time is scheduled local departure time at each origin. The same hour across airports is not the same UTC instant. The historical M1 map retained its one invalid-time row; the reviewed notebook and M2 dashboard data remove it from all working totals. Keep these versions distinct when reconciling counts.
- Proposed low-sample indicator: fewer than 30 eligible arrivals. This is a presentation caution, not a statistical guarantee. Show counts and a distinct outline/pattern; retain data, with exact statistics in tooltips. Avoid definitive best/worst claims for sparse groups.

## Views and selection contract

| View | Question and encoding | In-view interaction |
| --- | --- | --- |
| Airport map | Where do departure origins differ in arrival reliability? Position by coordinates, color by late-arrival rate, circle area by scheduled volume | Hover/focus details; select/toggle airport |
| Heatmap | At this origin, which scheduled hours and weekdays differ? 24 hours × 7 weekday rows, color by late-arrival rate | Hover/focus details, click selection, rectangular brush |
| Airline bars | Within this origin/time context, how do reporting carriers compare? Horizontal bar length is late-arrival percent; eligible n displayed | Hover/focus details and row highlight |

Every view has a descriptive title, units/legend where applicable, period/context caption, empty state, and counts plus late-arrival, cancellation and diversion rates in hover/focus details. Diversion rate is diverted flights divided by scheduled flights; it is unavailable when there are no scheduled flights. Map coordinates take the place of chart axes; provide a geographic caption and size/color legends. Map, heatmap and airline bars share one smooth Viridis late-rate scale from 0% to a labelled 50%+ cap. Values at or above 50% share the final color, while exact rates remain available in the detail tooltip. The airline bar-length axis remains fixed at 0–100%. Null is a separate neutral style. Heatmap cells and airline rows transition over 300 ms on manual filter changes, except under reduced motion. Use stable carrier order (code/name) during playback to preserve tracking.
The fourth all-hour context chart uses pale teal for scheduled-flight-share bars and strong teal for the arrival-late-rate line. These match the page accent and separate the two measures; the line's vertical position, not its color, encodes the rate. Both percentage axes and legend labels remain explicit. The local heatmap clear button uses the teal control color while pink marks selections and focus.
For the current wide-screen layout, give the map the left column and stack the heatmap and airline bars on the right. The contiguous-U.S. map uses the full map width, with Alaska and Hawaii insets beneath it. Place the heatmap question beside its view heading and use the airline view heading without a repeated chart question. Make this three-chart section one viewport tall so it can be viewed together after scrolling past the compact page introduction. Put the full-width all-hour context below it. Fit complete charts and legends inside their cards without internal scrolling on desktop; retain the stacked order and horizontal chart scrolling at narrow widths. The immediately prior frontend files are saved in `docs/revisions/pre_insets_below_2026-11-07/` for restoration.

Map MVP: a projected coordinate point map with geographic graticule, suitable labels, and explicit Alaska/Hawaii/territory treatment. No additional analytical source is necessary. A licensed static boundary basemap is optional; if used, record its source/license as a third supporting asset and confirm it fits the two-source preference. Do not silently omit out-of-projection airports. No route overlays in the planned release.

One shared state: selectedOriginId (null means all), selectedCells (set of weekday/hour pairs; empty means no time filter), animationHour (null means off), isPlaying. Cells are exact tuples: selecting Monday 08:00 and Friday 17:00 must not also select Monday 17:00 or Friday 08:00.

| Action | Map | Heatmap | Airline bars |
| --- | --- | --- | --- |
| Select airport (A) | Keep overview and mark selected airport | Reaggregate to origin; retain time selection | Reaggregate to origin and current selected cells |
| Select/brush heatmap (B) | Keep geographic overview | Keep all context cells and outline selected cells | Reaggregate to union of selected tuples at selected origin |
| Clear airport | Clear highlight | All-origin context, retain selected cells | All origins within selected cells |
| Clear time selection | Unchanged | Clear outlines | All valid times at selected origin |
| Reset all | Restore baseline | Restore baseline | Restore baseline |

A and B have different source views and filtering dimensions. A updating both dependent charts still counts as only one pair. Heatmap selection does not filter away the heatmap itself, preserving context. Map intentionally remains an overview during B; chart titles and the current-selection summary show each view's scope. Click toggles a cell and brush replaces with a rectangular set. Global Clear time and Reset all clear clicked or brushed selections in one action. Pink hover/focus and selection outlines stay distinct from the Viridis data colors. Keyboard-accessible cell and airport selection provide alternatives to dragging. Airport changes retain time selection visibly even if the new context is empty. No airline-driven filtering is required.

## Bonus animation (only after core acceptance)

Animate historical local departure hour 00–23 with play/pause and slider, around one frame per second with roughly 300 ms interpolation. Start playback begins playing immediately at 00:00. Playback stops on 23:00; a short Replay button starts again at 00:00. Under reduced motion, entering the mode shows the slider without automatic playback. Fixed color/size scales, stable airport IDs and explicit hour label. Map frames show all-origin airports for that hour; heatmap keeps full context and highlights the active column; bars use selected origin and active hour across weekdays. Entering playback temporarily suspends the manual cell filter and clearly displays this state; leaving playback restores it. Editing heatmap selection exits playback first. Airport changes preserve active hour but pause while the new context loads. Reset stops playback and clears all filters. Prefetch/cache 24 compact map frames; no request on every animation tick. Late/stale results must never overwrite a newer state.

The slider is an ordered hour-of-day profile over the fixed period, not a chronological day or moving-flight simulation. Validate a frame against the equivalent manual all-weekdays hour selection. Document the feature's exploration value and technical work in the report; request no assumption of awarded bonus.

## Risks, open decisions, and exclusions

- BTS acquisition and historical sequence joins passed M1. Future source updates may change the reference or form; preserve raw ZIPs and hashes for exact reproduction.
- Deadline and available work hours need confirmation. Proposed effort is 19–29 focused hours including optional animation and submission preparation; reduce optional work if unavailable.
- Need student's submission name, approved final period, and deadline/timezone before packaging. No need to block planning on these.
- All selected flights match historical coordinates within the reference validity intervals. No alternate source or join is needed for this scope.
- Geography and carrier labels depend on actual data. Preserve coverage information rather than hiding omissions.
- Rankings confound route mix, weather, season, and schedule. No causal estimates, prediction model, or unsupported recommendation to travelers.
- No auth, routing analysis, live data, weather joins, extra dashboard views, date picker, or deployment automation in core scope.
- Fine-grained origin/carrier/weekday/hour groups are often sparse even across three months. Retain sample-size indicators and avoid interpreting those cells as precise carrier comparisons. UI latency still requires measurement during implementation.

## Technical references consulted

- [D3 brushing](https://d3js.org/d3-brush): SVG brushing support; React state integration is our design choice.
- [D3 geographic tools](https://d3js.org/d3-geo): geographic projections for airport positions.
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/): startup/shutdown data-loading lifecycle.
- BTS source links above: actual downloaded schemas are recorded in docs/feasibility/2025-q3/quality_report.json.

See PLAN.md for approval-gated milestones and PROGRESS.md for evidence and status.
