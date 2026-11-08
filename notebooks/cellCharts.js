import {createAirportMap} from '../frontend/src/charts/airportMap.js';
import {createDepartureHeatmap} from '../frontend/src/charts/departureHeatmap.js';
import {createAirlineBars} from '../frontend/src/charts/airlineBars.js';
import {createHourlyOverview} from '../frontend/src/charts/hourlyOverview.js';
import {drawHistogram, drawRateLines, drawAirportScatter, drawAirportComparison} from './analysisCharts.js';
import {renderDiagram} from './diagrams.js';

// The Python cell supplies the actual rows. No presets, file reads or aggregation here.
export function render(container, kind, rows, options) {
  switch (kind) {
    case 'map': return createAirportMap(container, {...options, airports: rows});
    case 'heatmap': return createDepartureHeatmap(container, {...options, cells: rows});
    case 'bars': return createAirlineBars(container, {...options, rows});
    case 'hourly_overview': return createHourlyOverview(container, {...options, rows});
    case 'histogram': return drawHistogram(container, {...options, rows});
    case 'lines': return drawRateLines(container, {...options, rows});
    case 'scatter': return drawAirportScatter(container, {...options, rows});
    case 'airport_compare': return drawAirportComparison(container, {...options, rows});
    case 'diagram': return renderDiagram(container, options.kind);
    default: throw new Error(`Unknown notebook chart: ${kind}`);
  }
}
