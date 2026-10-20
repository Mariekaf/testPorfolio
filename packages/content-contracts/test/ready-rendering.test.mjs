import {test} from 'node:test';import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';import {createHash} from 'node:crypto';
import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer,demonstrations} from '../../../scripts/verification/ready-rendering-support.mjs';
import {resolveFixtureMedia} from '../src/ready-fixture-media.ts';
import {loadReadyRegistry} from '../src/ready-registry.ts';
const render=(c,props={})=>renderToStaticMarkup(React.createElement(Renderer,{document:c.document,media:c.media,enabled:true,demonstration:true,...props}));
const base=demonstrations.cases[0];
for(const c of demonstrations.cases)test('full six-section synthetic rendering '+c.id,()=>{
 const before=JSON.stringify(c),html=render(c);
 const sections=[...html.matchAll(/data-ready-section="([^"]+)"/g)].map(x=>x[1]);
 assert.deepEqual(sections,['navigation','hero','about','projects','contact','footer']);
 assert.equal((html.match(/<h1 /g)||[]).length,1);assert.equal((html.match(/<h2 /g)||[]).length,3);assert.equal((html.match(/<h3>/g)||[]).length,3);
 assert.ok(html.includes('Démonstration synthétique'));assert.ok(html.includes(c.document.content.slots.identity_name.value));
 for(const [id,slot] of Object.entries(c.document.content.slots)){
  if(slot.type==='text'&&slot.value)assert.ok(html.includes(slot.value.replaceAll('&','&amp;')),id);
  if(slot.type==='rich_text')for(const p of slot.blocks)for(const child of p.children)assert.ok(html.includes(child.text),id);
  if(slot.type==='image'||slot.type==='logo')assert.ok(html.includes(slot.value.alt),id);
  if(slot.type==='link')assert.ok(html.includes(slot.label),id);
  if(slot.type==='project_list')for(const item of slot.items)assert.ok(html.includes(item.title)&&html.includes(item.summary)&&html.includes(item.cover.alt),id);
  if(slot.type==='social_links')for(const item of slot.items)assert.ok(html.includes(item.label),id);
 }
 assert.equal(JSON.stringify(c),before);
});
test('default gate closed, invalid scope and malformed/legacy documents refuse',()=>{
 assert.throws(()=>render(base,{enabled:undefined}),/disabled/);assert.throws(()=>render(base,{enabled:false}),/disabled/);
 for(const scope of ['bad scope','x" style="color:red',''])assert.throws(()=>render(base,{scope}));
 for(const version of [1,2,4])assert.throws(()=>render({...base,document:{...base.document,schema_version:version}}));
 const c=structuredClone(base);delete c.document.content.slots.hero_title;assert.throws(()=>render(c));
});
test('empty draft has honest placeholders and omits missing sections/navigation links',()=>{
 const html=render({document:loadReadyRegistry().get().bundle.snapshot},{demonstration:false});
 assert.ok(html.includes('Votre titre — brouillon'));assert.ok(html.includes('Identité à compléter'));assert.ok(!html.includes('<img'));
 assert.deepEqual([...html.matchAll(/data-ready-section="([^"]+)"/g)].map(x=>x[1]),['navigation','hero','footer']);
 assert.ok(!html.includes('href="#creative-projects"'));assert.ok(!html.includes('Alix'));assert.ok(!html.includes('Sacha'));
});
for(const state of ['available','missing','processing','rejected','unauthorized','invalid'])test('controlled portrait state '+state,()=>{
 const c=structuredClone(base),ref=c.document.content.slots.hero_portrait.value,entry=c.media.assets[ref.asset_id];
 if(state==='missing')delete c.media.assets[ref.asset_id];
 if(state==='processing'||state==='rejected')entry.state=state;
 if(state==='unauthorized')entry.accountId='foreign';
 if(state==='invalid')entry.sourceId='https://example.invalid/evil.svg';
 const result=resolveFixtureMedia(ref,c.media);assert.equal(result.state,state);
 const html=render(c);
 if(state==='available'){assert.ok(html.includes('portrait-a.svg'));assert.ok(result.src.startsWith('/__ready_assets/'));}
 else{assert.ok(html.includes(`data-media-state="${state}"`));assert.ok(!html.includes('portrait-a.svg'));}
});
test('no rights, alt missing and unknown source never render an image fallback',()=>{
 const c=structuredClone(base),ref=c.document.content.slots.hero_portrait.value,entry=c.media.assets[ref.asset_id];
 entry.rightsConfirmed=false;assert.equal(resolveFixtureMedia(ref,c.media).state,'unauthorized');
 entry.rightsConfirmed=true;entry.sourceId='../../.local/auth.json';assert.equal(resolveFixtureMedia(ref,c.media).state,'invalid');
 ref.alt='';assert.equal(resolveFixtureMedia(ref,c.media).state,'missing');
 assert.ok(!render(c).includes('portrait-a.svg'));
});
test('hostile strings are text, markup/CSS/URL injections refuse',()=>{
 const c=structuredClone(base);c.document.content.slots.hero_title.value='<script>alert("x")</script>';
 let html=render(c);assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));
 c.document.content.slots.hero_cta.target={kind:'external',url:'javascript:alert(1)'};assert.throws(()=>render(c));
 const d=structuredClone(base);d.document.content.slots.hero_portrait.value.url='file:///.local/auth.json';assert.throws(()=>render(d));
 d.document=structuredClone(base.document);d.document.customization.style_overrides.css='position:fixed';assert.throws(()=>render(d));
});
test('authorized palettes/fonts apply without changing locked structure',()=>{
 const canonical=[...render(base).matchAll(/data-ready-section="([^"]+)"/g)].map(x=>x[1]);
 for(const palette_id of ['ink-lime','paper-cobalt'])for(const id of ['system-sans','system-serif']){
  const c=structuredClone(base);c.document.customization.style_overrides={palette_id,font_ref:{id,version:'1.0.0'}};
  const html=render(c);assert.deepEqual([...html.matchAll(/data-ready-section="([^"]+)"/g)].map(x=>x[1]),canonical);
  assert.ok(html.includes(id==='system-serif'?'ui-serif':'ui-sans-serif'));
 }
});
test('two independent data sets share exact composition and differ in text and media',()=>{
 const [a,b]=demonstrations.cases;assert.deepEqual(a.document.composition,b.document.composition);
 assert.deepEqual(a.document.presentation,b.document.presentation);assert.notEqual(render(a),render(b));
 for(const [id,slot] of Object.entries(a.document.content.slots))assert.notDeepEqual(slot,b.document.content.slots[id],id);
});
test('synthetic assets have real hashes and closed passive original SVG vocabulary',()=>{
 const root=new URL('../../../contracts/fixtures/ready-rendering/assets/',import.meta.url),index=JSON.parse(readFileSync(new URL('index.v1.json',root),'utf8'));
 for(const source of index.sources){
  const raw=readFileSync(new URL(source.file,root)),svg=raw.toString('utf8');assert.equal(raw.length,source.bytes);assert.equal(createHash('sha256').update(raw).digest('hex'),source.sha256);
  assert.ok(!/<(?:script|foreignObject|image|use|a|style|filter|animate)\b|\bon[a-z]+\s*=|href\s*=|url\(/i.test(svg));
 }
});
