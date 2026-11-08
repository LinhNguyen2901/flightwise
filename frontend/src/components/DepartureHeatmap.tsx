import {useEffect, useRef} from 'react';
import {createDepartureHeatmap} from '../charts/departureHeatmap.js';
import type {ContextRow} from '../types';
import {heatmapCounts} from '../charts/metrics.js';

export default function DepartureHeatmap({rows, period, origin, selectedCells, activeHour, onSelect, onBrush,
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches}: {
  rows: ContextRow[]; period: string; origin: string; selectedCells: readonly (readonly [number, number])[];
  activeHour: number | null; reducedMotion?: boolean;
  onSelect: (cell: {weekday: number; hour: number}) => void;
  onBrush: (cells: [number, number][]) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof createDepartureHeatmap> | null>(null);
  const firstUpdate = useRef(true);
  useEffect(() => {
    if (!container.current) return;
    chart.current = createDepartureHeatmap(container.current, {cells: heatmapCounts(rows), period, origin,
      selectedCells, activeHour, onSelect, onBrush, animate: !reducedMotion});
    firstUpdate.current = true;
    return () => {chart.current?.destroy(); chart.current = null;};
  }, []);
  useEffect(() => {
    if (firstUpdate.current) {firstUpdate.current = false; return;}
    chart.current?.update({cells: heatmapCounts(rows), period, origin, selectedCells: [...selectedCells],
      activeHour, onSelect, onBrush, animate: !reducedMotion});
  }, [rows, period, origin, selectedCells, activeHour, onSelect, onBrush, reducedMotion]);
  return <div ref={container} />;
}
