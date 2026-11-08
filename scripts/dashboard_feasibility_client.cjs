// M1.5 cached JavaScript count reduction benchmark. No DOM, server or app.
const fs = require('node:fs');
const path = require('node:path');
const { performance } = require('node:perf_hooks');
const root = path.join(__dirname, '..');
const configPath = path.join(root, 'data/active_dataset.json');
const active = JSON.parse(fs.readFileSync(configPath,'utf8'));
const dir = process.argv[2] ? path.resolve(process.argv[2]) : path.join(root, active.feasibility_dir);
const input = fs.readFileSync(path.join(dir, 'client_inputs.json'), 'utf8');
const {contexts, counts, filters, expected_bars} = JSON.parse(input);
function reduce(rows, cells, heatmap = false) {
  const selected = new Set(cells.map(([d,h]) => `${d}:${h}`));
  const groups = new Map();
  for (const row of rows) {
    if (selected.size && !selected.has(`${row.weekday}:${row.hour}`)) continue;
    const key = heatmap ? `${row.weekday}:${row.hour}` : row.carrier;
    if (!groups.has(key)) groups.set(key, Object.fromEntries(counts.map(c => [c,0])));
    const group = groups.get(key);
    for (const count of counts) group[count] += row[count];
  }
  return groups;
}
function bench(fn) {
  for(let i=0;i<20;i++) fn();
  const ms=[];
  for(let i=0;i<200;i++){const t=performance.now();fn();ms.push(performance.now()-t);}
  ms.sort((a,b)=>a-b);
  return {iterations:200,median_ms:ms[100],p95_ms:ms[189],max_ms:ms[199]};
}
const results = {node:process.version,benchmarks:{},checked_scenarios:0};
for (const [context,rows] of Object.entries(contexts)) {
  const serialized = JSON.stringify(rows);
  for (const [selection,cells] of Object.entries(filters)) {
    const result=reduce(rows,cells);
    const expected=expected_bars.filter(r=>r.context===context && r.selection===selection);
    if (result.size!==expected.length) throw Error('Carrier count mismatch');
    for (const row of expected) for (const count of counts) {
      if(result.get(row.carrier)[count]!==row[count]) throw Error(`${context}/${selection}/${count}`);
    }
    results.checked_scenarios++;
  }
  results.benchmarks[context]={
    parse_context:bench(()=>JSON.parse(serialized)),
    heatmap_counts:bench(()=>reduce(rows,[],true)),
    narrow_bar_counts:bench(()=>reduce(rows,[[1,8]])),
    disjoint_bar_counts:bench(()=>reduce(rows,[[1,8],[5,17]])),
  };
}
fs.writeFileSync(path.join(dir,'client_results.json'),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify(results,null,2));
