import {useEffect, useRef} from 'react';
import {createAirportComparison} from '../charts/airportComparison.js';
import {hourlyCounts} from '../chartData';
import type {ContextRow} from '../types';

type Props = {
  pinned: {code: string; name: string};
  current: {code: string; name: string};
  pinnedRows: ContextRow[];
  currentRows: ContextRow[];
  period: string;
};

export default function AirportComparison({pinned, current, pinnedRows, currentRows, period}: Props) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current) return;
    const chart = createAirportComparison(container.current, {
      airports: [
        {...pinned, rows: hourlyCounts(pinnedRows)},
        {...current, rows: hourlyCounts(currentRows)},
      ], period,
    });
    return () => chart.destroy();
  }, [pinned.code, pinned.name, current.code, current.name, pinnedRows, currentRows, period]);
  return <div className="comparison-chart" ref={container} />;
}
