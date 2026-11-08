# FlightWise

FlightWise is a tool for exploring historical U.S. flight reliability in terms of late arrival. It uses July–September 2025 BTS reporting-carrier flights and the BTS airport coordinate reference. The dashboard shows 340 origin airports and 14 reporting airlines. It is an exploration of past associations, not a live tracker or prediction. Future work can expand the data coverage to full year.

## Install once

- Python 3.13 (validated with 3.13.5)
- Node.js and npm (validated with Node 24.18.0 and npm 11.16.0)

In PowerShell, go to the project root and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix frontend ci
```

## Start the website

The prepared data is included, so no download or data build is needed to start the site. Open two terminals at the project root.

### Terminal 1: backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2: frontend

```powershell
npm --prefix frontend run dev
```

Open **http://127.0.0.1:5173/**.

This site runs on **localhost**; it is not publicly deployed.

## Dataset

The project includes the original July–September 2025 BTS ZIPs in `data/raw/` and prepared dashboard tables in `data/processed/2025-q3/dashboard/`. The backend loads the prepared tables at startup, so no download or data processing is needed to run the website.

## How the dashboard works

1. Airport map: circle area shows scheduled volume and color shows arrival-late rate. Choose an origin airport to update its departure-time context.
2. Weekday-by-hour heatmap: choose exact local scheduled-departure cells to filter the airline comparison.
3. Airline bars: compare reporting carriers within the selected airport and time cells.
4. All-hour context: compare scheduled-flight share and arrival-late rate across 24 local hours. An optional two-airport mode shows matching hourly profiles side by side.

The map, heatmap, and airline bars share a Viridis rate scale from 0% to 50%+. Hover or keyboard focus shows counts and exact rates. Selections are visible and reversible through Clear airport, Clear time, and Reset all. Historical-hour playback uses a slider and play/pause controls; it pools the same scheduled *local* hour across the quarter, rather than showing a live day or common UTC instant.

The API provides:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Readiness and data version |
| `GET /api/metadata` | Period, metric rules, coverage, and quality exclusions |
| `GET /api/airports` | All-origin airport counts, rates, and coordinates |
| `GET /api/context?origin_id=<id>` | Carrier, weekday, and hour counts for one airport; omit the ID for all origins |
| `GET /api/airport-hours` | The 24 count frames used by playback |

Arrival-late rate divides late arrivals by completed, non-diverted flights with known arrival status. Cancellation rate uses scheduled flights when cancellation status is known. Missing outcomes are never treated as on time, zero denominators produce null rates, and combined rates are calculated from summed counts.

