# Restore the prior three-view layout

This folder holds the six frontend files as they were before moving the Alaska and Hawaii map insets beneath the mainland and simplifying the headings on November 7, 2026. From the project root, run:

```powershell
$source = 'docs/revisions/pre_insets_below_2026-11-07'
Copy-Item "$source/airportMap.js" 'frontend/src/charts/airportMap.js'
Copy-Item "$source/departureHeatmap.js" 'frontend/src/charts/departureHeatmap.js'
Copy-Item "$source/airlineBars.js" 'frontend/src/charts/airlineBars.js'
Copy-Item "$source/common.js" 'frontend/src/charts/common.js'
Copy-Item "$source/App.tsx" 'frontend/src/App.tsx'
Copy-Item "$source/style.css" 'frontend/src/style.css'
npm --prefix frontend run build
```

The earlier map-centered layout is separately saved in `docs/revisions/pre_three_view_focus_2026-11-07/`.
