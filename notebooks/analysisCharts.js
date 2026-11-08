// Exploratory notebook figures only; these are not additional dashboard features.
import {scaleBand, scalePoint, scaleLinear, scaleLog, axisBottom, axisLeft, line, max, extent, group, format} from 'd3';
import {chartSurface, number, percent} from '../frontend/src/charts/common.js';

export function drawHistogram(container, {rows, title, subtitle, xLabel}) {
  const surface = chartSurface(container, title);
  surface.reset(490, title, subtitle, 'EXPLORATION / DISTRIBUTION');
  const {svg} = surface;
  const x = scaleBand().domain(rows.map(d => d.label)).range([95, 960]).padding(0.16);
  const y = scaleLinear().domain([0, max(rows, d => d.count) || 1]).nice().range([370, 115]);
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(95,0)').call(axisLeft(y).ticks(5).tickFormat(format('~s')));
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(0,370)').call(axisBottom(x));
  const bars = svg.selectAll('.bin').data(rows).join('rect').attr('class', 'mark bin')
    .attr('x', d => x(d.label)).attr('y', d => y(d.count)).attr('width', x.bandwidth())
    .attr('height', d => y(0) - y(d.count)).attr('fill', '#188c91');
  surface.details(bars, d => `${d.label}\nFlights: ${number(d.count)}`);
  svg.append('text').attr('x', 95).attr('y', 101).text('Flights (count)');
  svg.append('text').attr('x', 520).attr('y', 421).attr('text-anchor', 'middle').text(xLabel);
  svg.append('text').attr('x', 28).attr('y', 465).attr('class', 'muted')
    .text('Equal-width bars represent labelled intervals; bin widths differ, so bar height is count, not density.');
  return surface;
}

export function drawRateLines(container, {rows, title, subtitle, xLabel}) {
  const surface = chartSurface(container, title);
  surface.reset(505, title, subtitle, 'EXPLORATION / CONDITIONAL RATES');
  const {svg} = surface;
  const x = scalePoint().domain([...new Set(rows.map(d => d.x))]).range([95, 950]).padding(0.25);
  const y = scaleLinear().domain([0, 1]).range([375, 140]);
  const colors = ['#007f87', '#bb5939', '#6859a5', '#417a44'];
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(95,0)').call(axisLeft(y).ticks(5).tickFormat(format('.0%')));
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(0,375)').call(axisBottom(x));
  const series = [...group(rows, d => d.series)];
  series.forEach(([name, points], i) => {
    const color = colors[i % colors.length];
    svg.append('text').attr('x', 95 + i * 205).attr('y', 112).style('fill', color).text(name);
    svg.append('path').datum(points).attr('fill', 'none').attr('stroke', color).attr('stroke-width', 2)
      .attr('d', line().defined(d => d.y != null && d.n >= 30).x(d => x(d.x)).y(d => y(d.y)));
    const dots = svg.append('g').selectAll('circle').data(points.filter(d => d.y != null)).join('circle')
      .attr('class', 'mark rate-point').attr('cx', d => x(d.x)).attr('cy', d => y(d.y)).attr('r', 4)
      .attr('fill', d => d.n < 30 ? 'white' : color).attr('stroke', color)
      .attr('stroke-dasharray', d => d.n < 30 ? '2 1' : null).attr('data-n', d => d.n);
    surface.details(dots, d => `${name} / ${d.x}\n${d.details ?? ''}\nRate: ${percent(d.y)}; denominator n = ${number(d.n)}${d.n < 30 ? '\nSmall sample: interpret cautiously.' : ''}`);
  });
  svg.append('text').attr('x', 520).attr('y', 422).attr('text-anchor', 'middle').text(xLabel);
  svg.append('text').attr('x', 28).attr('y', 458).attr('class', 'muted')
    .text('Rates divide summed numerators by summed denominators. Compare the accompanying count table.');
  svg.append('text').attr('x', 28).attr('y', 483).attr('class', 'muted')
    .text('Hollow points: n < 30. Lines break at sparse or missing points. Associations do not establish causes.');
  return surface;
}

export function drawAirportScatter(container, {rows, title, subtitle}) {
  const surface = chartSurface(container, title);
  surface.reset(505, title, subtitle, 'EXPLORATION / VOLUME AND RATE');
  const {svg} = surface;
  const valid = rows.filter(d => d.x > 0 && d.y != null);
  const bounds = extent(valid, d => d.x);
  const x = scaleLog().domain(bounds[0] === bounds[1] ? [1, (bounds[1] || 1) * 10] : bounds).nice().range([95, 950]);
  const y = scaleLinear().domain([0, 1]).range([375, 115]);
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(95,0)').call(axisLeft(y).ticks(5).tickFormat(format('.0%')));
  svg.append('g').attr('class', 'axis').attr('transform', 'translate(0,375)').call(axisBottom(x).ticks(5, ',d'));
  const dots = svg.selectAll('.airport-scatter').data(valid).join('circle').attr('class', 'mark airport-scatter')
    .attr('cx', d => x(d.x)).attr('cy', d => y(d.y)).attr('r', 4)
    .attr('fill', d => d.n < 30 ? 'white' : '#188c91').attr('fill-opacity', 0.65)
    .attr('stroke', '#142d40').attr('stroke-dasharray', d => d.n < 30 ? '2 1' : null);
  surface.details(dots, d => `${d.label}\nScheduled: ${number(d.x)}\nLate rate: ${percent(d.y)}; eligible n = ${number(d.n)}${d.n < 30 ? '\nSmall sample: interpret cautiously.' : ''}`);
  svg.append('text').attr('x', 95).attr('y', 101).text('Late-arrival rate');
  svg.append('text').attr('x', 520).attr('y', 422).attr('text-anchor', 'middle').text('Scheduled flights at origin (logarithmic scale)');
  svg.append('text').attr('x', 28).attr('y', 460).attr('class', 'muted')
    .text('Each point is an airport aggregate, not an individual flight. Hollow points have fewer than 30 eligible arrivals.');
  svg.append('text').attr('x', 28).attr('y', 484).attr('class', 'muted')
    .text('Volume, carrier mix and routes vary together; this plot does not isolate an airport-size effect.');
  return surface;
}

export function drawAirportComparison(container, {rows, title, subtitle}) {
  const surface = chartSurface(container, title);
  surface.reset(680, title, subtitle, 'EXPLORATION / NAMED AIRPORTS');
  const {svg} = surface;
  const top = 130;
  const rowHeight = 30;
  const volume = scaleLinear().domain([0, max(rows, d => d.scheduled_count) || 1]).range([320, 570]);
  const largestRate = max(rows, d => d.arrival_eligible_count ? d.late_count / d.arrival_eligible_count : 0) || 0;
  const rateMax = Math.max(0.1, Math.ceil(largestRate * 10) / 10);
  const rate = scaleLinear().domain([0, rateMax]).range([685, 930]);
  svg.append('text').attr('x', 320).attr('y', 107).attr('font-weight', 650).text('Scheduled flights');
  svg.append('text').attr('x', 685).attr('y', 107).attr('font-weight', 650).text('Late arrivals / eligible flights');
  const groups = svg.selectAll('.airport-comparison-row').data(rows).join('g')
    .attr('class', 'airport-comparison-row')
    .attr('transform', (_, i) => `translate(0,${top + i * rowHeight})`);
  groups.append('text').attr('x', 305).attr('y', 16).attr('text-anchor', 'end')
    .text(d => `${d.origin_code} · ${d.name}`);
  groups.append('rect').attr('x', volume(0)).attr('y', 1).attr('height', 21)
    .attr('width', d => volume(d.scheduled_count) - volume(0)).attr('fill', '#739caa');
  groups.append('rect').attr('x', rate(0)).attr('y', 1).attr('height', 21)
    .attr('width', d => d.arrival_eligible_count ?
      rate(d.late_count / d.arrival_eligible_count) - rate(0) : 0).attr('fill', '#c76a42');
  const hit = groups.append('rect').datum(d => d).attr('class', 'mark airport-comparison-detail')
    .attr('x', 25).attr('y', -2).attr('width', 935).attr('height', 27)
    .attr('fill', 'transparent').attr('stroke', 'none');
  surface.details(hit, d => `${d.name} (${d.origin_code})\nScheduled flights: ${number(d.scheduled_count)}\nLate arrivals: ${number(d.late_count)}\nEligible flights: ${number(d.arrival_eligible_count)}\nLate-arrival rate: ${d.arrival_eligible_count ? percent(d.late_count / d.arrival_eligible_count) : 'Unavailable'}`);
  const axisY = top + rows.length * rowHeight + 6;
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${axisY})`)
    .call(axisBottom(volume).ticks(4).tickFormat(format('~s')));
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${axisY})`)
    .call(axisBottom(rate).ticks(4).tickFormat(format('.0%')));
  svg.append('text').attr('x', 28).attr('y', axisY + 57).attr('class', 'muted')
    .text('The busiest origins only; this view compares named airports and does not represent every airport.');
  return surface;
}
