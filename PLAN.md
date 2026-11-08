# FlightWise — Milestone Plan

Status: M1 and M1.5 are complete for July-September 2025. The user accepted M1.6, accepted M4 and authorized M2–M6. M2–M6 are implemented and locally verified. Later user-approved refinements aligned the three rate color encodings, added short filter transitions, and made the supporting all-hour chart visually quieter. After professor feedback, the current desktop layout focuses on the three linked views above a full-width all-hour chart, with the mainland map above Alaska and Hawaii insets. A later user request removed the local heatmap clear control; global Clear time remains. Saved rollbacks cover the November 7 layout revisions. M7–M8 remain unapproved. See docs/design_decisions.md for the design history. Work on one approved milestone at a time.

November 5 visual-review addition: the user proposed a combined chart with scheduled-flight-share bars and an arrival-late-rate line overlaid in one local-hour plot. The initial two-panel interpretation was corrected. M1.6 includes the revised reusable D3 preview. M3 now mounts this and the other three reviewed D3 modules in React. The two required independent selection pairs remain M4 work.

Approved scope: **July-September 2025**. Keep the eight main milestones and the focused M1.6 D3/notebook checkpoint before API/app integration. Production architecture remains React + TypeScript + D3.js and FastAPI. The reviewed hourly view is mounted alongside the original three views; linked interactions and optional features retain their separate milestone gates. Obsolete quarter data and reports were removed after verification with explicit user authorization.

The grading priority is coordinated views (15 points), a reliable full stack (4), then complete report/video (6). Reserve submission time before spending time on the optional bonus. The original overall estimate was 19–29 focused hours. M1.6 now brings chart implementation forward from M3; its work is not an additional Python plotting pass. Notebook setup and user revisions add effort, while M3 becomes integration. Earlier 1–2-hour preview and 3–4-hour M3 estimates no longer describe this split; remaining time must be reassessed when implementation begins.

## M1 — Establish data feasibility and freeze definitions (3–4 hours)

**Objective:** Prove the two sources can support correct, reproducible analysis. This is the single best first implementation milestone.

**Tasks:** Obtain July–September 2025 reporting-carrier data and airport reference; inspect actual headers and historical fields; record hashes and acquisition steps; implement schema normalization, nullable flags and time parsing; audit missingness/duplicates and many-to-one joins; calculate count-based aggregates. Assess the quarter using measured cost rather than assumed scale. Produce exploratory counts/ranges without claiming causal findings. Review useful display scales and geographic coverage from real data. Use the verified current-quarter tools and evidence.

**Deliverables:** `scripts/download_data.py` if automation is feasible, `scripts/prepare_data.py`, `data/manifest.json`, raw inputs excluded from Git as appropriate, `data/processed/2025-q3/` aggregates, a small provenance-labelled real sample, `docs/data_audit_2025_q3.md`, metric fixtures/tests under `tests/data/`, dependency specification, `.gitignore`, and acquisition/reproduction instructions in `README.md`.

**Dependencies:** User approval of M1 and proposed metric rules.

**Acceptance:** Actual schemas recorded; required fields exist or approved alternatives are documented; joins do not multiply records; ambiguous matches and exclusions are quantified; numerator/denominator rules reconcile with raw records; zero denominator stays null; dataset period and geographic coverage are explicit. Final release period proposed for user approval. A failed acquisition is reported with a concrete alternative, not fabricated data.

**Verification:** Run preprocessing twice on identical inputs and compare sorted counts/output hashes where deterministic. Fixtures cover 14/15-minute threshold, cancellation/diversion, missing flags/delays, contradictory delay fields, HHMM/2400, exact duplicates versus flight-identity collisions, historical coordinate duplicates, unmatched airports, and weighted rates. Hand-check a small sample against source rows. Record row counts, join cardinality, runtime, peak memory where measurable, and aggregate size. Include a known unequal-denominator example that fails if percentages are averaged.

## M1.6 — Build reusable D3 charts and approve all visuals in Jupyter

**Objective:** Build the actual D3 charts, complete visual design and obtain user approval in one milestone before API/app integration. M1.5 established computational feasibility; M1.6 owns reusable chart implementation and approval of all planned charts and diagrams.

**Latest notebook clarification:** The notebook reads local raw ZIPs and visibly inspects, cleans, joins, summarizes and explores all three months. It shows per-month issue counts, affected rows, reasons for removals, separate eligible arrivals and reconciled totals. It stands on its own without comparing to older processed M1 files. Main dashboard previews use reusable D3 source; ordinary exploratory plots use Matplotlib, with a D3 named-airport comparison for hover details. The milestone sequence is unchanged.

**Tasks:** Create reusable D3 modules for the airport map, complete 24×7 heatmap and airline bars. Display the same modules in one Jupyter notebook using summaries calculated there from July–September raw ZIPs. Keep dashboard rendering code outside notebook cells and independent of data fetching. Provide editable airport and exact weekday/hour selections with filtered, sparse, empty and no-eligible examples. Include static hourly map states. Distinguish missing rates from 0%, show supporting counts in hover/focus details, and use verified full reporting-airline names. Scope the preview to contiguous U.S., Alaska and Hawaii origins, reporting territory-origin exclusions. Add notebook exploration of cancellations, diversions and late arrivals. Full app coordination remains M4.

**Design coverage:** Review titles, axes, scales, colors, legends, mark sizes, ordering, sample-size warnings, tooltip/focus content and selection indicators for every chart. Include dashboard layout, labelled coordination arrows for both relationships, and the existing frontend/API/data-flow architecture diagram. Preview loading/error/empty states as sketches where actual data cannot represent them. Include optional hourly-map snapshots and a playback-control storyboard for design review; animation implementation remains optional M6. The notebook and review notes form one review package, not separate design milestones.

**Deliverables:** Reusable modules under `frontend/src/charts/` (airport map, departure heatmap, airline bars and proposed combined hourly chart); `notebooks/dashboard_preview.ipynb` displaying those modules and executing the raw-processing workflow; `docs/visual_review.md` with the chart/diagram inventory; exported figures/diagrams under `docs/figures/`; README instructions and pinned dependencies. The user accepted the current package to begin M2 and may request later refinements.

**Dependencies and November 5 scope update:** Completed M1/M1.5 and local July–September raw data. The user authorized a readable raw-data workflow inside the notebook. It removes one invalid-time flight and one unexplained missing-arrival flight from working flight data, plus one coordinate-less row from the working airport reference, after showing evidence and counts. Cancelled and diverted flights remain available for disruption statistics. The notebook does not download data or overwrite verified M1 outputs. Reusable dashboard chart code remains outside the notebook; FastAPI and React scaffolding remain outside M1.6.

**Acceptance:** All three chart types are visibly rendered and understandable without reading the code. Major/smaller-airport and time-selection examples reveal the expected filtered views with explicit n and empty/sparse states. Geographic coverage and volume/color legends are clear; hourly snapshots keep comparable scales. The notebook runs from a clean kernel without hidden state and does not modify source data. All planned charts and diagrams have been reviewed, requested revisions incorporated, and user approval explicitly recorded before M2 begins. Stop after presenting the review package and wait for that approval. Notebook completion alone does not constitute user approval. The reusable chart source carries forward into the app; the notebook is supporting design evidence and does not replace the assignment's HTTP backend, interactive D3 views, or demonstration video.

**Verification:** Restart kernel and run every cell from raw ZIPs; reconcile source, removed, geographic-scope and eligible-arrival rows. Inspect actual D3 rendering in the documented notebook viewer; Python execution alone does not prove JavaScript rendered. Check map outlines, airline names and ordering, keyboard details, and null/zero and sparse/empty distinctions. Document protected-input preservation and expected differences from historical M1 totals caused by the new cleaning and scope. HTTP interactions and animation remain later checks.

## M2 — Build the API and application foundation (3–4 hours)

**Objective:** Establish the data API and a runnable React shell for the already approved visual designs.

**Tasks:** Add React/TypeScript/Vite and FastAPI scaffolding while preserving M1.6 chart modules; pin dependencies; load processed data once with lifespan; implement health, metadata, airport and `/api/context` endpoints and shared response types. Prove React can fetch real aggregates over HTTP with a simple count/status display. Implement the API client and request failure handling. Reference the approved M1.6 diagrams in implementation notes. Document ports 5173/8000, API base configuration and local CORS. Mounting existing charts into the app belongs to M3.

**Deliverables:** `backend/app/{main,schemas,data_service}.py`, API contract tests, `frontend/src/{App,api,types}` modules, package/lockfiles, `docs/design.md` referencing the approved design package, runnable README commands.

**Dependencies:** M1 accepted, M1.5 complete, all M1.6 charts and diagrams explicitly approved by the user, and M2 approved. Before serving data, regenerate the production prepared aggregates under the approved cleaning and geographic scope; the historical M1 files still contain the former all-origin counts and must not be silently served as if they matched the revised notebook.

**Acceptance:** React displays a real count fetched over HTTP from the backend; all core endpoints support the approved views; startup does not reread raw CSV per request; responses include counts, null-safe rates, period and version. No flight arrays are hard-coded into the application. Student can explain the architecture.

**Verification:** Start both halves using README; inspect network responses and compare representative airport/context counts to existing feasibility evidence. Run API contract/serialization tests for valid/invalid filters, empty results and null rates, plus TypeScript/build checks. Stop backend and verify visible retryable failure. Check startup failure for missing processed inputs. Do not repeat M1 schema/join validation unless a discrepancy appears.

## M3 — Integrate the approved D3 charts with React and the API

**Objective:** Reuse the approved M1.6 chart source in the dashboard and supply M2 API data. No second chart implementation is required.

**Tasks:** Add thin React wrappers that mount, update and clean up the existing D3 chart modules in isolated containers. Pass typed airport/context API data into those modules, with only small data-shape adapters where needed. Assemble the approved layout and wire real loading/error/retry/empty states. Preserve the existing encodings, legends, captions, tooltips and sparse-data rules. Verify representative contexts from the API and responsive sizing; live cross-view selection wiring belongs to M4. Do not copy or rewrite chart rendering logic. Material visual departures require user review.

**Deliverables:** Thin `AirportMap.tsx`, `DepartureHeatmap.tsx` and `AirlineBarChart.tsx` wrappers importing the M1.6 modules; API-to-chart integration; relevant frontend tests; web screenshots compared with approved notebook figures.

**Dependencies:** M1.6 approved visual package, M2 accepted with core API endpoints available; M3 approved.

**Acceptance:** Three distinct views each answer their stated question, display scope/period, and provide in-view interaction. Every bar/cell can expose its numerator and denominator. Counts reconcile after accounting for documented invalid-time exclusions; airline totals are weighted correctly. No-data cells look different from 0% late cells.

**Verification:** Compare web renderings with approved notebook figures for the same contexts, and compare displayed counts to existing feasibility evidence. Test missing cells, sparse carriers, documented time exclusions and zero denominators. Check geographic coverage, labels/tooltips at demo resolution and narrow viewport. Run relevant frontend tests and build; rerun API tests if API code changes. Reopen data validation only if a discrepancy is discovered.

## M4 — Implement and prove both selection relationships (3–4 hours)

**Objective:** Implement and verify the two distinct, reversible relationships already approved in the M1.6 coordination diagram.

**Tasks:** Add shared selection reducer/state and visible chips/counts; implement map airport selection → heatmap context (A), heatmap click/rectangular brush → airline aggregate (B). Implement reset/clear and keyboard alternatives. Keep exact weekday/hour tuples, preserve heatmap overview, and retain time selections on airport changes. Cache coarse contexts; abort/ignore stale responses. Document what each view intentionally filters or preserves.

**Deliverables:** `frontend/src/selection.ts`, `SelectionSummary.tsx`, updated three view components, reducer/aggregation tests and browser integration tests (Playwright or equivalent), `docs/verification.md` interaction matrix.

**Dependencies:** M3 accepted; M4 approved and implemented. See `docs/verification.md` for actual M4 checks.

**Acceptance:** A alone visibly changes the heatmap correctly; B alone changes airline bars while origin remains fixed. Both together apply the intersection of origin and union of selected tuples. Selection is obvious, reversible and responsive. One airport selection feeding two charts is never counted as two pairs. No stale airport response can replace a newer selection.

**Verification:** On deterministic fixtures and real data: select airport, select cell, brush rectangle, toggle cells, clear each filter, reset, select everything, choose an empty combination, and rapidly switch airports. Explicitly test two disjoint tuples to detect accidental Cartesian-product filtering. Compare all resulting airline counts against independently filtered rows. Measure cached interaction latency and verify no per-pointer-move request storm. Save evidence for the demo.

## M5 — Harden and accept the core dashboard (2–3 hours)

**Objective:** Make the full 19-point application component reliable and usable before bonus work.

**Tasks:** Review layout, legends, scope captions, focus/keyboard behavior, color/low-sample/null distinction, tooltip edges, request failures, browser console and largest context. Profile payload and latency targets from the specification. Ask a peer to explore without coaching if available, and record feedback. Draft report outline and demo sequence now; select only findings reproducible in dashboard states. Test installation/start instructions in a clean copy/environment.

**Deliverables:** Polished views, verified README, `docs/verification.md` with measured results and limitations, report outline, demo outline, development/AI-use log updates.

**Dependencies:** M4 accepted; M5 approved and locally verified. See `docs/verification.md` for measured results and limitations.

**Acceptance:** Both coordination pairs pass independently and together; all three views have complete legends/captions/details; fresh-start procedure works; empty/error cases are intelligible; no known blocking bugs. Remaining time for report and video is reserved before deciding whether to start M6.

**Verification:** Run meaningful data/API/selection tests, TypeScript/build checks and browser interaction suite. Manually check keyboard operation and 1080p legibility, stale fetch handling, context payload size and response latency. Record any target misses honestly. A failed check blocks core acceptance until fixed or the limitation is explicitly reviewed.

## M6 — Add historical-hour animation (optional, 2–3 hours)

**Objective:** Provide a clear advanced interaction eligible for bonus consideration.

**Tasks:** Add compact 24-hour airport frames and prefetch/cache; add play/pause, slider, active-hour label, fixed scales and stable transitions. Highlight heatmap column and update carrier bars for the active hour. Implement the specified manual-filter suspension/restoration behavior, pause-on-context-load, reduced motion, and reset/exit cleanup. Explain that each frame pools local scheduled hours over the selected historical period.

**Deliverables:** `HourPlayback.tsx`, animation state/API changes, frame-equivalence and lifecycle tests, updated README, `Extra Credit Features` report draft and demo segment.

**Dependencies:** The user accepted the M5 result and explicitly authorized M6. M6 is implemented and locally verified; see `docs/verification.md`.

**Acceptance:** Play/pause/slider work; no timer leaks or stale updates; all 24 hours are labelled correctly; empty hours do not retain stale marks; normal selection restores correctly. No bonus points are claimed as guaranteed.

**Verification:** Compare hour-frame totals with equivalent manual all-weekdays hour selections. Exercise start/pause/seek/airport change/heatmap edit/exit/reset repeatedly. Test reduced motion and component unmount. Confirm fixed legends and absence of a request per tick. Re-run the two core selection scenarios after exiting playback.

## M7 — Produce the report and narrated demo (2–4 hours)

**Objective:** Deliver the six points of explanation and demonstration with honest evidence.

**Tasks:** Student reviews and authors final rationale/findings. Assemble approximately 600–1200 words: dataset/question, design alternatives, both pairs and exploration logic, architecture, sources, process/hours, limitations and AI disclosure. Include sketch and useful screenshots. Add a clearly labelled Extra Credit Features section only for implemented features. Rehearse and record 4–6 minutes at 1080p with student's own narration; name/assignment at start, A and B separately, combined exploration, resets, findings, limitations, and any animation.

**Deliverables:** `docs/report.md` (or editable equivalent), `docs/demo_outline.md`, `LastName_FirstName_A2_report.pdf`, `LastName_FirstName_A2_demo.mp4` or an accessible unlisted video link. Actual student name is needed by this stage.

**Dependencies:** M5 accepted; M6 accepted or deliberately skipped; M7 approved. Capture final evidence only after the demonstrated UI is stable.

**Acceptance:** PDF opens and covers every required section; word count is in target range; no invented findings or hours; AI assistance is disclosed. Exported video is audible, legible, and demonstrates every implemented feature with actual interactions.

**Verification:** Count narrative words, open exported PDF, check screenshot labels and references. Watch the complete exported video and check resolution/audio/duration. Reproduce each reported finding in the dashboard. If hosted elsewhere, test link access without account privileges. The assistant cannot substitute synthetic narration for the user's required voice.

## M8 — Package and verify submission readiness (1–3 hours)

**Objective:** Produce all four correctly named artifacts that a grader can use.

**Tasks:** Freeze documented dataset and code version; choose localhost by default. Create ZIP excluding dependency directories, environments, caches and credentials. Include dataset if practical, otherwise working acquisition script plus real sample and clear full-data steps. Create links file with localhost statement and README start-command reference or tested public URL; include hosted video link if applicable. Unzip to a clean directory and follow README literally. Verify submission list against preserved assignment text. Public deployment is only attempted with separate approval and sufficient time; it does not replace a running backend.

**Deliverables:** `LastName_FirstName_A2.zip`, `LastName_FirstName_A2_links.txt`, final report/video from M7, final submission checklist and updated PROGRESS.md. Upload remains a user action unless explicitly authorized.

**Dependencies:** M7 accepted; M8 approved; submission name and deadline confirmed.

**Acceptance:** Four required submission items accounted for, correct names, readable report/playable video, reproducible complete application, no missing data instructions or secrets. Localhost status is explicit if used. Submission-ready is distinct from actually uploaded.

**Verification:** Inspect ZIP inventory; install and start both halves from extracted contents; exercise A and B and any bonus animation. Check all links and exact filenames. Verify acquisition works if full data is omitted. Record the successful commands/results and any remaining user submission actions.

## Deadline-oriented sequence and scope gates

The student later authorized a small optional two-airport comparison after M6. It is implemented as a mode of the existing full-width all-hour section, using a pinned airport plus the current map airport. The snapshot and restore instructions are in `docs/revisions/pre_airport_comparison_2026-11-07/RESTORE.md`; implementation and verification results are in `PROGRESS.md` and `docs/verification.md`. M7 report/video and M8 packaging remain separate approval gates. Any extra-credit claim requires the labelled report section and student review.

Provisional sequence, contingent on approval and availability: M1/M1.5 are complete; review M1.6 notebook previews before M2, then continue M2–M5. Reserve time for M7 and M8 before optional M6. The provisional submission deadline remains November 8 at 11:55 p.m.; the extra visual review should replace avoidable chart-design rework, and optional animation remains the first substantial feature to defer if time is tight. This is an aggressive schedule, not a promise.

If time tightens: omit route overlays (already excluded), public deployment, and M6 first; ask before reducing or changing the approved July–September period. Preserve three views, both distinct coordination relationships, real APIs, report and video. Do not sacrifice submission artifacts to chase bonus points. Before each milestone, confirm its approval from the conversation, read the project docs, then implement only its scope. At completion, report verification and update PROGRESS.md before requesting approval for the next milestone.
