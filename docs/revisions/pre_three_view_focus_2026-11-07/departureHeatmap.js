import {scaleBand, range, axisBottom, axisLeft, brush} from 'd3';
import {chartSurface, countDetails, markFill, number, rateLegend, COLORS} from './common.js';
import {DAYS, cellKey, sampleStatus, sumCounts} from './metrics.js';

export function createDepartureHeatmap(container, initial) {
  const surface = chartSurface(container, 'Departure hour and weekday heatmap');
  const toolbar = document.createElement('div');
  toolbar.className = 'heatmap-toolbar';
  const brushButton = document.createElement('button');
  brushButton.type = 'button';
  brushButton.textContent = 'Brush time cells';
  const clearButton = document.createElement('button');
  clearButton.type = 'button';
  clearButton.className = 'clear-time-button';
  toolbar.append(brushButton, clearButton, 'Click cells to toggle; brush replaces the selected set.');
  if (initial.onBrush) container.prepend(toolbar);
  function update({cells, period, origin = 'ALL',
    selectedCells = /** @type {(readonly [number, number])[]} */ ([]),
    activeHour = /** @type {number | null} */ (null), onSelect, onBrush, animate = false}) {
    const {svg, nullFill} = surface;
    const previous = new Map();
    svg.selectAll('.cell').each(function(d) {
      previous.set(cellKey(d.weekday, d.hour), {fill: this.getAttribute('fill'),
        stroke: this.getAttribute('stroke'), width: this.getAttribute('stroke-width')});
    });
    const totals = sumCounts(cells);
    const selected = new Set(selectedCells.map(([day, hour]) => cellKey(day, hour)));
    clearButton.textContent = selected.size
      ? `Clear ${selected.size} selected cell${selected.size === 1 ? '' : 's'}` : 'Clear time selection';
    clearButton.disabled = selected.size === 0;
    clearButton.onclick = () => onBrush?.([]);
    surface.reset(460, 'When do late arrivals concentrate?',
      `${period} · ${origin === 'ALL' ? 'All origins' : origin} · ${number(totals.arrival_eligible_count)} eligible arrivals · Full time overview`,
      '02 / SCHEDULED DEPARTURE TIME');
    const x = scaleBand().domain(range(24)).range([80, 970]).padding(0.08);
    const y = scaleBand().domain(range(1, 8)).range([112, 322]).padding(0.08);
    svg.append('g').attr('class', 'axis').attr('transform', 'translate(0,328)')
      .call(axisBottom(x).tickFormat(d => String(d).padStart(2, '0')).tickSize(0)).call(g => g.select('.domain').remove());
    svg.append('g').attr('class', 'axis').attr('transform', 'translate(72,0)')
      .call(axisLeft(y).tickFormat(d => DAYS[d - 1]).tickSize(0)).call(g => g.select('.domain').remove());
    if (activeHour != null) svg.append('rect').attr('class', 'active-hour-column')
      .attr('x', x(activeHour) - 3).attr('y', 107).attr('width', x.bandwidth() + 6).attr('height', 220)
      .attr('fill', '#e7f4f3').attr('stroke', COLORS.selected).attr('stroke-width', 2)
      .style('pointer-events', 'none');
    const targetFill = d => markFill(d, nullFill);
    const targetStroke = d => selected.has(cellKey(d.weekday, d.hour)) ? COLORS.selected :
      sampleStatus(d) === 'low_n' ? '#536574' : '#d8e0e5';
    const targetWidth = d => selected.has(cellKey(d.weekday, d.hour)) ? 3 : 1;
    const marks = svg.append('g').selectAll('.cell').data(cells, d => cellKey(d.weekday, d.hour)).join('rect')
      .attr('class', 'mark cell').attr('data-cell', d => cellKey(d.weekday, d.hour)).attr('data-status', sampleStatus)
      .attr('x', d => x(d.hour)).attr('y', d => y(d.weekday))
      .attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 2)
      .attr('fill', d => animate ? previous.get(cellKey(d.weekday, d.hour))?.fill ?? targetFill(d) : targetFill(d))
      .attr('stroke', d => animate ? previous.get(cellKey(d.weekday, d.hour))?.stroke ?? targetStroke(d) : targetStroke(d))
      .attr('stroke-width', d => animate ? previous.get(cellKey(d.weekday, d.hour))?.width ?? targetWidth(d) : targetWidth(d))
      .attr('stroke-dasharray', d => sampleStatus(d) === 'low_n' && !selected.has(cellKey(d.weekday, d.hour)) ? '3 2' : null)
      .attr('aria-pressed', d => onSelect ? String(selected.has(cellKey(d.weekday, d.hour))) : null);
    if (animate && previous.size) marks.transition().duration(300)
      .attr('fill', targetFill).attr('stroke', targetStroke).attr('stroke-width', targetWidth);
    else if (animate) marks.attr('opacity', 0.2).transition().duration(300).attr('opacity', 1);
    surface.details(marks, d => `${DAYS[d.weekday - 1]} ${String(d.hour).padStart(2, '0')}:00–${String(d.hour).padStart(2, '0')}:59\n${countDetails(d)}`, onSelect);
    if (onBrush) {
      const layer = svg.append('g').attr('class', 'time-brush').style('display', 'none');
      const behavior = brush().extent([[80, 112], [970, 322]]).on('end', event => {
        if (!event.sourceEvent || !event.selection) return;
        const [[x0, y0], [x1, y1]] = event.selection;
        const chosen = cells.filter(d => {
          const cx = x(d.hour) + x.bandwidth() / 2;
          const cy = y(d.weekday) + y.bandwidth() / 2;
          return cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1;
        }).map(d => [d.weekday, d.hour]);
        onBrush(chosen);
        layer.call(behavior.move, null);
        layer.style('display', 'none');
        brushButton.textContent = 'Brush time cells';
      });
      layer.call(behavior);
      brushButton.onclick = () => {
        const active = layer.style('display') === 'none';
        layer.style('display', active ? null : 'none');
        brushButton.textContent = active ? 'Cancel brush' : 'Brush time cells';
      };
    }
    svg.append('text').attr('x', 525).attr('y', 362).attr('text-anchor', 'middle').attr('class', 'muted')
      .text('Scheduled departure hour at origin (local time)');
    rateLegend(svg, 391, nullFill);
    svg.append('text').attr('x', 28).attr('y', 448).attr('class', 'muted')
      .text(`${cells.filter(d => sampleStatus(d) === 'low_n').length} cells with fewer than 30 eligible flights · ${activeHour == null ? 'Pink outline = selected time cells.' : 'Pink column = playback hour.'}`);
  }
  update(initial);
  return {update, destroy() {surface.destroy(); toolbar.remove();}};
}
