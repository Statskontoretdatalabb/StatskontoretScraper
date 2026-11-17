import {App, applyDocumentTheme, applyHostStyleVariables} from '@modelcontextprotocol/ext-apps';

const app = new App({name: 'Myndighetsnyckeltal', version: '1.0.0'});
const colors = ['#006b63', '#a84326', '#3656a8', '#855295', '#876100', '#0084a0', '#94405c', '#536d2d', '#6155a5', '#795744'];
const number = new Intl.NumberFormat('sv-SE', {maximumFractionDigits: 3});
const svgNS = 'http://www.w3.org/2000/svg';
const $ = id => document.getElementById(id);
let current;
const hidden = new Set();

function element(tag, text, parent) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (parent) parent.append(node);
  return node;
}
function shape(tag, attrs, parent, text) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  parent.append(node);
  return node;
}
function render(data) {
  current = data;
  $('status').hidden = true;
  $('content').hidden = false;
  $('title').textContent = data.metric;
  $('subtitle').textContent = `${data.years[0]}–${data.years.at(-1)} · ${data.denominator === 'Ingen' ? 'Källvärde' : 'Per ' + data.denominator.toLocaleLowerCase('sv')}`;
  $('note').textContent = `Testdata. ${data.note}`;
  $('legend').replaceChildren();
  data.series.forEach((series, index) => {
    const label = element('label', undefined, $('legend'));
    const input = element('input', undefined, label);
    input.type = 'checkbox'; input.checked = !hidden.has(index);
    input.style.accentColor = colors[index];
    element('span', series.myndighet, label);
    input.addEventListener('change', () => {
      if (input.checked) hidden.delete(index); else hidden.add(index);
      draw();
    });
  });
  const table = $('values'); table.replaceChildren();
  const head = element('thead', undefined, table), header = element('tr', undefined, head);
  element('th', 'Myndighet', header).scope = 'col';
  data.years.forEach(year => {element('th', String(year), header).scope = 'col';});
  const body = element('tbody', undefined, table);
  data.series.forEach(series => {
    const row = element('tr', undefined, body);
    element('th', series.myndighet, row).scope = 'row';
    series.values.forEach(value => element('td', value == null ? 'Saknas' : number.format(value), row));
  });
  $('source').textContent = `Datasetrevision ${data.dataset.revision.slice(0, 12)}`;
  draw();
}
function draw() {
  const data = current, svg = $('chart'); svg.replaceChildren();
  const width = Math.max(380, svg.clientWidth || 760), height = 310;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  shape('title', {}, svg, `${data.metric}, ${data.years[0]} till ${data.years.at(-1)}. Fullständiga värden finns i tabellen.`);
  const selected = data.series.map((s, index) => ({...s, index})).filter(s => !hidden.has(s.index));
  const values = selected.flatMap(s => s.values).filter(v => v != null);
  if (!values.length) {
    shape('text', {x: width / 2, y: 145, 'text-anchor': 'middle', fill: 'currentColor'}, svg, selected.length ? 'Inga värden för det valda intervallet.' : 'Välj minst en myndighet i teckenförklaringen.');
    return;
  }
  let low = Math.min(0, ...values), high = Math.max(0, ...values);
  if (high === low) high = low + 1;
  const left = width < 500 ? 74 : 98, right = width - 22, top = 18, bottom = 270;
  const x = i => data.years.length === 1 ? (left + right) / 2 : left + i * (right - left) / (data.years.length - 1);
  const y = value => bottom - (value - low) / (high - low) * (bottom - top);
  const compact = new Intl.NumberFormat('sv-SE', {notation: 'compact', maximumFractionDigits: 1});
  for (let i = 0; i <= 4; i++) {
    const value = low + (high - low) * i / 4, position = y(value);
    shape('line', {x1: left, x2: right, y1: position, y2: position, stroke: 'currentColor', opacity: .14}, svg);
    shape('text', {x: left - 12, y: position + 4, 'text-anchor': 'end', fill: 'currentColor', 'font-size': 12}, svg, compact.format(value));
  }
  data.years.forEach((year, i) => shape('text', {x: x(i), y: bottom + 26, 'text-anchor': 'middle', fill: 'currentColor', 'font-size': 12}, svg, year));
  selected.forEach(series => {
    let path = '', connected = false;
    series.values.forEach((value, i) => {
      if (value == null) {connected = false; return;}
      path += `${connected ? 'L' : 'M'}${x(i)},${y(value)} `; connected = true;
    });
    shape('path', {d: path, fill: 'none', stroke: colors[series.index], 'stroke-width': 2.5}, svg);
    series.values.forEach((value, i) => {
      if (value == null) return;
      const point = shape('circle', {cx: x(i), cy: y(value), r: 4, fill: colors[series.index], tabindex: 0, role: 'img', 'aria-label': `${series.myndighet}, ${data.years[i]}: ${number.format(value)}`}, svg);
      shape('title', {}, point, `${series.myndighet}\n${data.years[i]}: ${number.format(value)}`);
      const label = () => {$('hover').textContent = `${series.myndighet} · ${data.years[i]} · ${number.format(value)}`;};
      point.addEventListener('focus', label); point.addEventListener('pointerenter', label);
    });
  });
}
function fail(message) {$('status').textContent = message; $('status').hidden = false;}
app.ontoolresult = result => {
  if (result.isError) {fail('Uppgifterna kunde inte hämtas. Be assistenten kontrollera myndigheter, mått och år.');return;}
  try {
    const text = result.content?.find(c => c.type === 'text')?.text;
    const data = result.structuredContent?.series ? result.structuredContent : JSON.parse(text);
    hidden.clear(); render(data);
  } catch {fail('Svaret innehåller inga läsbara årsserier. Be assistenten anropa show_comparison igen.');}
};
app.onhostcontextchanged = context => {
  if (context.theme) applyDocumentTheme(context.theme);
  if (context.styles?.variables) applyHostStyleVariables(context.styles.variables);
};
app.ontoolcancelled = () => fail('Anropet avbröts. Be assistenten försöka igen.');
app.onerror = () => fail('Anslutningen till chatten misslyckades. Be assistenten försöka igen.');
new ResizeObserver(() => {if (current) draw();}).observe($('chart'));
app.connect().catch(() => fail('Öppna diagrammet genom show_comparison i en chatt som stöder MCP Apps.'));
