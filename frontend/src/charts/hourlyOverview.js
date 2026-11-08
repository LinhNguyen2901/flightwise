import {axisBottom, axisLeft, axisRight, line, max, range, scaleBand, scaleLinear} from 'd3';
import {chartSurface, countDetails, number, percent, COLORS} from './common.js';
import {lateRate, sumCounts} from './metrics.js';

const volumeColor = '#b5d8d5';
const rateLineColor = '#007f87';

export function createHourlyOverview(container, initial) {
  const surface = chartSurface(container, 'Scheduled flights and arrival-late rate by local hour');

  function update({rows, period, origin = 'ALL'}) {
    const {svg} = surface;
    const byHour = new Map(rows.map(row => [Number(row.hour), row]));
    const hours = range(24).map(hour => byHour.get(hour) ?? {
      hour, scheduled_count: 0, arrival_eligible_count: 0, late_count: 0,
      cancelled_count: 0, cancellation_eligible_count: 0,
    });
    const total = sumCounts(hours);
    const flightShare = row => total.scheduled_count ? row.scheduled_count / total.scheduled_count : 0;

    surface.reset(590, 'How do flights and late arrivals vary by hour?',
      `${period} · ${origin === 'ALL' ? 'All origins' : origin} · ${number(total.scheduled_count)} scheduled flights`,
      'ONE SHARED LOCAL-HOUR PLOT');

    const left = 92;
    const right = 908;
    const top = 160;
    const bottom = 490;
    const x = scaleBand().domain(range(24)).range([left, right]).padding(0.18);
    const shareTop = Math.max(0.01, (max(hours, flightShare) ?? 0) * 1.12);
    const rateTop = Math.max(0.05, (max(hours, row => lateRate(row) ?? 0) ?? 0) * 1.12);
    const yShare = scaleLinear().domain([0, shareTop]).nice(5).range([bottom, top]);
    const yRate = scaleLinear().domain([0, rateTop]).nice(5).range([bottom, top]);

    svg.append('rect').attr('x', left).attr('y', 105).attr('width', 16).attr('height', 14)
      .attr('fill', volumeColor);
    svg.append('text').attr('x', left + 23).attr('y', 117)
      .text('Bars: share of all scheduled flights (left axis)');
    svg.append('line').attr('x1', 490).attr('x2', 512).attr('y1', 112).attr('y2', 112)
      .attr('stroke', rateLineColor).attr('stroke-width', 3);
    svg.append('circle').attr('cx', 501).attr('cy', 112).attr('r', 4).attr('fill', rateLineColor);
    svg.append('text').attr('x', 520).attr('y', 117)
      .text('Line: late arrivals / eligible flights (right axis)');

    svg.append('g').attr('class', 'grid').attr('transform', `translate(${left},0)`)
      .call(axisLeft(yShare).ticks(5).tickSize(-(right - left)).tickFormat(''));
    svg.append('g').attr('class', 'axis share-axis').attr('transform', `translate(${left},0)`)
      .call(axisLeft(yShare).ticks(5).tickFormat(value => `${Math.round(value * 100)}%`));
    svg.append('g').attr('class', 'axis rate-axis').attr('transform', `translate(${right},0)`)
      .call(axisRight(yRate).ticks(5).tickFormat(value => `${Math.round(value * 100)}%`));
    svg.append('text').attr('class', 'muted').attr('text-anchor', 'middle')
      .attr('transform', `translate(25,${(top + bottom) / 2}) rotate(-90)`)
      .text('Scheduled-flight share (%)');
    svg.append('text').attr('text-anchor', 'middle')
      .attr('transform', `translate(977,${(top + bottom) / 2}) rotate(90)`)
      .attr('fill', rateLineColor).text('Arrival-late rate (%)');

    const bars = svg.append('g').selectAll('.hour-bar').data(hours).join('rect')
      .attr('class', 'mark hour-bar').attr('x', row => x(row.hour))
      .attr('y', row => yShare(flightShare(row)))
      .attr('width', x.bandwidth()).attr('height', row => bottom - yShare(flightShare(row)))
      .attr('fill', volumeColor);
    surface.details(bars, row => `${String(row.hour).padStart(2, '0')}:00-${String(row.hour).padStart(2, '0')}:59\n${number(row.scheduled_count)} scheduled flights (${percent(flightShare(row))} of period total)`);

    const path = line().defined(row => lateRate(row) != null)
      .x(row => x(row.hour) + x.bandwidth() / 2).y(row => yRate(lateRate(row)));
    svg.append('path').datum(hours).attr('d', path).attr('fill', 'none')
      .attr('stroke', 'white').attr('stroke-width', 6);
    svg.append('path').datum(hours).attr('d', path).attr('fill', 'none')
      .attr('stroke', rateLineColor).attr('stroke-width', 3);
    const observed = hours.filter(row => lateRate(row) != null);
    const points = svg.append('g').selectAll('.hour-rate').data(observed).join('circle')
      .attr('class', 'mark hour-rate').attr('cx', row => x(row.hour) + x.bandwidth() / 2)
      .attr('cy', row => yRate(lateRate(row))).attr('r', 5)
      .attr('data-status', row => row.arrival_eligible_count < 30 ? 'small-sample' : 'observed')
      .attr('fill', row => row.arrival_eligible_count < 30 ? 'white' : rateLineColor)
      .attr('stroke', rateLineColor).attr('stroke-width', 2);
    surface.details(points, row => `${String(row.hour).padStart(2, '0')}:00-${String(row.hour).padStart(2, '0')}:59\n${countDetails(row)}`);

    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${bottom})`)
      .call(axisBottom(x).tickFormat(hour => String(hour).padStart(2, '0')).tickSize(0))
      .call(group => group.select('.domain').remove());
    svg.append('text').attr('x', 500).attr('y', 530).attr('text-anchor', 'middle').attr('class', 'muted')
      .text('Scheduled departure hour at origin (local time)');
    const sparse = hours.filter(row => row.scheduled_count > 0 && row.arrival_eligible_count < 30).length;
    svg.append('text').attr('x', left).attr('y', 567).attr('class', 'muted')
      .text(`${sparse} ${sparse === 1 ? 'hour has' : 'hours have'} fewer than 30 eligible arrivals (hollow point). Gaps mean no eligible arrivals.`);
  }

  update(initial);
  return {update, destroy: surface.destroy};
}
