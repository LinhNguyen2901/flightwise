# Restore the November 7 layout before airport comparison

This folder saves the five existing frontend files and the selection test as they were immediately before the optional comparison feature. It is the current three-view layout with the full-width all-hour chart below.

From the project root, run:

```powershell
$source = 'docs/revisions/pre_airport_comparison_2026-11-07'
Copy-Item "$source/App.tsx" 'frontend/src/App.tsx'
Copy-Item "$source/selection.ts" 'frontend/src/selection.ts'
Copy-Item "$source/style.css" 'frontend/src/style.css'
Copy-Item "$source/HourlyOverview.tsx" 'frontend/src/components/HourlyOverview.tsx'
Copy-Item "$source/hourlyOverview.js" 'frontend/src/charts/hourlyOverview.js'
Copy-Item "$source/selection.test.js" 'tests/charts/selection.test.js'
npm --prefix frontend run build
npm --prefix frontend test
```

The new `AirportComparison.tsx` and `airportComparison.js` become unused after restoring. They can be removed if desired. The saved source files are not overwritten by this feature.
