/** Existing renderer only; no v2 imports or browser/DB required. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import ts from 'typescript';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
registerHooks({
  resolve(s,c,next){return next(s.endsWith('/template-render') ? s+'.ts' : s,c);},
  load(url,c,next){
    if(url.endsWith('.json'))return {format:'module',shortCircuit:true,source:'export default '+JSON.stringify(JSON.parse(readFileSync(new URL(url),'utf8')))+';'};
    if(url.endsWith('.module.css'))return {format:'module',shortCircuit:true,source:'export default new Proxy({}, {get:(_,key)=>String(key)});'};
    if(url.endsWith('.tsx'))return {format:'module',shortCircuit:true,source:ts.transpileModule(readFileSync(new URL(url),'utf8'),{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.ESNext}}).outputText};
    return next(url,c);
  }
});
const {default:Renderer}=await import('../../../apps/studio/src/components/templates/portfolio-renderer.tsx');
const baseline=JSON.parse(readFileSync(new URL('../../../contracts/fixtures/hero/v1-reference.v1.json',import.meta.url),'utf8'));
for(const name of ['minimal','editorial'])test(`v1 ${name}: immutable source and exact rendered HTML baseline`,()=>{
  const raw=readFileSync(new URL(`../../../contracts/templates/${name}/1.0.0/snapshot.json`,import.meta.url));
  const html=renderToStaticMarkup(React.createElement(Renderer,{snapshot:JSON.parse(raw.toString('utf8')),demonstration:true}));
  assert.equal(createHash('sha256').update(html).digest('hex'),baseline.html_sha256[name]);
});
