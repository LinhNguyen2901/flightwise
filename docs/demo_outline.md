# Narrated demo outline for student review (M5 draft)

When showing the optional comparison, point out the dashed pink ring on the pinned airport and solid pink ring on the current airport. In the lower section, show that bars mean each airport's scheduled-flight share and lines mean its late-arrival rate; the two panels use matching axes. Clear comparison to return to the original all-hour view.

**Comparison addition:** After demonstrating the two required links, select ATL, choose **Pin airport to compare**, then select LAX on the map. Scroll to the full-width lower section and show the two profiles on their shared rate axis; mention that heatmap time cells do not filter this all-hour comparison. Clear comparison to restore the original all-hour chart. This is an optional extra-credit demonstration, not a third required coordination pair.

This is a rehearsal sequence, not a recorded M7 deliverable. Use the student's own voice and actual name. Aim for about 4–6 minutes, with the dashboard and API running locally at the documented ports.

1. **Opening (about 20–30 seconds).** State the student's name, assignment, question, July–September 2025 BTS data and that the dashboard shows historical late-arrival rates, not predictions.
2. **Baseline views (about 45 seconds).** Show map position, bubble area and the shared smooth 0–50%+ Viridis legends; point out the hourly chart's separate percentage axes, heatmap's local scheduled hour/weekday axes, and airline bar percentage axis. Focus a mark to show counts and cancellation/diversion details.
3. **Pair A (about 45 seconds).** Select an airport on the map, show its highlighted bubble, changed heatmap context and the selected airport in the summary. Clear airport to restore all origins. Mention that the map remains an overview.
4. **Pair B (about 45 seconds).** With all origins, select one heatmap cell. Show its outline and changed airline bars. Select a second disjoint cell, such as Monday 08:00 and Friday 17:00, and explain that these are exact tuples. Clear time.
5. **Both together (about 60 seconds).** Select an airport, then two time cells. Show the selected origin/time summary, heatmap outlines and airline comparison for their intersection. Demonstrate brush replacement, keyboard Enter/Space on a cell if practical, and Reset all.
6. **Optional M6 playback (about 40–50 seconds).** Start playback, pause and seek to 08:00, then show the fixed map scale, heatmap hour outline and airline bars. Explain that each frame pools the same scheduled local hour across the quarter, not a live/UTC snapshot. Exit and show the manual time selection returning. If recording time is tight, shorten the baseline tour rather than omitting a demonstrated implemented feature.
7. **Robustness and limitations (about 35–45 seconds).** Show a sparse or empty time cell, then clear it. Explain that rates with fewer than 30 eligible arrivals are flagged, missing rates are not zero, and comparisons reflect this quarter and route/carrier mix. Demonstrate map zoom/pan/reset if time allows.
8. **Close (about 15–20 seconds).** Recap one observation only after checking its exact dashboard counts. State the local API/frontend architecture and any genuine limitations.

Before M7 recording, verify each spoken number in the live dashboard, check 1080p readability and audio, and ensure all implemented interactions appear in the final recording. M6 playback is now implemented, so include it if it remains in the final version.
