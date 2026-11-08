import {useEffect, useRef} from 'react';
import {createHourlyOverview} from '../charts/hourlyOverview.js';
import {hourlyCounts} from '../chartData';
import type {ContextRow} from '../types';

export default function HourlyOverview({rows, period, origin}: {rows: ContextRow[]; period: string; origin: string}) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current) return;
    const chart = createHourlyOverview(container.current, {rows: hourlyCounts(rows), period, origin});
    return () => chart.destroy();
  }, [rows, period, origin]);
  return <div ref={container} />;
}
