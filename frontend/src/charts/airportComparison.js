import {axisBottom, axisLeft, axisRight, line, max, range, scaleBand, scaleLinear} from 'd3';
import {chartSurface, countDetails, number, percent} from './common.js';
import {lateRate, sumCounts} from './metrics.js';

const volumeColor = '#b5d8d5';
const rateColor = '#007f87';

// Both panels use the same share and late-rate axes for direct comparison.
export function createAirportComparison(container, initial) {
  const surface = chartSurface(container, 'Two airport late-arrival profiles by local departure hour');

  function update({airports, period}) {
    const profiles = airports.map(airport => {
      const byHour = new Map(airport.rows.map(row => [Number(row.hour), row]));
      const hours = range(24).map(hour => byHour.get(hour) ?? {
        hour, scheduled_count: 0, cancelled_count: 0, diverted_count: 0,
        cancellation_eligible_count: 0, arrival_eligible_count: 0, late_count: 0,
      });
      return {...airport, hours, total: sumCounts(hours)};
    });
    const share = (row, total) => total ? row.scheduled_count / total : 0;
    const highestShare = max(profiles.flatMap(profile =>
      profile.hours.map(row => share(row, profile.total.scheduled_count)))) ?? 0;
    const highestRate = max(profiles.flatMap(profile => profile.hours), row => lateRate(row) ?? 0) ?? 0;
    const yShare = scaleLinear().domain([0, Math.max(0.01, highestShare * 1.12)])
      .nice(5).range([400, 175]);
    const yRate = scaleLinear().domain([0, Math.max(0.05, highestRate * 1.12)])
      .nice(5).range([400, 175]);

    surface.reset(540, 'How do these airports differ by departure hour?',
      `${period} · all weekdays · shared share and late-rate axes`, '', false);
    const {svg} = surface;
    svg.append('rect').attr('x', 28).attr('y', 82).attr('width', 16).attr('height', 14)
      .attr('fill', volumeColor);
    svg.append('text').attr('x', 52).attr('y', 94)
      .text('Bars: share of that airport’s scheduled flights (left axes)');
    svg.append('line').attr('x1', 570).attr('x2', 592).attr('y1', 89).attr('y2', 89)
      .attr('stroke', rateColor).attr('stroke-width', 3);
    svg.append('circle').attr('cx', 581).attr('cy', 89).attr('r', 4).attr('fill', rateColor);
    svg.append('text').attr('x', 602).attr('y', 94)
      .text('Line: late arrivals / eligible flights (right axes)');

    profiles.forEach((profile, index) => {
      const left = index === 0 ? 48 : 538;
      const plotLeft = left + 45;
      const plotRight = left + 405;
      const x = scaleBand().domain(range(24)).range([plotLeft, plotRight]).padding(0.18);
      svg.append('text').attr('x', left).attr('y', 130).attr('font-size', 17)
        .attr('font-weight', 700).text(`${index === 0 ? 'Pinned' : 'Current'}: ${profile.code} · ${profile.name}`);
      svg.append('text').attr('class', 'muted').attr('text-anchor', 'middle')
        .attr('transform', `translate(${plotLeft - 42},287) rotate(-90)`)
        .text('Scheduled-flight share (%)');
      svg.append('text').attr('text-anchor', 'middle')
        .attr('transform', `translate(${plotRight + 30},287) rotate(90)`)
        .attr('fill', rateColor).text('Late-arrival rate (%)');
      svg.append('text').attr('x', (plotLeft + plotRight) / 2).attr('y', 448)
        .attr('text-anchor', 'middle').attr('class', 'muted')
        .text('Scheduled departure hour (local time)');
      svg.append('text').attr('x', left).attr('y', 475).attr('class', 'muted')
        .text(`${number(profile.total.scheduled_count)} scheduled · ${number(profile.total.arrival_eligible_count)} eligible arrivals`);
      svg.append('g').attr('class', 'grid').attr('transform', `translate(${plotLeft},0)`)
        .call(axisLeft(yShare).ticks(5).tickSize(-(plotRight - plotLeft)).tickFormat(''));
      svg.append('g').attr('class', 'axis share-axis').attr('transform', `translate(${plotLeft},0)`)
        .call(axisLeft(yShare).ticks(5).tickFormat(value => `${Math.round(value * 100)}%`));
      svg.append('g').attr('class', 'axis rate-axis').attr('transform', `translate(${plotRight},0)`)
        .call(axisRight(yRate).ticks(5).tickFormat(value => `${Math.round(value * 100)}%`));
      svg.append('g').attr('class', 'axis').attr('transform', 'translate(0,400)')
        .call(axisBottom(x).tickValues([0, 4, 8, 12, 16, 20, 23])
          .tickFormat(hour => String(hour).padStart(2, '0')));

      const bars = svg.append('g').selectAll('rect').data(profile.hours).join('rect')
        .attr('class', 'mark hour-bar').attr('x', row => x(row.hour))
        .attr('y', row => yShare(share(row, profile.total.scheduled_count)))
        .attr('width', x.bandwidth())
        .attr('height', row => 400 - yShare(share(row, profile.total.scheduled_count)))
        .attr('fill', volumeColor);
      surface.details(bars, row => `${profile.code} · ${String(row.hour).padStart(2, '0')}:00-${String(row.hour).padStart(2, '0')}:59\n${number(row.scheduled_count)} scheduled flights (${percent(share(row, profile.total.scheduled_count))} of ${profile.code} total)`);

      const path = line().defined(row => lateRate(row) !== null)
        .x(row => x(row.hour) + x.bandwidth() / 2).y(row => yRate(lateRate(row)));
      svg.append('path').datum(profile.hours).attr('d', path)
        .attr('fill', 'none').attr('stroke', 'white').attr('stroke-width', 6);
      svg.append('path').datum(profile.hours).attr('d', path)
        .attr('fill', 'none').attr('stroke', rateColor).attr('stroke-width', 3);
      const points = svg.append('g').selectAll('circle').data(profile.hours.filter(row => lateRate(row) !== null))
        .join('circle').attr('class', 'mark hour-rate')
        .attr('cx', row => x(row.hour) + x.bandwidth() / 2).attr('cy', row => yRate(lateRate(row)))
        .attr('r', 4).attr('fill', row => row.arrival_eligible_count < 30 ? 'white' : rateColor)
        .attr('stroke', rateColor).attr('stroke-width', 2);
      surface.details(points, row => `${profile.code} · ${String(row.hour).padStart(2, '0')}:00-${String(row.hour).padStart(2, '0')}:59\n${countDetails(row)}`);
    });
    svg.append('text').attr('x', 500).attr('y', 515).attr('text-anchor', 'middle')
      .attr('class', 'muted').text('Both panels use the same axes · Hollow points: fewer than 30 eligible arrivals · Gaps: no eligible arrivals');
  }

  update(initial);
  return {update, destroy: surface.destroy};
}
