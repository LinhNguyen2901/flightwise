import {geoEquirectangular, geoPath, scaleSqrt, max, zoom, zoomIdentity} from 'd3';
import {feature} from 'topojson-client';
import stateAtlas from 'us-atlas/states-10m.json';
import {chartSurface, countDetails, markFill, number, rateLegend, COLORS} from './common.js';
import {sampleStatus, sumCounts} from './metrics.js';

// Fixed coordinate windows keep geography stable across selections and hourly frames.
const PANELS = [
  {id: 'main', title: 'Contiguous U.S.', box: [28, 102, 944, 420], bounds: [[-126, 24], [-66, 50]]},
  {id: 'AK', title: 'Alaska', box: [28, 540, 600, 170], bounds: [[-180, 50], [-129, 73]]},
  {id: 'HI', title: 'Hawaii', box: [648, 540, 324, 170], bounds: [[-161, 18.5], [-154, 23]]},
];
const stateShapes = feature(stateAtlas, stateAtlas.objects.states).features;
// Most airports are below 50%; higher rates retain their exact value in details.

export function regionFor(airport) {
  if (airport.region === 'AK' || airport.region === 'HI') return airport.region;
  if (['PR', 'VI', 'TT'].includes(airport.region)) return null;
  if (['GUM', 'SPN', 'PPG'].includes(airport.origin_code)) return null;
  return 'main';
}

export function createAirportMap(container, initial) {
  const surface = chartSurface(container, 'Airport map');
  const transforms = new Map();

  function update({airports, period, selectedOrigin = /** @type {string | null} */ (null),
    pinnedOrigin = /** @type {string | null} */ (null),
    hour = /** @type {number | null} */ (null), volumeMax = /** @type {number | undefined} */ (undefined),
    reducedMotion = false, onSelect}) {
    const {svg, nullFill} = surface;
    const totals = sumCounts(airports);
    const scope = hour == null ? 'All scheduled departures' : `Local departure hour ${String(hour).padStart(2, '0')}:00`;
    surface.reset(900, 'Where are late arrivals more common?',
      `${period} · ${scope} · ${number(totals.scheduled_count)} scheduled flights`, '');
    const radius = scaleSqrt().domain([0, volumeMax ?? max(airports, d => d.scheduled_count) ?? 1]).range([0, 18]);
    let plotted = 0;
    for (const panel of PANELS) {
      const [x, y, w, h] = panel.box;
      const group = svg.append('g').attr('data-region', panel.id);
      group.append('rect').attr('x', x).attr('y', y).attr('width', w).attr('height', h)
        .attr('rx', 8).attr('fill', '#f8fafb').attr('stroke', '#e0e7eb');
      group.append('text').attr('x', x + 12).attr('y', y + 20).attr('font-weight', 650).text(panel.title);
      const projection = geoEquirectangular().fitExtent([[x + 22, y + 36], [x + w - 22, y + h - 14]],
        {type: 'MultiPoint', coordinates: panel.bounds});
      const path = geoPath(projection);
      const clipId = `map-clip-${panel.id}`;
      group.append('clipPath').attr('id', clipId).append('rect')
        .attr('x', x + 1).attr('y', y + 28).attr('width', w - 2).attr('height', h - 29);
      const clipped = group.append('g').attr('clip-path', `url(#${clipId})`);
      const mapLayer = clipped.append('g');
      const labelLayer = clipped.append('g');
      const shapes = stateShapes.filter(state => panel.id === 'AK' ? state.id === '02' :
        panel.id === 'HI' ? state.id === '15' : !['02', '15', '72', '78'].includes(state.id));
      mapLayer.selectAll('.state-outline').data(shapes).join('path')
        .attr('class', 'state-outline').attr('d', path)
        .attr('fill', '#e7edf0').attr('stroke', '#c7d3da').attr('stroke-width', 0.9);
      const rows = airports.filter(d => regionFor(d) === panel.id)
        .sort((a, b) => b.scheduled_count - a.scheduled_count);
      const points = mapLayer.selectAll('.airport').data(rows, d => d.origin_id).join('circle')
        .attr('class', 'mark airport').attr('data-origin', d => d.origin_code)
        .attr('data-status', sampleStatus)
        .attr('cx', d => projection([d.LONGITUDE, d.LATITUDE])[0])
        .attr('cy', d => projection([d.LONGITUDE, d.LATITUDE])[1])
        .attr('r', d => d.scheduled_count ? Math.max(2, radius(d.scheduled_count)) : 1.6)
        .attr('fill', d => markFill(d, nullFill)).attr('stroke', d => d.origin_code === selectedOrigin ? COLORS.selected : '#536574')
        .attr('stroke-width', d => d.origin_code === selectedOrigin ? 3 : 0.8)
        .attr('stroke-dasharray', d => sampleStatus(d) === 'low_n' ? '2 2' : null)
        .attr('aria-pressed', d => onSelect ? String(d.origin_code === selectedOrigin) : null);
      surface.details(points, d => `${d.origin_code} · ${d.name}\n${countDetails(d)}`, onSelect);

      const rings = mapLayer.selectAll('.comparison-ring')
        .data(rows.filter(d => pinnedOrigin && (d.origin_code === pinnedOrigin || d.origin_code === selectedOrigin)))
        .join('circle').attr('class', 'comparison-ring')
        .attr('data-origin', d => d.origin_code)
        .attr('data-role', d => d.origin_code === pinnedOrigin ? 'pinned' : 'current')
        .attr('cx', d => projection([d.LONGITUDE, d.LATITUDE])[0])
        .attr('cy', d => projection([d.LONGITUDE, d.LATITUDE])[1])
        .attr('r', d => (d.scheduled_count ? Math.max(2, radius(d.scheduled_count)) : 1.6) + 5)
        .attr('fill', 'none').attr('stroke', COLORS.selected).attr('stroke-width', 3)
        .attr('stroke-dasharray', d => d.origin_code === pinnedOrigin ? '4 2' : null)
        .style('pointer-events', 'none');

      if (hour != null && !reducedMotion) points.attr('opacity', 0.3).transition().duration(300).attr('opacity', 1);

      function showLabels(transform) {
        const labels = [];
        const used = [];
        const candidates = rows.filter(d => transform.k >= 1.8 ||
          d.origin_code === selectedOrigin || ['ATL', 'LAX', 'JFK'].includes(d.origin_code));
        for (const airport of candidates) {
          const [px, py] = projection([airport.LONGITUDE, airport.LATITUDE]);
          const cx = transform.applyX(px);
          const cy = transform.applyY(py);
          if (cx < x + 4 || cx > x + w - 4 || cy < y + 32 || cy > y + h - 4) continue;
          const text = airport.origin_code;
          const width = text.length * 7.5;
          const bubble = airport.scheduled_count ? Math.max(2, radius(airport.scheduled_count)) : 1.6;
          let left = cx + bubble + 4;
          if (left + width > x + w - 4) left = cx - bubble - width - 4;
          if (left < x + 4) continue;
          const box = {left: left - 4, right: left + width + 4, top: cy - 12, bottom: cy + 10};
          if (used.some(other => box.left < other.right && box.right > other.left &&
            box.top < other.bottom && box.bottom > other.top)) continue;
          used.push(box);
          labels.push({id: airport.origin_id, text, x: left, y: cy + 4});
        }
        labelLayer.selectAll('.airport-label').data(labels, d => d.id).join('text')
          .attr('class', 'airport-label').attr('x', d => d.x).attr('y', d => d.y)
          .attr('font-weight', 700).attr('paint-order', 'stroke')
          .attr('stroke', 'white').attr('stroke-width', 2)
          .style('pointer-events', 'none').text(d => d.text);
      }

      const behavior = zoom().scaleExtent([1, 6])
        .extent([[x, y + 28], [x + w, y + h]])
        .translateExtent([[x, y + 28], [x + w, y + h]])
        .filter(event => !event.button && (event.type === 'wheel' || !event.target.closest('.airport')))
        .on('zoom', event => {
          mapLayer.attr('transform', event.transform);
          // Keep bubbles readable as the geography expands, then reveal labels.
          points.attr('r', d => (d.scheduled_count ? Math.max(2, radius(d.scheduled_count)) : 1.6) / event.transform.k)
            .attr('stroke-width', d => (d.origin_code === selectedOrigin ? 3 : 0.8) / event.transform.k);
          rings.attr('r', d => ((d.scheduled_count ? Math.max(2, radius(d.scheduled_count)) : 1.6) + 5) / event.transform.k)
            .attr('stroke-width', 3 / event.transform.k)
            .attr('stroke-dasharray', d => d.origin_code === pinnedOrigin ? `${4 / event.transform.k} ${2 / event.transform.k}` : null);
          showLabels(event.transform);
          transforms.set(panel.id, event.transform);
        });
      group.call(behavior).call(behavior.transform, transforms.get(panel.id) ?? zoomIdentity);
      plotted += rows.length;
    }
    svg.attr('data-airport-count', plotted);
    rateLegend(svg, 730, nullFill);
    svg.append('text').attr('x', 28).attr('y', 860).attr('class', 'muted')
      .text(`Late-arrival rate by origin airport; bubble area shows scheduled volume. ${plotted} origins; ${hour == null ? 'shared bubble scale.' : 'fixed scale across hourly frames.'}`);
    svg.append('text').attr('x', 28).attr('y', 880).attr('class', 'muted')
      .text('Alaska/Hawaii insets have separate geographic scales. U.S. Census 2017 outlines; local hours are not UTC snapshots.');
    const sizes = hour == null ? [1000, 10000, 100000] : [100, 1000, 5000];
    for (const [i, value] of sizes.entries()) {
      const x = 275 + i * 115;
      svg.append('circle').attr('cx', x).attr('cy', 794).attr('r', radius(value))
        .attr('fill', 'none').attr('stroke', '#536574');
      svg.append('text').attr('x', x).attr('y', 836).attr('text-anchor', 'middle').text(number(value));
    }
    svg.append('text').attr('x', 28).attr('y', 797).attr('class', 'muted').text('Scheduled volume');
  }
  update(initial);
  return {update, destroy() { surface.destroy(); }};
}
