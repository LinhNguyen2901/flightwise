import {useEffect, useRef} from 'react';
import {createAirportMap} from '../charts/airportMap.js';
import {frameAirports, mapAirports} from '../chartData';
import type {Airport, AirportHourRow} from '../types';

export default function AirportMap({airports, period, selectedOrigin, pinnedOrigin, onSelect, hour, frameRows, volumeMax, reducedMotion}: {
  airports: Airport[]; period: string; selectedOrigin: string | null; pinnedOrigin: string | null;
  onSelect: (airport: Airport) => void;
  hour: number | null; frameRows: AirportHourRow[] | null; volumeMax: number; reducedMotion: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof createAirportMap> | null>(null);
  useEffect(() => {
    if (!container.current) return;
    chart.current = createAirportMap(container.current, {airports: mapAirports(airports), period,
      selectedOrigin, pinnedOrigin, onSelect});
    return () => {chart.current?.destroy(); chart.current = null;};
  }, []);
  useEffect(() => {
    const visible = frameRows ? frameAirports(airports, frameRows) : airports;
    chart.current?.update({airports: mapAirports(visible), period, selectedOrigin, pinnedOrigin, onSelect, hour,
      volumeMax, reducedMotion});
  }, [airports, period, selectedOrigin, pinnedOrigin, onSelect, hour, frameRows, volumeMax, reducedMotion]);
  return <div ref={container} />;
}
