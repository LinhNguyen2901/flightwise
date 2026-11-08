import {select} from 'd3';
import {svgStyles} from '../frontend/src/charts/common.js';

// Fixed review sketches, not an application diagram framework.
export function renderDiagram(container, kind) {
  const height = kind === 'layout' ? 500 : 390;
  const svg = select(container).append('svg').attr('xmlns', 'http://www.w3.org/2000/svg')
    .attr('viewBox', `0 0 1000 ${height}`).attr('width', 1000).attr('height', height).attr('role', 'img');
  svg.append('style').text(svgStyles);
  svg.append('rect').attr('width', 1000).attr('height', height).attr('fill', 'white');
  function text(x, y, value, size = 14, weight = 400) {
    svg.append('text').attr('x', x).attr('y', y).style('font-size', `${size}px`).attr('font-weight', weight).text(value);
  }
  function box(x, y, w, h, title, lines = []) {
    svg.append('rect').attr('x', x).attr('y', y).attr('width', w).attr('height', h).attr('rx', 8)
      .attr('fill', '#f0f7f7').attr('stroke', '#b7d7d9');
    text(x + 16, y + 28, title, 16, 650);
    lines.forEach((line, i) => text(x + 16, y + 53 + i * 22, line, 13));
  }
  function arrow(x, y, end, label) {
    svg.append('path').attr('d', `M${x},${y}H${end}m-8,-5l8,5l-8,5`).attr('fill', 'none').attr('stroke', '#007f87').attr('stroke-width', 2);
    text(x + 4, y - 13, label, 12, 600);
  }
  const titles = {layout: 'Dashboard layout / proposed design', coordination: 'Two distinct selection relationships',
    architecture: 'From immutable source files to visible marks', states: 'Loading, failure and empty-state designs', playback: 'Optional hour playback / storyboard only'};
  svg.attr('aria-label', titles[kind]); text(28, 40, titles[kind], 23, 650);
  if (kind === 'layout') {
    box(28, 65, 944, 65, 'Scope and selections', ['Period · airport · exact weekday/hour cells · Clear airport / Clear time / Reset all']);
    box(28, 145, 944, 75, '01 Airport map — U.S. overview', ['State outlines · Alaska/Hawaii insets · rate color · volume size · selection']);
    box(28, 235, 944, 75, '02 Hourly overview — proposed fourth view', ['Scheduled-flight share bars + late-rate line overlaid · shared hour axis · left/right % axes']);
    box(28, 325, 560, 105, '03 Departure-hour × weekday heatmap', ['168 cells remain visible · selected cells outlined', 'Tooltips expose counts and cancellation rate']);
    box(608, 325, 364, 105, '04 Airline bars', ['Full reporting-airline names · rate order', 'Counts on hover · 0–100% rate axis']);
    text(28, 468, 'Proposed layout for review. Hourly overview follows airport context; the two required selection pairs remain unchanged.', 13);
  } else if (kind === 'coordination') {
    box(28, 100, 250, 120, 'Airport map', ['Select JFK', 'Map stays an overview', 'Selected airport outlined']);
    arrow(285, 160, 367, 'A: origin');
    box(375, 100, 250, 120, 'Time heatmap', ['Reaggregate to JFK', 'Select Monday 08:00', 'Keep full 24 × 7 context']);
    arrow(633, 160, 714, 'B: cells');
    box(722, 100, 250, 120, 'Airline bars', ['JFK AND selected cells', 'Union of exact time tuples', 'Counts first; divide last']);
    text(28, 270, 'Airport changes also update bars, retaining the manual time selection. This still counts as pair A.', 14);
    text(28, 300, 'Clear airport preserves time cells. Clear time preserves airport. Reset all clears both.', 14);
    text(28, 330, 'Monday 08 + Friday 17 never includes Monday 17 or Friday 08. No airline-driven filtering.', 14);
  } else if (kind === 'architecture') {
    box(28, 100, 245, 120, 'BTS raw ZIP files', ['Local, immutable inputs', 'Flight records + coordinates', 'Hashes in manifest']);
    arrow(281, 160, 367, 'prepare');
    box(375, 100, 250, 120, 'pandas → Parquet', ['Offline count aggregates', 'Load once in FastAPI (M2)', 'JSON: airports / context']);
    arrow(633, 160, 714, 'HTTP');
    box(722, 100, 250, 120, 'React + D3 (M3–M4)', ['React owns selection state', 'D3 owns chart descendants', 'Sum counts in browser']);
    text(28, 270, 'M1.6: notebook reads raw ZIPs, cleans rows, builds summaries and feeds the same D3 modules.', 14);
    text(28, 300, 'No raw flight arrays in the web app. Chart functions receive data and callbacks; they never fetch.', 14);
    text(28, 330, 'Data loading changes at integration; the approved chart-rendering source is reused.', 14);
  } else if (kind === 'states') {
    box(28, 100, 300, 140, 'Loading airport context…', ['Keep period and scope visible', 'Mark dependent charts busy', 'No stale values as new results']);
    box(350, 100, 300, 140, 'Could not load this context', ['Show the requested airport', '[ Retry ]', 'Preserve the chosen selection']);
    box(672, 100, 300, 140, 'No flights in this selection', ['Keep the full heatmap', '[ Clear time ]  [ Reset all ]', 'Do not label missing as 0%']);
    text(28, 290, 'These are UI sketches. Real network loading, retry and stale-response handling belong to M2–M4.', 14);
    text(28, 320, 'No eligible arrivals: hatched neutral marks. Small sample: dashed outline / fewer than 30 warning.', 14);
  } else {
    box(28, 85, 944, 75, 'Paused at 08:00 local departure hour', ['[ Play / Pause ]     00 ─────────●──────────────────── 23     [ Exit playback ]']);
    box(28, 182, 300, 115, 'Map', ['All origins at active hour', 'Fixed position / size / color', 'Empty hours clear old marks']);
    box(350, 182, 300, 115, 'Heatmap', ['Keep full origin context', 'Highlight active hour column', 'Manual cells suspended']);
    box(672, 182, 300, 115, 'Airline bars', ['Selected origin + active hour', 'Pool all weekdays', 'Exit restores manual cells']);
    text(28, 332, 'Historical pooled local hours, not a simultaneous UTC event. 04:00 is especially sparse.', 14);
    text(28, 361, 'M6 only: play/pause, seek, reduced motion, cleanup and filter restoration must still be implemented.', 14);
  }
}
