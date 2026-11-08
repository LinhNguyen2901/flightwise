# Restore the pre-review layout

These three files are exact copies of the frontend before the November 6 guided-layout revision. Run from the repository root in PowerShell to restore the earlier stacked layout and playback panel:

```powershell
Copy-Item -LiteralPath docs/revisions/pre_intuitive_layout_2026-11-06/App.tsx -Destination frontend/src/App.tsx
Copy-Item -LiteralPath docs/revisions/pre_intuitive_layout_2026-11-06/style.css -Destination frontend/src/style.css
Copy-Item -LiteralPath docs/revisions/pre_intuitive_layout_2026-11-06/HourPlayback.tsx -Destination frontend/src/components/HourPlayback.tsx
npm --prefix frontend run build
```

This restores the stacked layout and earlier playback panel. Later chart changes, including the shared rate colors and filter transitions, remain in place. The D3 chart modules, API, data, and selection behavior were not changed by the layout revision itself. The new layout browser script and screenshots can remain as historical review evidence.
