import {scaleLinear, axisBottom, range, select} from 'd3';
import {chartSurface, countDetails, number, rateColor, rateLegend} from './common.js';
import {lateRate, sampleStatus, sumCounts} from './metrics.js';
import {airlineName} from './airlineNames.js';

export function createAirlineBars(container, initial) {
  const surface = chartSurface(container, 'Airline comparison');

  function update({rows, period, origin = 'ALL', selectionLabel = 'All valid times',
    stableOrder = false, animate = false}) {
    const {svg, nullFill} = surface;
    const previous = new Map();
    svg.selectAll('.carrier-row').each(function(code) {
      const bar = select(this).select('.rate-bar').node();
      previous.set(code, {position: this.getAttribute('transform'),
        width: bar ? Number(bar.getAttribute('width')) : 0,
        fill: bar?.getAttribute('fill')});
    });
    const byAirline = new Map(rows.map(row => [row.carrier, row]));
    const codes = rows.map(row => row.carrier);
    const order = stableOrder ? [...codes] : [...codes].sort((a, b) => {
      const aRate = byAirline.has(a) ? lateRate(byAirline.get(a)) : null;
      const bRate = byAirline.has(b) ? lateRate(byAirline.get(b)) : null;
      if (aRate == null && bRate != null) return 1;
      if (bRate == null && aRate != null) return -1;
      return (bRate ?? 0) - (aRate ?? 0) || airlineName(a).localeCompare(airlineName(b));
    });
    const totals = sumCounts(rows);
    const rowGap = 23;
    const bottom = 123 + order.length * rowGap;
    surface.reset(bottom + 140, 'How do airlines compare?',
      `${period} · ${origin === 'ALL' ? 'All origins' : origin} · ${selectionLabel} · ${number(totals.arrival_eligible_count)} eligible flights`,
      '', false);

    const x = scaleLinear().domain([0, 1]).range([240, 970]);
    svg.append('g').attr('class', 'grid').attr('transform', `translate(0,${bottom})`)
      .call(axisBottom(x).tickValues(range(0, 1.01, 0.2)).tickFormat(() => '').tickSize(-(bottom - 110)));

    const position = (_, i) => `translate(0,${119 + i * rowGap})`;
    const groups = svg.append('g').selectAll('.carrier-row').data(order).join('g')
      .attr('class', 'carrier-row').attr('data-carrier', code => code)
      .attr('transform', position);
    groups.each(function(code) {
      const row = byAirline.get(code);
      const group = select(this);
      group.append('text').attr('x', 225).attr('y', 15).attr('text-anchor', 'end')
        .attr('font-weight', 650).text(airlineName(code));
      if (!row || !row.scheduled_count) {
        group.append('text').attr('x', 250).attr('y', 15).attr('class', 'muted').text('No flights in selection');
        return;
      }
      const rate = lateRate(row);
      const status = sampleStatus(row);
      group.append('rect').attr('class', 'rate-bar').attr('x', x(0)).attr('y', 1)
        .attr('width', rate == null ? 18 : x(rate) - x(0)).attr('height', 19).attr('rx', 2)
        .attr('fill', rate == null ? nullFill : rateColor(rate))
        .attr('stroke', status === 'low_n' ? '#536574' : 'none')
        .attr('stroke-dasharray', status === 'low_n' ? '3 2' : null);
      if (rate === 0) group.append('line').attr('x1', x(0)).attr('x2', x(0))
        .attr('y1', 1).attr('y2', 20).attr('stroke', '#536574').attr('stroke-width', 2);
      if (rate == null) group.append('text').attr('x', 266).attr('y', 15)
        .attr('class', 'muted').text('No eligible arrivals');
      if (status === 'low_n') group.append('text').attr('x', 980).attr('y', 15)
        .attr('font-weight', 700).text('*');
      const target = group.append('rect').datum(row).attr('class', 'mark bar-detail')
        .attr('data-status', status).attr('x', 24).attr('y', -2)
        .attr('width', 960).attr('height', 23).attr('fill', 'transparent').attr('stroke', 'none');
      surface.details(target, flight => `${airlineName(code)} (${code})\n${countDetails(flight)}`);
    });

    if (animate) {
      groups.attr('transform', (code, i) => previous.get(code)?.position ?? position(code, i))
        .transition().duration(300).attr('transform', position);
      groups.selectAll('.rate-bar').each(function(code) {
        const bar = select(this);
        const width = Number(bar.attr('width'));
        const fill = bar.attr('fill');
        const old = previous.get(code);
        bar.attr('width', old?.width ?? 0);
        if (old?.fill?.startsWith('#') && fill.startsWith('#')) bar.attr('fill', old.fill);
        bar.transition().duration(300).attr('width', width).attr('fill', fill);
      });
    }

    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${bottom})`)
      .call(axisBottom(x).tickValues(range(0, 1.01, 0.2)).tickFormat(value => `${Math.round(value * 100)}%`));
    svg.append('text').attr('x', 595).attr('y', bottom + 35).attr('text-anchor', 'middle')
      .attr('class', 'muted').text('Late arrivals / eligible flights');
    rateLegend(svg, bottom + 50, nullFill);
    const message = !totals.scheduled_count ? 'No flights in this selection. Clear time or choose another airport.' :
      rows.filter(row => row.scheduled_count > 0).length === 1 ?
      'One airline in this selection; no comparison is possible.' : '';
    if (message) svg.append('text').attr('x', 28).attr('y', bottom + 105).attr('font-weight', 600).text(message);
    svg.append('text').attr('x', 28).attr('y', bottom + 125).attr('class', 'muted')
      .text('* Fewer than 30 eligible flights: interpret cautiously. Hover or focus a row for exact rates and counts.');
  }

  update(initial);
  return {update, destroy: surface.destroy};
}
