# Restore the previous guided layout

`style.css` here is an exact copy from before the November 7 compact layout revision. From the repository root in PowerShell:

```powershell
Copy-Item -LiteralPath docs/revisions/pre_single_screen_layout_2026-11-07/style.css -Destination frontend/src/style.css
npm --prefix frontend run build
```

This restores the previous wide-screen placement and spacing. The charts, data, API, selection logic and playback behavior were not changed by the compact layout revision. The new screenshots and browser checks remain as review evidence.
