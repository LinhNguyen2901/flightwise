import type {SelectionAction} from '../selection';

export default function HourPlayback({hour, isPlaying, savedCells, ready, loading, error,
  reducedMotion, dispatch, retry}: {
  hour: number | null; isPlaying: boolean; savedCells: number; ready: boolean;
  loading: boolean; error: string; reducedMotion: boolean;
  dispatch: (action: SelectionAction) => void; retry: () => void;
}) {
  const active = hour !== null;
  const hourText = active ? String(hour).padStart(2, '0') : '';
  return <section className="playback" aria-label="Historical departure-hour playback">
    <h2>Explore the local-hour profile</h2>
    <p>Each frame pools flights scheduled in the same local departure hour across July–September 2025. Frames are not a live day or UTC snapshot.</p>
    {loading && <p role="status">Loading 24 airport-hour frames…</p>}
    {error && <div className="error" role="alert"><p>Could not load hour frames: {error}</p>
      <button onClick={retry}>Retry frames</button></div>}
    {!active ? <button onClick={() => dispatch({type: 'enterPlayback'})} disabled={!ready}>Enter hour playback</button> : <>
      <div className="playback-controls">
        <button onClick={() => dispatch({type: isPlaying ? 'pause' : 'play'})}
          disabled={!ready || (reducedMotion && !isPlaying)}>{isPlaying ? 'Pause' : 'Play'}</button>
        <label htmlFor="playback-hour">Local departure hour: <strong>{hourText}:00–{hourText}:59</strong></label>
        <input id="playback-hour" type="range" min="0" max="23" step="1" value={hour}
          onChange={event => dispatch({type: 'seek', hour: Number(event.target.value)})} />
        <button onClick={() => dispatch({type: 'exitPlayback'})}>Exit playback</button>
      </div>
      <p className="detail">Hour {hourText} in the 00–23 profile. Airline bars use this hour across all weekdays at the selected airport.</p>
      {savedCells > 0 && <p className="detail">Your {savedCells} manual time cell{savedCells === 1 ? '' : 's'} are temporarily suspended and return when playback exits.</p>}
      {reducedMotion && <p className="detail">Automatic playback is disabled by your reduced-motion setting. Use the hour slider to explore frames.</p>}
    </>}
  </section>;
}
