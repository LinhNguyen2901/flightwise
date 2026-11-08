// Small review harness only. React state, HTTP, brushing and playback belong to later milestones.
import {createAirportMap} from '../frontend/src/charts/airportMap.js';
import {createDepartureHeatmap} from '../frontend/src/charts/departureHeatmap.js';
import {createAirlineBars} from '../frontend/src/charts/airlineBars.js';
import {heatmapCounts, airlineCounts, DAYS} from '../frontend/src/charts/metrics.js';
import {renderDiagram} from './diagrams.js';

export const scenarios = [
  {id: 'overview', label: 'All origins / all valid times', origin: 'ALL', cells: []},
  {id: 'jfk', label: 'JFK / all valid times', origin: 'JFK', cells: []},
  {id: 'jfk_mon08', label: 'JFK / Monday 08:00', origin: 'JFK', cells: [[1, 8]]},
  {id: 'atl_disjoint', label: 'ATL / Monday 08:00 + Friday 17:00', origin: 'ATL', cells: [[1, 8], [5, 17]]},
  {id: 'abe', label: 'ABE / all valid times (small airport)', origin: 'ABE', cells: []},
  {id: 'abe_fri17', label: 'ABE / Friday 17:00 (sparse, true 0%)', origin: 'ABE', cells: [[5, 17]]},
  {id: 'bqn_empty', label: 'BQN / Monday 08:00 (no flights)', origin: 'BQN', cells: [[1, 8]]},
  {id: 'bqn_morning', label: 'BQN / weekdays 06–09 (one carrier)', origin: 'BQN', cells: [1, 2, 3, 4, 5].flatMap(d => [6, 7, 8, 9].map(h => [d, h]))},
  {id: 'stc', label: 'STC / all valid times (very small sample)', origin: 'STC', cells: []},
  ...[4, 8, 17].map(hour => ({id: `hour${hour}`, label: `Map snapshot / ${String(hour).padStart(2, '0')}:00 local`, origin: 'ALL', cells: [], hour})),
];

export function selectionLabel(cells) {
  if (!cells.length) return 'All valid times';
  if (cells.length > 3) return `${cells.length} selected weekday/hour cells`;
  return cells.map(([d, h]) => `${DAYS[d - 1]} ${String(h).padStart(2, '0')}:00`).join(' + ');
}

export function mount(root, payload, options = {}) {
  root.innerHTML = `
    <style>
      * { box-sizing: border-box; }
      body { margin: 0; background: #f1f5f7; color: #142d40; font-family: Segoe UI, Arial, sans-serif; }
      .preview { max-width: 1080px; margin: auto; padding: 24px; }
      header { padding: 8px 0 18px; } h1 { font-size: 32px; margin: 8px 0; letter-spacing: -.8px; }
      .kicker { color: #007f87; font-size: 12px; letter-spacing: 2px; font-weight: 700; }
      .lede { color: #536574; line-height: 1.55; margin: 8px 0; }
      .controls { display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin:18px 0; }
      select { padding:10px; border:1px solid #a9bbc7; border-radius:6px; background:white; color:#142d40; max-width:100%; }
      .chart-card { background:white; border:1px solid #dce5ea; border-radius:12px; margin:16px 0; overflow:auto; }
      .fw-chart { min-width: 700px; } .note { padding:14px 18px; border-left:3px solid #007f87; background:#e5f2f2; line-height:1.6; font-size:13px; }
      footer { color:#536574; font-size:12px; line-height:1.6; } .diagram { margin-top:16px; background:white; border-radius:12px; overflow:auto; }
      .diagram svg { min-width:700px; display:block; width:100%; height:auto; }
    </style>
    <main class="preview">
      <header><div class="kicker">FLIGHTWISE / VISUAL REVIEW</div><h1>A quarter of departures.</h1>
      <p class="lede">Explore geography, scheduled departure time and reporting carriers.<br>July–September 2025 · Historical associations, not predictions.</p></header>
      <div class="note" id="provenance"></div>
      <div class="controls"><label for="scenario">Review context</label><select id="scenario"></select></div>
      <p class="lede" id="scope"></p>
      <section class="chart-card" id="map"></section>
      <section class="chart-card" id="heatmap"></section>
      <section class="chart-card" id="bars"></section>
      <footer>Presets demonstrate the proposed selection results. Live cross-view brushing, React/API integration and animation are later milestones.<br>Hover or keyboard-focus marks for details. On a narrow screen, scroll within a chart to retain legible labels.</footer>
      <section id="diagrams"></section>
    </main>`;
  root.querySelector('#provenance').textContent = payload.note;
  const reviewScenarios = [...scenarios];
  if (payload.no_eligible) reviewScenarios.push({id: 'no_eligible', ...payload.no_eligible,
    label: `${payload.no_eligible.origin} / ${selectionLabel(payload.no_eligible.cells)} (no eligible arrivals)`});
  const menu = root.querySelector('#scenario');
  for (const s of reviewScenarios) menu.add(new Option(s.label, s.id));
  const map = createAirportMap(root.querySelector('#map'), {airports: payload.airports, period: payload.period});
  const heatmap = createDepartureHeatmap(root.querySelector('#heatmap'), {cells: heatmapCounts([]), period: payload.period});
  const bars = createAirlineBars(root.querySelector('#bars'), {rows: [], carrierOrder: [], period: payload.period});
  const volumeMax = Math.max(1, ...payload.airports.map(d => d.scheduled_count));
  function show(scenario) {
    const context = payload.contexts[scenario.origin] ?? [];
    const frame = scenario.hour == null ? null : new Map(payload.frames[scenario.hour].map(d => [d.origin_id, d]));
    map.update({airports: frame ? payload.airports.map(d => ({...d, ...frame.get(d.origin_id)})) : payload.airports,
      period: payload.period, selectedOrigin: scenario.origin === 'ALL' ? null : scenario.origin, hour: scenario.hour, volumeMax});
    heatmap.update({cells: heatmapCounts(context), period: payload.period, origin: scenario.origin, selectedCells: scenario.cells});
    bars.update({rows: airlineCounts(context, scenario.cells), carrierOrder: [...new Set(context.map(d => d.carrier))].sort(),
      period: payload.period, origin: scenario.origin, selectionLabel: selectionLabel(scenario.cells)});
    root.querySelector('#scope').textContent = scenario.hour == null
      ? `${scenario.label}. Map retains the geographic overview; heatmap retains all 168 cells; bars use the selected context.`
      : `${scenario.label}. Static map frame only; heatmap and bars stay at baseline. Playback coordination is a storyboard, not implemented.`;
    root.dataset.scenario = scenario.id ?? 'custom';
    menu.value = scenario.id ?? '';
  }
  menu.addEventListener('change', () => show(reviewScenarios.find(d => d.id === menu.value)));
  for (const kind of ['layout', 'coordination', 'architecture', 'states', 'playback']) {
    const panel = document.createElement('div'); panel.className = 'diagram'; panel.dataset.diagram = kind;
    root.querySelector('#diagrams').append(panel); renderDiagram(panel, kind);
  }
  let initialScenario = scenarios[0];
  if (options.origin) {
    initialScenario = reviewScenarios.find(s => s.origin === options.origin && s.hour == null &&
      JSON.stringify(s.cells) === JSON.stringify(options.cells ?? []));
    if (!initialScenario) {
      initialScenario = {id: 'notebook_parameters', origin: options.origin, cells: options.cells ?? [],
        label: `${options.origin} / ${selectionLabel(options.cells ?? [])} (notebook parameters)`};
      reviewScenarios.push(initialScenario);
      menu.add(new Option(initialScenario.label, initialScenario.id));
    }
  }
  show(initialScenario);
  return {show, map, heatmap, bars, scenarios: reviewScenarios,
    destroy() {map.destroy(); heatmap.destroy(); bars.destroy(); root.replaceChildren();}};
}
