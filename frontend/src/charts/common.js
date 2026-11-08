import {select, scaleSequential, interpolateViridis, format, range} from 'd3';
import {lateRate, cancellationRate, sampleStatus} from './metrics.js';

export const number = format(',d');
export const percent = value => value == null ? 'Not available' : format('.1%')(value);
export const rateColor = scaleSequential(interpolateViridis).domain([0, 0.5]).clamp(true);
export const COLORS = {ink: '#142d40', muted: '#536574', selected: '#d81b60', empty: '#edf1f3'};
let nextId = 0;

export const svgStyles = `
text { font-family: Segoe UI, Arial, sans-serif; fill: #142d40; font-size: 12px; }
.chart-title { font-size: 23px; font-weight: 650; }
.eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; fill: #007f87; }
.muted, .axis text { fill: #536574; }
.axis path, .axis line { stroke: #ccd5dc; }
.mark:focus { outline: none; stroke: ${COLORS.selected}; stroke-width: 4; }
.mark:hover { stroke: ${COLORS.selected}; stroke-width: 4; }
.grid line { stroke: #e2e8ed; } .grid path { display: none; }
`;

export function chartSurface(container, name) {
  const root = select(container).append('div').attr('class', 'fw-chart');
  const svg = root.append('svg').attr('xmlns', 'http://www.w3.org/2000/svg')
    .attr('role', 'group').attr('aria-label', name)
    .style('display', 'block').style('width', '100%').style('height', 'auto');
  const tooltip = root.append('div').attr('class', 'fw-tooltip').attr('role', 'status')
    .attr('aria-live', 'polite').attr('hidden', true)
    .style('position', 'fixed').style('z-index', 10).style('pointer-events', 'none')
    .style('white-space', 'pre-line').style('background', '#142d40').style('color', 'white')
    .style('padding', '12px 16px').style('border-radius', '8px').style('font', '13px Segoe UI, sans-serif')
    .style('max-width', '310px').style('box-shadow', '0 6px 24px #142d4033');
  const id = `fw-${++nextId}`;

  function reset(height, title, subtitle, eyebrow, showSubtitle = true, showTitle = true) {
    tooltip.attr('hidden', true);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 1000 ${height}`).attr('width', 1000).attr('height', height);
    svg.append('style').text(svgStyles);
    svg.append('rect').attr('width', 1000).attr('height', height).attr('fill', 'white');
    // desc keeps the chart context for assistive technology without a browser hover strip.
    svg.append('desc').text(`${title}. ${subtitle}`);
    if (eyebrow) svg.append('text').attr('x', 28).attr('y', 27).attr('class', 'eyebrow').text(eyebrow);
    if (showTitle) svg.append('text').attr('x', 28).attr('y', 57).attr('class', 'chart-title').text(title);
    if (showSubtitle && subtitle) svg.append('text').attr('x', 28).attr('y', 80).attr('class', 'muted').text(subtitle);
    const pattern = svg.append('defs').append('pattern').attr('id', `${id}-null`)
      .attr('patternUnits', 'userSpaceOnUse').attr('width', 6).attr('height', 6);
    pattern.append('rect').attr('width', 6).attr('height', 6).attr('fill', '#e4e9ed');
    pattern.append('path').attr('d', 'M-1,1L1,-1M0,6L6,0M5,7L7,5')
      .attr('stroke', '#9daab5').attr('stroke-width', 1);
  }

  function details(marks, label, onSelect) {
    marks.attr('tabindex', 0).attr('role', onSelect ? 'button' : 'img')
      .attr('aria-label', label)
      .on('pointerenter.details focus.details', function(event, d) {
        tooltip.text(label(d)).attr('hidden', null);
        const rect = this.getBoundingClientRect();
        const tip = tooltip.node().getBoundingClientRect();
        const x = event.type === 'focus' ? rect.right : event.clientX;
        const y = event.type === 'focus' ? rect.bottom : event.clientY;
        tooltip.style('left', `${Math.max(8, Math.min(x + 14, window.innerWidth - tip.width - 8))}px`)
          .style('top', `${Math.max(8, Math.min(y + 14, window.innerHeight - tip.height - 8))}px`);
      })
      .on('pointerleave.details blur.details', () => tooltip.attr('hidden', true));
    if (onSelect) marks.on('click.select', (_, d) => onSelect(d))
      .on('keydown.select', (event, d) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(d); }
      });
  }
  return {svg, reset, details, nullFill: `url(#${id}-null)`,
    destroy() { root.remove(); }};
}

export function countDetails(row) {
  const status = sampleStatus(row);
  return [
    `Late arrivals: ${number(row.late_count)} / ${number(row.arrival_eligible_count)} eligible flights (${percent(lateRate(row))})`,
    `Scheduled: ${number(row.scheduled_count)}`,
    `Cancelled: ${number(row.cancelled_count)} / ${number(row.scheduled_count)} scheduled (${percent(cancellationRate(row))})`,
    row.diverted_count != null ? `Diverted: ${number(row.diverted_count)} / ${number(row.scheduled_count)} scheduled (${percent(row.scheduled_count > 0 ? row.diverted_count / row.scheduled_count : null)})` : '',
    status === 'low_n' ? 'Small sample: fewer than 30 eligible arrivals. Interpret cautiously.' :
      status === 'no_flights' ? 'No scheduled flights in this selection.' :
      status === 'no_eligible_arrivals' ? 'Flights scheduled, but no eligible arrivals. Rate is missing, not 0%.' : '',
  ].filter(Boolean).join('\n');
}

export function rateLegend(svg, y, nullFill) {
  svg.append('text').attr('x', 28).attr('y', y).attr('font-weight', 650)
    .text('Late arrivals / eligible arrivals · shared 0-50%+ scale');
  svg.append('g').attr('class', 'rate-legend').selectAll('rect').data(range(100)).join('rect')
    .attr('x', d => 28 + d * 2.8).attr('y', y + 10).attr('width', 3).attr('height', 10)
    .attr('fill', d => rateColor(d / 99 * 0.5));
  for (const index of range(6)) {
    svg.append('text').attr('x', 28 + index * 56).attr('y', y + 36)
      .attr('text-anchor', index ? 'middle' : 'start')
      .text(index === 5 ? '50%+' : `${index * 10}%`);
  }
  const items = [
    {x: 352, fill: COLORS.empty, text: 'No flights'},
    {x: 493, fill: nullFill, text: 'No eligible arrivals'},
    {x: 711, fill: 'white', text: '<30 eligible flights', dash: '3 2'},
  ];
  for (const item of items) {
    svg.append('rect').attr('x', item.x).attr('y', y + 9).attr('width', 14).attr('height', 14)
      .attr('fill', item.fill).attr('stroke', '#536574').attr('stroke-dasharray', item.dash ?? null);
    svg.append('text').attr('x', item.x + 21).attr('y', y + 21).text(item.text);
  }
}

export function markFill(row, nullFill) {
  const status = sampleStatus(row);
  return status === 'no_flights' ? COLORS.empty : status === 'no_eligible_arrivals' ? nullFill : rateColor(lateRate(row));
}
