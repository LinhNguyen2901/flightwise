# Active data audit — July–September 2025

The active analysis period is **July-September 2025**. Architecture, charts, interactions, metric definitions and milestone sequence are unchanged. M2 remains pending approval.

## Data and processing results

The existing downloader acquired the three official BTS Reporting Carrier monthly archives for July, August and September. The existing historical airport reference was hash-verified and reused. `data/manifest.json` lists the three active flight archives and shared coordinate reference. No new analytical source was introduced.

| Month | Scheduled | Cancelled | Arrival-eligible | Late arrivals | Excluded arrival records |
| --- | ---: | ---: | ---: | ---: | ---: |
| July | 631,428 | 15,473 | 612,811 | 177,012 | 18,617 |
| August | 602,378 | 6,483 | 593,733 | 133,920 | 8,645 |
| September | 562,439 | 2,886 | 558,328 | 92,859 | 4,111 |
| Total | 1,796,245 | 24,842 | 1,764,872 | 403,791 | 31,373 |

The active scope contains **348 origins and 14 reporting carriers**. Overall late-arrival rate is 22.8793% of eligible arrivals; cancellation rate is 1.3830% of scheduled records. These are descriptive audit totals, not a causal explanation or a claim about all-year reliability.

All selected columns are present. Each month passed date/weekday checks and the existing historical airport join checks. There are no selected-field duplicates, candidate flight-identity collisions, delay-flag conflicts, cancellation/diversion overlaps, unknown cancellation/diversion flags or unmatched airport records. No flight row was dropped or multiplied by the coordinate join. Each used origin has one historical sequence in this quarter. The reference still includes one unused record (ZZZ) with missing coordinates; it does not affect the selected flights.

## One scheduled-time exclusion under the unchanged rule

July contains one `CRSDepTime=2400` record: July 24, 2025, reporting carrier OO, flight 6512, DSM–ORD, arrival delay 1,451 minutes, non-cancelled and non-diverted. The existing policy quarantines 2400 until its date/hour convention is confirmed. This switch does **not** change that rule.

Consequently:

- The map/all-scheduled totals retain all 1,796,245 records, including that eligible late arrival.
- The hour/weekday cube, time-based airline contexts and animation contain 1,796,244 scheduled records, 1,764,871 eligible arrivals and 403,790 late arrivals.
- The forthcoming UI must disclose “1 flight excluded from time-based views because scheduled departure time could not be assigned under the current rule.” Null is not hour zero, and the extra flight must not disappear from map totals.

There are no other invalid scheduled times. This is a documented coverage difference, not an arithmetic mismatch. Existing count reconciliation explicitly verifies it.

## Size, runtime and verification

The prepared count cube has 78,018 rows and is **438,005 bytes**. The first processing run took 28.442 seconds; the repeat took 44.456 seconds. The first run peaked at 769,650,688 bytes of process working set (about 734 MiB). Runtime varies with cache and concurrent checks; no preprocessing occurs per dashboard interaction.

Validation evidence is stored in [feasibility/2025-q3/](feasibility/2025-q3/):

- `quality_report.json`: actual schemas, missingness, joins, exclusions, source hashes and output hashes.
- `independent_verification.json`: direct source-CSV totals and three selected contexts, computed independently of preparation metric helpers.
- `migration_checks.json`: equality of six output Parquet hashes across both runs and historical preservation checks performed before the subsequent authorized cleanup.
- 25 tests passed, including period-label generation and refusal to overwrite another quarter's output or sample provenance. The original metric/join tests continue to pass.

The three raw flight ZIPs total 91,224,579 bytes. The 300-record real sample and used reference rows are isolated under `data/sample/2025-q3/`; obsolete samples have been removed. Sample rows are the first 100 source records per month and are not representative for estimating rates.

## Active paths

- Raw archives and shared airport reference: `data/raw/`.
- Prepared data: `data/processed/2025-q3/`.
- Sample/provenance: `data/sample/2025-q3/`.
- Verification evidence: `docs/feasibility/2025-q3/`.
- Reports: this audit and `docs/dashboard_feasibility_2025_q3.md`.

`data/active_dataset.json` selects the verified period and paths. Obsolete quarter data, reports and archived documents were subsequently removed with user authorization; the active data and analytical evidence were preserved.

## Conclusion

July–September is feasible with the same architecture. The [updated feasibility report](dashboard_feasibility_2025_q3.md) retains a **CONDITIONAL GO** because sparse selections and empty overnight states require the same display safeguards as before. The period change does not justify new causal claims, a season-comparison feature or any other feature expansion. M2 remains pending approval.
