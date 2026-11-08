# Restore the map-centered four-view layout

These three files are exact copies from before the November 7 three-view focus revision. From the repository root in PowerShell:

```powershell
Copy-Item -LiteralPath docs/revisions/pre_three_view_focus_2026-11-07/style.css -Destination frontend/src/style.css
Copy-Item -LiteralPath docs/revisions/pre_three_view_focus_2026-11-07/departureHeatmap.js -Destination frontend/src/charts/departureHeatmap.js
Copy-Item -LiteralPath docs/revisions/pre_three_view_focus_2026-11-07/airlineBars.js -Destination frontend/src/charts/airlineBars.js
npm --prefix frontend run build
npm --prefix frontend run build:preview
```

This restores the map-centered four-view layout and the earlier chart dimensions. Data, API responses, selection logic and playback behavior are unchanged. The earlier guided layout is separately saved in `docs/revisions/pre_single_screen_layout_2026-11-07/`.
