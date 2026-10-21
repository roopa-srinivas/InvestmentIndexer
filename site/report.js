// Displays site/data.json, written by `python -m indexer export`.
// All the numbers are computed in Python; this file only sorts and draws.

const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)'];
const MARKET_COLOR = 'var(--ink)';
const MAX_PICKS = 4;
const MEASURES = {
  cagr: { label: 'growth per year', format: (v) => pct(v), better: 'high' },
  sharpe: { label: 'Sharpe ratio', format: (v) => v.toFixed(2), better: 'high' },
  max_drawdown: { label: 'worst drop', format: (v) => pct(v, 0), better: 'high' },
  volatility: { label: 'volatility', format: (v) => pct(v), better: 'low' },
};

const $ = (id) => document.getElementById(id);
const pct = (v, digits = 1) => `${(v * 100).toFixed(digits)}%`;
const money = (v) => (v >= 100 ? `$${Math.round(v).toLocaleString()}` : `$${v.toFixed(2)}`);
const state = { years: '15', by: 'cagr', group: 'all', picks: [], sort: { key: 'rank', dir: 1 } };
let data, byId;

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

// Rows for the current window and group, ranked by the chosen measure.
function ranked() {
  const rows = data.windows[state.years].rows
    .map((r) => ({ ...r, ...byId[r.id] }))
    .filter((r) => state.group === 'all' || r.group === state.group || r.id === 'market');
  const dir = MEASURES[state.by].better === 'low' ? 1 : -1;
  rows.sort((a, b) => (a[state.by] - b[state.by]) * dir);
  rows.forEach((r, i) => (r.rank = i + 1));
  return rows;
}

function renderTiles(rows) {
  const m = MEASURES[state.by];
  const market = rows.find((r) => r.id === 'market');
  const others = rows.filter((r) => r.id !== 'market');
  const beat = others.filter((r) => r.cagr > market.cagr).length;
  const tiles = [
    ['Best', rows[0].name, `${m.format(rows[0][state.by])} ${m.label}`],
    ['Worst', rows.at(-1).name, `${m.format(rows.at(-1)[state.by])} ${m.label}`],
    ['US Total Market', `#${market.rank} of ${rows.length}`, `${pct(market.cagr)} a year; $1 became ${money(market.growth)}`],
    ['Beat the market', `${beat} of ${others.length}`, 'grew faster per year than the total market'],
  ];
  $('tiles').replaceChildren(...tiles.map(([label, value, detail]) => {
    const t = el('div', 'tile');
    t.append(el('div', 'label', label), el('div', 'value', value), el('div', 'detail', detail));
    return t;
  }));
}

function renderBoards(rows) {
  const w = data.windows[state.years];
  const m = MEASURES[state.by];
  $('board-title').textContent = `Ranked by ${m.label}, ${state.years === '1' ? 'last 12 months' : `last ${state.years} years`}`;
  $('board-sub').textContent = `${w.start} to ${data.end} · ${rows.length} indexes${state.group === 'all' ? '' : ` in ${state.group} (plus the market)`} · the tick mark is the US Total Market`;
  const values = rows.map((r) => r[state.by]);
  const lo = Math.min(0, ...values), hi = Math.max(0, ...values);
  const x = (v) => ((v - lo) / (hi - lo || 1)) * 100;
  const market = rows.find((r) => r.id === 'market');
  const item = (r) => {
    const li = el('li', r.id === 'market' ? 'is-market' : '');
    const name = el('span', 'nm', r.name);
    if (r.group !== 'Industry') name.append(el('small', null, r.group));
    li.append(el('span', 'rk', `#${r.rank}`), name, el('span', 'vl', m.format(r[state.by])));
    const bar = el('div', 'bar');
    const fill = el('span', r[state.by] < 0 ? 'neg' : '');
    const [a, b] = [x(0), x(r[state.by])].sort((p, q) => p - q);
    fill.style.left = `${a}%`;
    fill.style.width = `${Math.max(b - a, 0.5)}%`;
    const tick = el('i');
    tick.style.left = `calc(${x(market[state.by])}% - 1px)`;
    bar.append(fill, tick);
    li.append(bar);
    return li;
  };
  $('top').replaceChildren(...rows.slice(0, 10).map(item));
  $('bottom').replaceChildren(...rows.slice(-10).map(item));
}

function renderTable(rows) {
  const { key, dir } = state.sort;
  const sorted = [...rows].sort((a, b) => (typeof a[key] === 'string' ? a[key].localeCompare(b[key]) : a[key] - b[key]) * dir);
  document.querySelectorAll('#table th button').forEach((b) => {
    if (b.dataset.sort === key) b.setAttribute('aria-sort', dir === 1 ? 'ascending' : 'descending');
    else b.removeAttribute('aria-sort');
  });
  $('table').querySelector('tbody').replaceChildren(...sorted.map((r) => {
    const tr = el('tr', [r.id === 'market' ? 'is-market' : '', state.picks.includes(r.id) ? 'picked' : ''].join(' '));
    tr.tabIndex = 0;
    tr.setAttribute('aria-selected', String(state.picks.includes(r.id)));
    const name = el('td');
    const k = state.picks.indexOf(r.id);
    if (k >= 0 || r.id === 'market') {
      const sw = el('i', 'swatch');
      sw.style.borderColor = r.id === 'market' ? MARKET_COLOR : SERIES[k];
      name.append(sw);
    }
    name.append(document.createTextNode(r.name));
    tr.append(
      el('td', 'num', String(r.rank)), name, el('td', null, r.group),
      el('td', `num${r.cagr < 0 ? ' neg' : ''}`, pct(r.cagr)), el('td', 'num', pct(r.volatility)),
      el('td', 'num', r.sharpe.toFixed(2)), el('td', 'num neg', pct(r.max_drawdown, 0)), el('td', 'num', money(r.growth)));
    const toggle = () => pick(r.id);
    tr.addEventListener('click', toggle);
    tr.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    return tr;
  }));
}

function pick(id) {
  if (id === 'market') return;
  const i = state.picks.indexOf(id);
  if (i >= 0) state.picks.splice(i, 1);
  else {
    if (state.picks.length >= MAX_PICKS) state.picks.shift();
    state.picks.push(id);
  }
  render();
}

// ----- growth of $1 (log scale) -----------------------------------------------------
const tip = $('tooltip');
function renderGrowth() {
  const g = data.growth;
  const years = +state.years;
  // Rebase every line to $1 at the start of the chosen window.
  const [endYear, endMonth] = data.end.split('-').map(Number);
  const baseLabel = `${endYear - years}-${String(endMonth).padStart(2, '0')}`;
  const from = Math.max(0, g.labels.indexOf(baseLabel));
  const labels = g.labels.slice(from);
  const rebase = (path) => path.slice(from).map((v) => v / path[from]);
  const series = [{ id: 'market', name: 'US Total Market', color: MARKET_COLOR, values: rebase(g.paths.market) },
    ...state.picks.map((id, k) => ({ id, name: byId[id].name, color: SERIES[k], values: rebase(g.paths[id]) }))];
  $('growth-sub').textContent = `$1 invested at the end of ${labels[0]}, valued every ${new Date(`${data.end}-15`).toLocaleString('en-US', { month: 'long' })} through ${data.end}`;

  const key = $('growth-key');
  key.replaceChildren(...series.map((s) => {
    const span = el('span');
    const line = el('i');
    line.style.borderColor = s.color;
    span.append(line, document.createTextNode(s.name));
    if (s.id !== 'market') {
      const x = el('button', null, '×');
      x.setAttribute('aria-label', `Remove ${s.name}`);
      x.onclick = () => pick(s.id);
      span.append(x);
    }
    return span;
  }));

  const box = $('growth-chart').getBoundingClientRect();
  const width = Math.max(300, box.width), height = box.height;
  const m = { top: 10, right: 70, bottom: 26, left: 52 };
  const all = series.flatMap((s) => s.values).filter((v) => v > 0);
  const x = d3.scaleLinear().domain([0, labels.length - 1]).range([m.left, width - m.right]);
  const y = d3.scaleLog().domain([Math.min(0.5, d3.min(all)), Math.max(2, d3.max(all))]).nice().range([height - m.bottom, m.top]);
  const svg = d3.select('#growth-chart').selectAll('svg').data([null]).join('svg').attr('viewBox', `0 0 ${width} ${height}`);
  svg.selectAll('*').remove();
  const ticks = y.ticks().filter((t) => [1, 2, 5].includes(+t.toPrecision(1)[0]) || t === 1);
  const yTicks = ticks.length > 8 ? ticks.filter((t) => String(t)[0] === '1') : ticks;
  svg.append('g').selectAll('line').data(yTicks).join('line').attr('class', (t) => (t === 1 ? 'baseline' : 'gridline'))
    .attr('x1', m.left).attr('x2', width - m.right).attr('y1', y).attr('y2', y);
  svg.append('g').attr('class', 'axis').selectAll('text').data(yTicks).join('text')
    .attr('x', m.left - 8).attr('y', y).attr('dy', '0.32em').attr('text-anchor', 'end').text((t) => `$${t >= 1000 ? d3.format('~s')(t) : t}`);
  const step = Math.ceil(labels.length / 8);
  svg.append('g').attr('class', 'axis').selectAll('text').data(labels.map((l, i) => [l, i]).filter(([, i]) => i % step === 0))
    .join('text').attr('x', ([, i]) => x(i)).attr('y', height - 6).attr('text-anchor', 'middle').text(([l]) => l.slice(0, 4));
  const line = d3.line().x((_, i) => x(i)).y((v) => y(v));
  const ends = [];
  for (const s of series) {
    svg.append('path').attr('class', 'line').attr('stroke', s.color).attr('d', line(s.values));
    ends.push({ text: money(s.values.at(-1)), y: y(s.values.at(-1)) });
  }
  // Direct value labels at the line ends, nudged apart so they don't overlap.
  ends.sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 13);
  svg.append('g').selectAll('text').data(ends).join('text').attr('class', 'label').attr('x', width - m.right + 6).attr('y', (d) => d.y).attr('dy', '0.32em').text((d) => d.text);

  const cross = svg.append('line').attr('class', 'crosshair').attr('y1', m.top).attr('y2', height - m.bottom).style('display', 'none');
  const dots = series.map((s) => svg.append('circle').attr('class', 'dot').attr('r', 4.5).attr('fill', s.color).style('display', 'none'));
  svg.append('rect').attr('x', m.left).attr('y', 0).attr('width', width - m.left - m.right).attr('height', height - m.bottom).attr('fill', 'transparent')
    .on('pointermove', (event) => {
      const i = Math.max(0, Math.min(labels.length - 1, Math.round(x.invert(d3.pointer(event)[0]))));
      cross.style('display', null).attr('x1', x(i)).attr('x2', x(i));
      series.forEach((s, k) => dots[k].style('display', null).attr('cx', x(i)).attr('cy', y(s.values[i])));
      tip.replaceChildren(el('div', 'tt-title', labels[i]));
      [...series].sort((a, b) => b.values[i] - a.values[i]).forEach((s) => {
        const row = el('div', 'tt-row');
        const k = el('i', 'tt-key');
        k.style.borderColor = s.color;
        row.append(k, el('b', null, money(s.values[i])), el('span', null, s.name));
        tip.append(row);
      });
      tip.hidden = false;
      const r = tip.getBoundingClientRect();
      tip.style.left = `${Math.min(event.clientX + 14, innerWidth - r.width - 8)}px`;
      tip.style.top = `${Math.min(event.clientY + 14, innerHeight - r.height - 8)}px`;
    })
    .on('pointerleave', () => { cross.style('display', 'none'); dots.forEach((d) => d.style('display', 'none')); tip.hidden = true; });
}

function renderPersistence() {
  $('persist').replaceChildren(...['10', '15', '20'].map((y) => {
    const p = data.persistence[y];
    const box = el('div', 'p');
    box.append(el('span', null, `${y}-year periods: ${p.earlier} vs ${p.recent}`),
      el('b', null, `${p.top10_repeat} of 10`),
      el('span', null, `of the earlier top 10 stayed in the top 10 · rank correlation ${p.spearman.toFixed(2)}`));
    return box;
  }));
}

function render() {
  const rows = ranked();
  renderTiles(rows);
  renderBoards(rows);
  renderTable(rows);
  renderGrowth();
}

async function init() {
  data = await fetch('site/data.json').then((r) => r.json());
  byId = Object.fromEntries(data.indexes.map((i) => [i.id, i]));
  $('data-end').textContent = new Date(`${data.end}-15`).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  const seg = $('window');
  const buttons = Object.keys(data.windows).map((y) => {
    const b = el('button', null, y === '1' ? '1 yr' : `${y} yrs`);
    b.type = 'button';
    b.setAttribute('role', 'radio');
    b.onclick = () => { state.years = y; buttons.forEach((x) => x.setAttribute('aria-checked', String(x === b))); render(); };
    b.setAttribute('aria-checked', String(y === state.years));
    return b;
  });
  seg.replaceChildren(...buttons);

  $('by').onchange = (e) => { state.by = e.target.value; state.sort = { key: 'rank', dir: 1 }; render(); };
  const groups = [...new Set(data.indexes.map((i) => i.group))].filter((g) => g !== 'Market');
  $('group').replaceChildren(new Option('All 125 indexes', 'all'), ...groups.map((g) => new Option(g === 'Industry' ? 'Industries' : g, g)));
  $('group').onchange = (e) => { state.group = e.target.value; render(); };
  document.querySelectorAll('#table th button').forEach((b) => (b.onclick = () => {
    const key = b.dataset.sort;
    const natural = ['name', 'group', 'rank', 'volatility'].includes(key) ? 1 : -1;
    state.sort = { key, dir: state.sort.key === key ? -state.sort.dir : natural };
    renderTable(ranked());
  }));

  // Start by comparing the 15-year best and worst with the market.
  const first = ranked();
  state.picks = [first[0].id, first.at(-1).id];
  renderPersistence();
  render();
  let t;
  addEventListener('resize', () => { clearTimeout(t); t = setTimeout(renderGrowth, 120); });
}

init().catch((err) => { $('tiles').textContent = `The data didn’t load: ${err}`; });
