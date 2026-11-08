import {useEffect, useRef} from 'react';
import {createAirlineBars} from '../charts/airlineBars.js';
import {airlineCounts, playbackAirlineCounts} from '../charts/metrics.js';
import type {ContextRow} from '../types';

export default function AirlineBarChart({rows, period, origin, selectedCells, selectionLabel, activeHour,
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches}: {
  rows: ContextRow[]; period: string; origin: string; selectedCells: readonly (readonly [number, number])[];
  selectionLabel: string; activeHour: number | null; reducedMotion?: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof createAirlineBars> | null>(null);
  const firstUpdate = useRef(true);
  const counts = () => activeHour === null ? airlineCounts(rows, [...selectedCells])
    : playbackAirlineCounts(rows, activeHour);
  useEffect(() => {
    if (!container.current) return;
    chart.current = createAirlineBars(container.current, {rows: counts(), period,
      origin, selectionLabel, stableOrder: activeHour !== null, animate: !reducedMotion});
    firstUpdate.current = true;
    return () => {chart.current?.destroy(); chart.current = null;};
  }, []);
  useEffect(() => {
    if (firstUpdate.current) {firstUpdate.current = false; return;}
    chart.current?.update({rows: counts(), period, origin, selectionLabel,
      stableOrder: activeHour !== null, animate: !reducedMotion});
  }, [rows, period, origin, selectedCells, selectionLabel, activeHour, reducedMotion]);
  return <div ref={container} />;
}
