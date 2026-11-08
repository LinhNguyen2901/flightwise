import {build} from 'esbuild';
import {resolve} from 'node:path';

await build({
  absWorkingDir: import.meta.dirname,
  entryPoints: ['../notebooks/preview.js'],
  nodePaths: [resolve(import.meta.dirname, 'node_modules')],
  bundle: true,
  format: 'iife',
  globalName: 'FlightWisePreview',
  outfile: '../notebooks/build/preview.js',
});

await build({
  absWorkingDir: import.meta.dirname,
  entryPoints: ['../notebooks/cellCharts.js'],
  nodePaths: [resolve(import.meta.dirname, 'node_modules')],
  bundle: true,
  minify: true,
  format: 'iife',
  globalName: 'FlightWiseCell',
  outfile: '../notebooks/build/cellCharts.js',
});
