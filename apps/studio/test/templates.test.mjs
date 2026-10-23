import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {registerHooks} from 'node:module';
import ts from 'typescript';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {effectiveSections,safeProjectUrl} from '../src/lib/template-render.ts';

// Test the actual TSX component through the installed TypeScript compiler.
registerHooks({
 resolve(specifier,context,next){
  if(specifier.endsWith('/template-render'))return next(specifier+'.ts',context);
  return next(specifier,context);
 },
 load(url,context,next){
  if(url.endsWith('.json'))return {format:'module',shortCircuit:true,source:'export default '+JSON.stringify(JSON.parse(readFileSync(new URL(url),'utf8')))+';'};
  if(url.endsWith('.module.css'))return {format:'module',shortCircuit:true,source:'export default new Proxy({}, {get:(_,key)=>String(key)});'};
  if(url.endsWith('.tsx'))return {format:'module',shortCircuit:true,source:ts.transpileModule(readFileSync(new URL(url),'utf8'),{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.ESNext}}).outputText};
  return next(url,context);
 }
});
const {default:PortfolioRenderer}=await import('../src/components/templates/portfolio-renderer.tsx');
const snapshot=name=>JSON.parse(readFileSync(new URL(`../../../contracts/templates/${name}/1.0.0/snapshot.json`,import.meta.url),'utf8'));

test('real renderer produces distinct layouts and all declared section variants',()=>{
 const html=['minimal','editorial'].map(name=>{
  const doc=snapshot(name);const html=renderToStaticMarkup(React.createElement(PortfolioRenderer,{snapshot:doc,demonstration:true}));
  for(const section of doc.composition.sections)assert.ok(html.includes(`data-variant="${section.variant}"`));
  assert.equal((html.match(/data-section=/g)||[]).length,5);
  assert.equal((html.match(/ÉTUDE DE CAS/g)||[]).length,3);
  assert.ok(html.includes('Contenus et projets fictifs'));assert.ok(!html.includes('<img'));
  return html;
 });
 assert.ok(html[0].includes('minimal-stack'));assert.ok(html[1].includes('editorial-grid'));assert.notEqual(html[0],html[1]);
});
test('same renderer resolves a local snapshot without modifying its source',()=>{
 const source=snapshot('minimal');const instance=structuredClone(source);
 instance.customization={schema_version:1,section_order:['hero','skills','about','projects','contact'],sections:[{section_id:'about',visible:false},{section_id:'projects',presentation:{spacing:'airy'}}]};
 const sections=effectiveSections(instance);
 assert.deepEqual(sections.map(s=>s.section.id),['hero','skills','projects','contact']);
 assert.equal(sections.find(s=>s.section.id==='projects').settings.spacing,'airy');
 assert.equal(source.customization.sections.length,0);
 const html=renderToStaticMarkup(React.createElement(PortfolioRenderer,{snapshot:instance}));
 assert.ok(!html.includes('data-section="about"'));assert.ok(html.indexOf('data-section="skills"')<html.indexOf('data-section="projects"'));
});
test('React escapes hostile text and never renders HTML or unsafe project links',()=>{
 const doc=snapshot('minimal');doc.content.sections.find(s=>s.type==='hero').data.title='<script>alert(1)</script>';
 doc.content.sections.find(s=>s.type==='projects').data.items[0].url='javascript:alert(1)';
 const html=renderToStaticMarkup(React.createElement(PortfolioRenderer,{snapshot:doc,demonstration:true}));
 assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script'));assert.ok(!html.includes('javascript:'));
});
test('URLs reject unsafe schemes, credentials and whitespace',()=>{
 for(const value of [null,'javascript:alert(1)','data:text/html,hi','http://example.test','https://u:p@example.test','https://example.test/\n'])assert.equal(safeProjectUrl(value),undefined);
 assert.equal(safeProjectUrl('https://example.test/case'),'https://example.test/case');
});
test('protected sections, unknown documents and invalid settings fail closed',()=>{
 for(const modify of [d=>d.experience={},d=>d.schema_version=2,d=>d.customization.sections=[{section_id:'hero',visible:false}],d=>d.customization.section_order=['contact','hero','projects','about','skills'],d=>d.customization.sections=[{section_id:'projects',presentation:{spacing:'arbitrary-css'}}]]){
  const doc=snapshot('minimal');modify(doc);assert.throws(()=>effectiveSections(doc));
 }
});
test('renderer has only whitelisted local styling and responsive container rules',()=>{
 const css=readFileSync(new URL('../src/components/templates/portfolio-renderer.module.css',import.meta.url),'utf8');
 assert.ok(css.includes('@container(max-width:650px)'));assert.ok(css.includes('grid-template-columns:1fr'));
 assert.ok(!/url\(|@import|animation:/.test(css));
});
