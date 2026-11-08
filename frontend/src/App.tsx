import {useCallback, useEffect, useMemo, useReducer, useRef, useState} from 'react';
import {API_BASE, loadAirportHours, loadContext, loadDashboard} from './api';
import type {Airport, AirportHourFrames, Context, Metadata} from './types';
import {initialSelection, selectionReducer} from './selection';
import AirportMap from './components/AirportMap';
import DepartureHeatmap from './components/DepartureHeatmap';
import AirlineBarChart from './components/AirlineBarChart';
import HourlyOverview from './components/HourlyOverview';
import AirportComparison from './components/AirportComparison';
import HourPlayback from './components/HourPlayback';
import './style.css';

type DashboardData = {metadata: Metadata; airports: Airport[]; context: Context};

function periodLabel(period: string) {
  const [start, end] = period.split('/');
  const month = (date: string) => new Date(`${date}T00:00:00Z`)
    .toLocaleString('en-US', {month: 'long', timeZone: 'UTC'});
  return `${month(start)}-${month(end)} ${end.slice(0, 4)}`;
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const [selection, dispatch] = useReducer(selectionReducer, initialSelection);
  const [context, setContext] = useState<Context | null>(null);
  const [contextError, setContextError] = useState('');
  const [contextLoading, setContextLoading] = useState(false);
  const [contextAttempt, setContextAttempt] = useState(0);
  const [frames, setFrames] = useState<AirportHourFrames | null>(null);
  const [frameError, setFrameError] = useState('');
  const [frameLoading, setFrameLoading] = useState(false);
  const [frameAttempt, setFrameAttempt] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);
  const cache = useRef(new Map<string, Context>());

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    loadDashboard(controller.signal)
      .then(([metadata, airports, allContext]) => {
        if (controller.signal.aborted) return;
        cache.current.clear();
        cache.current.set(`all:${metadata.version}`, allContext);
        setData({metadata, airports, context: allContext});
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Could not load dashboard data');
      })
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  }, [attempt]);

  const version = data?.metadata.version;
  useEffect(() => {
    if (!data) return;
    const controller = new AbortController();
    setFrameLoading(true);
    setFrameError('');
    setFrames(null);
    loadAirportHours(controller.signal)
      .then(result => {
        if (controller.signal.aborted) return;
        if (result.version !== data.metadata.version || result.frames.length !== 24) {
          throw new Error('Hour frames do not match this dashboard version');
        }
        setFrames(result);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setFrameError(cause instanceof Error ? cause.message : 'Could not load hour frames');
      })
      .finally(() => {if (!controller.signal.aborted) setFrameLoading(false);});
    return () => controller.abort();
  }, [data, frameAttempt]);

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      setReducedMotion(preference.matches);
      if (preference.matches) dispatch({type: 'pause'});
    };
    update();
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (!data || !version) return;
    const key = `${selection.originId ?? 'all'}:${version}`;
    const saved = cache.current.get(key);
    if (saved) {
      setContext(saved);
      setContextError('');
      setContextLoading(false);
      return;
    }
    if (selection.originId === null) return;
    const controller = new AbortController();
    setContext(null);
    setContextError('');
    setContextLoading(true);
    loadContext(selection.originId, controller.signal)
      .then(result => {
        if (controller.signal.aborted) return;
        cache.current.set(key, result);
        setContext(result);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setContextError(cause instanceof Error ? cause.message : 'Could not load airport context');
      })
      .finally(() => {if (!controller.signal.aborted) setContextLoading(false);});
    return () => controller.abort();
  }, [data, version, selection.originId, contextAttempt]);

  const onAirport = useCallback((airport: Airport) => dispatch({type: 'airport', originId: airport.origin_id}), []);
  const onCell = useCallback((cell: {weekday: number; hour: number}) =>
    dispatch({type: 'cell', cell: [cell.weekday, cell.hour]}), []);
  const onBrush = useCallback((cells: [number, number][]) => dispatch({type: 'replaceCells', cells}), []);
  const airport = data?.airports.find(item => item.origin_id === selection.originId);
  const activeContext = context?.origin_id === selection.originId && context?.version === version ? context : null;
  const pinnedAirport = data?.airports.find(item => item.origin_id === selection.pinnedOriginId);
  const pinnedContext = pinnedAirport && version
    ? cache.current.get(`${pinnedAirport.origin_id}:${version}`) : null;
  const framesReady = Boolean(frames && frames.version === version && frames.frames.length === 24);
  const frameVolumeMax = useMemo(() => frames
    ? Math.max(1, ...frames.frames.flatMap(frame => frame.rows.map(row => row.scheduled_count))) : 1,
    [frames]);
  const frameRows = frames && framesReady && selection.animationHour !== null
    ? frames.frames[selection.animationHour].rows : null;
  useEffect(() => {
    if (!selection.isPlaying || !framesReady || !activeContext || reducedMotion) return;
    const timer = window.setInterval(() => dispatch({type: 'tick'}), 1000);
    return () => window.clearInterval(timer);
  }, [selection.isPlaying, framesReady, activeContext, reducedMotion]);
  const period = data ? periodLabel(data.metadata.period) : '';
  const number = (value: number) => value.toLocaleString();
  const timeLabel = selection.animationHour !== null
    ? `Local hour ${String(selection.animationHour).padStart(2, '0')}:00 across weekdays`
    : selection.cells.length ? `${selection.cells.length} selected time cell${selection.cells.length === 1 ? '' : 's'}` : 'All valid times';
  const tupleLabels = selection.cells.map(([day, hour]) =>
    `${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][day - 1]} ${String(hour).padStart(2, '0')}:00`);
  const tupleSummary = selection.cells.length === 168 ? 'All 168 weekday/hour cells selected' :
    `${tupleLabels.slice(0, 12).join(', ')}${tupleLabels.length > 12 ? `, and ${tupleLabels.length - 12} more` : ''}`;

  return <main>
    <header>
      <p className="eyebrow">FlightWise · July-September 2025</p>
      <h1>Explore Flight Reliability: Late arrivals</h1>
      <p>Explore scheduled flights and arrival outcomes from real reporting-carrier data.</p>
    </header>
    {loading && <p role="status">Loading prepared flight data…</p>}
    {error && <section role="alert" className="error"><p>Could not load data from {API_BASE}: {error}</p>
      <button onClick={() => setAttempt(value => value + 1)}>Retry</button></section>}
    {!loading && !error && data && <>
      <section aria-label="Current data summary">
        <p className="scope">{period} · {data.metadata.origin_scope}</p>
        <div className="cards">
          <article><strong>{number(data.metadata.totals.scheduled_count)}</strong><span>Scheduled flights</span></article>
          <article><strong>{number(data.airports.length)}</strong><span>Origin airports</span></article>
          <article><strong>{number(Object.keys(data.metadata.carrier_names).length)}</strong><span>Reporting airlines</span></article>
        </div>
        <p className="detail">Data version: {data.metadata.version}. Times are scheduled local departure hours at each origin. Late arrival means at least 15 minutes late among eligible completed flights.</p>
      </section>
      {data.airports.length === 0 || data.context.rows.length === 0 ?
        <section className="empty" role="status">No chart data is available for this period.</section> : <>
          <section className="selection-summary" aria-label="Current selection">
            <h2>Current exploration</h2>
            <div className="selection-values">
              <p><span>Airport</span><strong>{airport ? `${airport.origin_code} · ${airport.name}` : 'All origins'}</strong></p>
              <p><span>Time</span><strong>{timeLabel}</strong></p>
              {pinnedAirport && <p><span>Comparison pin</span><strong>{pinnedAirport.origin_code} · {pinnedAirport.name}</strong></p>}
            </div>
            <div className="selection-actions">
              <button onClick={() => dispatch({type: 'clearAirport'})} disabled={selection.originId === null}>Clear airport</button>
              <button onClick={() => dispatch({type: 'clearTime'})} disabled={!selection.cells.length}>Clear time</button>
              <button onClick={() => dispatch({type: 'reset'})} disabled={selection.originId === null && selection.pinnedOriginId === null && !selection.cells.length && selection.animationHour === null}>Reset all</button>
              <button onClick={() => dispatch({type: 'pinAirport'})}
                disabled={!airport || !activeContext || selection.pinnedOriginId === selection.originId}>
                {pinnedAirport ? 'Pin current instead' : 'Pin airport to compare'}</button>
            </div>
            {selection.cells.length > 0 && <p className="detail">{selection.animationHour !== null ? 'Suspended manual' : 'Selected'} weekday/hour tuples: {tupleSummary}</p>}
          </section>
          <nav className="explore-steps" aria-label="Explore in three steps">
            <a href="#airport-map"><span>1</span><strong>Airport View</strong><small>Map updates the heatmap</small></a>
            <a href="#departure-heatmap"><span>2</span><strong>Departure Time View</strong><small>Heatmap filters airline bars</small></a>
            <a href="#airline-bars"><span>3</span><strong>Airlines View</strong><small>For this airport and time</small></a>
          </nav>
          <div className="views" aria-label="Flight reliability charts">
            <section className="chart-card map-card" id="airport-map">
              <div className="view-intro"><span className="step-number">1</span><h2>Airport View</h2></div>
              <HourPlayback hour={selection.animationHour} isPlaying={selection.isPlaying}
                ready={Boolean(framesReady && activeContext)} loading={frameLoading}
                error={frameError} reducedMotion={reducedMotion} dispatch={dispatch}
                retry={() => setFrameAttempt(value => value + 1)} />
              <AirportMap airports={data.airports} period={period}
              selectedOrigin={airport?.origin_code ?? null} pinnedOrigin={pinnedAirport?.origin_code ?? null}
              onSelect={onAirport}
              hour={selection.animationHour} frameRows={frameRows} reducedMotion={reducedMotion}
              volumeMax={selection.animationHour === null ? Math.max(...data.airports.map(item => item.scheduled_count)) : frameVolumeMax} />
            </section>
            {contextLoading || !activeContext ? <section className="chart-card context-status" role="status">
              {contextError ? <div className="error" role="alert"><p>Could not load {airport?.origin_code ?? 'airport'} context: {contextError}</p>
                <button onClick={() => setContextAttempt(value => value + 1)}>Retry airport</button></div> :
                <p>Loading {airport?.origin_code ?? 'all-origin'} context…</p>}
            </section> : <>
              <section className="chart-card heatmap-card" id="departure-heatmap">
                <div className="view-intro"><span className="step-number">2</span><h2>Departure Time View</h2><span className="view-question">When are late-arrival rates highest?</span></div>
                <DepartureHeatmap rows={activeContext.rows} period={period}
                origin={airport?.origin_code ?? 'ALL'} selectedCells={selection.animationHour === null ? selection.cells : []}
                activeHour={selection.animationHour} onSelect={onCell} onBrush={onBrush}
                reducedMotion={reducedMotion} /></section>
              <section className="chart-card airline-card" id="airline-bars">
                <div className="view-intro"><span className="step-number">3</span><h2>Airlines View</h2><span className="view-question">How do late-arrival rates compare?</span></div>
                <AirlineBarChart rows={activeContext.rows} period={period}
                origin={airport?.origin_code ?? 'ALL'} selectedCells={selection.cells} selectionLabel={timeLabel}
                activeHour={selection.animationHour} reducedMotion={reducedMotion} /></section>
              <section className="chart-card hourly-card">
                <div className="view-intro secondary-intro comparison-heading">
                  <div><h2>{pinnedAirport ? 'Compare airport hours' : 'All-hour context'}</h2>
                    <p>{pinnedAirport
                      ? `Scheduled-flight share and late-arrival rate by local departure hour for pinned ${pinnedAirport.origin_code} and the current airport. Both panels use matching axes; heatmap cells do not filter them.`
                      : `Scheduled-flight share and late-arrival rate by local departure hour for ${airport?.origin_code ?? 'all origins'}. This overview keeps all weekdays and does not use selected heatmap cells.`}</p></div>
                  <div className="comparison-actions">
                    {pinnedAirport && <button onClick={() => dispatch({type: 'clearComparison'})}>Clear comparison</button>}
                  </div>
                </div>
                {pinnedAirport && <p className="comparison-key">Pink map rings: dashed = pinned, solid = current airport.</p>}
                {pinnedAirport && <p className="comparison-scroll-hint">Swipe the chart sideways to see both airports.</p>}
                {pinnedAirport ? airport && airport.origin_id !== pinnedAirport.origin_id && pinnedContext
                  ? <AirportComparison pinned={{code: pinnedAirport.origin_code, name: pinnedAirport.name}}
                      current={{code: airport.origin_code, name: airport.name}}
                      pinnedRows={pinnedContext.rows} currentRows={activeContext.rows} period={period} />
                  : <p className="comparison-prompt" role="status">Choose a different airport on the map to compare with {pinnedAirport.origin_code}.</p>
                  : <HourlyOverview rows={activeContext.rows} period={period} origin={airport?.origin_code ?? 'ALL'} />}
              </section>
              {!activeContext.rows.length && <section className="empty" role="status">No flights are available for this airport context.</section>}
            </>}
          </div>
        </>}
    </>}
  </main>;
}
