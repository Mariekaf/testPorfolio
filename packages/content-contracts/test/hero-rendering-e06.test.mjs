import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer,fixtures} from '../../../scripts/verification/hero-rendering-support.mjs';
const base=new URL('../../../',import.meta.url);
const references=JSON.parse(readFileSync(new URL('contracts/fixtures/hero/e05-reference.v1.json',base),'utf8'));
const additions=JSON.parse(readFileSync(new URL('contracts/fixtures/hero/rendering.e06.v1.json',base),'utf8'));
const render=c=>renderToStaticMarkup(React.createElement(Renderer,{snapshot:c.design,sectionId:'hero',enabled:true,scope:c.id,continuationId:'projects'}));
for(const c of fixtures.cases)test(`E05 ${c.id}: exact accepted HTML preserved`,()=>{
 assert.equal(createHash('sha256').update(render(c)).digest('hex'),references.html_sha256[c.id]);
});
for(const c of additions.cases)test(`E06 ${c.id}: full-document SSR, no mutation, no invented user metrics`,()=>{
 const before=JSON.stringify(c.design),html=render(c);
 assert.ok(html.includes(`data-hero-layout="${c.id}"`));
 assert.ok(html.includes(c.design.content.sections[0].data.title));
 assert.equal((html.match(/<h1 /g)||[]).length,1);
 assert.ok(!/\b(?:98%|10k|users|utilisateurs)\b/.test(html));
 assert.equal(JSON.stringify(c.design),before);
});

for(const c of [...fixtures.cases,...additions.cases])test(`seven-layout combinations ${c.id}: palette independent of geometry`,()=>{
 for(const scale of ['compact','balanced','display'])for(const surface of ['flat','glass'])for(const dark of [false,true])for(const background of ['solid','gradient']){
  const d=structuredClone(c);const a=d.design.presentation.sections[0].hero.appearance;
  a.palette=dark?{text:'#FFFFFF',surface:'#111111',accent:'#CCFFAA'}:{text:'#111111',surface:'#FFFFFF',accent:'#224433'};
  a.typography.scale=scale;a.surface=surface==='flat'?{kind:'flat'}:{kind:'glass',opacity:85,blur:12};
  a.background=background==='solid'?{kind:'solid',color:'#123456'}:{kind:'gradient',angle:359,stops:[{color:'#123456',position:0},{color:'#FEDCBA',position:100}]};
  const html=render(d);assert.ok(html.includes(`data-hero-layout="${c.id}"`));
 }
});

test('textual profile is explicit and preserves rejection of old media prerequisites',async()=>{
 const {heroResolver,textHeroResolver}=await import('../src/hero-runtime.ts');
 for(const c of additions.cases.slice(1)){
  assert.throws(()=>heroResolver.resolve(c.design));
  assert.equal(textHeroResolver.resolve(c.design).heroes[0].layout.version,'1.1.0');
  const old=structuredClone(c.design);old.composition.sections[0].hero.layout.version='1.0.0';
  assert.throws(()=>textHeroResolver.resolve(old));
 }
});
test('untrusted profile edits, versions or properties cannot expand the renderer',async()=>{
 const {readContracts}=await import('./hero-resolution-support.ts');
 const {createHeroResolver}=await import('../src/hero-resolution.ts');
 const profile=JSON.parse(readFileSync(new URL('contracts/hero/text-layouts.v1.json',base),'utf8'));
 const schema=JSON.parse(readFileSync(new URL('contracts/schemas/hero/text-layouts.v1.json',base),'utf8'));
 for(const edit of [p=>p.version='2.0.0',p=>p.layouts[0].requires=[],p=>p.extra='css',p=>p.layouts.push({id:'unknown',version:'1.1.0',requires:[]})]){
  const copy=structuredClone(profile);edit(copy);const contracts=readContracts();contracts.schemas['hero/text-layouts.v1.json']=schema;
  assert.throws(()=>createHeroResolver({...contracts,textLayouts:copy}));
 }
 const d=structuredClone(additions.cases[1]);d.design.presentation.sections[0].hero.appearance.background={kind:'video',url:'https://example.invalid/x'};
 assert.throws(()=>render(d));
});

test('three E06 layouts have distinct real structures with decorative-only cells',()=>{
 const outputs=Object.fromEntries(additions.cases.map(c=>[c.id,render(c)]));
 assert.ok(outputs.asymmetric.includes('class="offsetArt"'));assert.ok(!outputs.asymmetric.includes('class="productPanel"'));
 assert.ok(outputs['product-showcase'].includes('class="productPanel"'));assert.ok(!outputs['product-showcase'].includes('data-cell='));
 assert.equal((outputs['bento-grid'].match(/data-cell=/g)||[]).length,3);
 assert.ok(!outputs['bento-grid'].includes('class="offsetArt"'));
 for(const html of Object.values(outputs))assert.equal((html.match(/<a /g)||[]).length,1);
});
