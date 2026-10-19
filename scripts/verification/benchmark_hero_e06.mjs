/** Synthetic Node SSR timings, not user-device or HTTP latency claims. */
import {performance} from 'node:perf_hooks';
import {readFileSync,writeFileSync} from 'node:fs';
import {gzipSync} from 'node:zlib';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
const start=performance.now();
const {Renderer,fixtures}=await import('./hero-rendering-support.mjs');
const initialization=performance.now()-start;
const extra=JSON.parse(readFileSync(new URL('../../contracts/fixtures/hero/rendering.e06.v1.json',import.meta.url),'utf8'));
const measurements=[];
for(const c of [...fixtures.cases,...extra.cases]){
 const render=()=>renderToStaticMarkup(React.createElement(Renderer,{snapshot:c.design,sectionId:'hero',enabled:true,scope:c.id,continuationId:'projects'}));
 const firstStart=performance.now();const html=render();const first=performance.now()-firstStart;
 for(let i=0;i<10;i++)render();
 const samples=[];for(let i=0;i<100;i++){const t=performance.now();render();samples.push(performance.now()-t);}
 samples.sort((a,b)=>a-b);
 measurements.push({layout:c.id,iterations:100,first_render_ms:first,median_ms:samples[49],p95_ms:samples[94],html_bytes:Buffer.byteLength(html)});
}
const css=readFileSync(new URL('../../apps/studio/src/components/templates/modular-hero-renderer.module.css',import.meta.url));
const result={runtime:process.version,initialization_ms:initialization,measurements,css_bytes:css.length,css_gzip_bytes:gzipSync(css).length,
 limitations:['Synthetic Node/Linux SSR, loader/JSX transpilation included in initialization.','No HTTP, hydration, database, physical mobile GPU or Core Web Vitals benchmark.','No new route activated; unused component is not a measured deployed bundle.']};
if(!process.argv[2])throw new Error('Pass a new evidence filename.');
writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n',{encoding:'utf8',flag:'wx'});
console.log('Synthetic SSR benchmark completed for '+measurements.length+' supported layouts.');
