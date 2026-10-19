import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer,fixtures} from '../../../scripts/verification/hero-rendering-support.mjs';
import {heroResolver} from '../src/hero-runtime.ts';
import {HeroRenderingError,requireRenderableHero} from '../src/hero-rendering.ts';
const render=(snapshot,extra={})=>renderToStaticMarkup(React.createElement(Renderer,{snapshot,sectionId:'hero',enabled:true,continuationId:'projects',...extra}));
const base=fixtures.cases[0].design;
for(const c of fixtures.cases)test(`actual SSR ${c.id}: valid full snapshot, independent breakpoint settings, no mutation`,()=>{
 const before=JSON.stringify(c.design);const html=render(c.design);
 assert.ok(html.includes(`data-hero-layout="${c.id}"`));assert.equal((html.match(/<h1 /g)||[]).length,1);
 assert.ok(html.includes('href="#projects"'));assert.ok(html.includes('aria-labelledby="modular-hero-hero-title"'));
 assert.ok(html.includes('--hero-align-tablet:left'));assert.ok(html.includes(`--hero-align-desktop:${c.id==='centered'?'center':'left'}`));
 assert.equal(JSON.stringify(c.design),before);
});
test('default opt-in gate is closed; no v1 fallback',()=>{
 assert.throws(()=>render(base,{enabled:undefined}),/disabled/);
 assert.throws(()=>render(base,{enabled:false}),/disabled/);
 assert.throws(()=>render({...base,schema_version:1}),/unsupported Hero contract/);
});
test('structural differences, not just data labels',()=>{
 const html=fixtures.cases.map(c=>render(c.design));
 assert.ok(!html[0].includes('DESIGN<br/>WITH INTENT.'));
 assert.ok(html[2].includes('01 — PORTFOLIO'));assert.ok(!html[1].includes('01 — PORTFOLIO'));
 assert.ok(html[3].includes('DESIGN<br/>WITH INTENT.'));
 const css=readFileSync(new URL('../../../apps/studio/src/components/templates/modular-hero-renderer.module.css',import.meta.url),'utf8');
 for(const id of ['centered','split-screen','fullscreen','typographic']) assert.ok(css.includes(`[data-hero-layout="${id}"]`));
 assert.ok(css.includes('min-height:100svh'));assert.ok(css.includes('minmax(0,1.2fr)'));
});
test('unsupported declarations are never presented as implementations',()=>{
 const registry=JSON.parse(readFileSync(new URL('../../../contracts/hero/renderer.v1.json',import.meta.url),'utf8'));
 assert.equal(registry.enabled_by_default,false);assert.equal(registry.layouts.filter(x=>x.implemented).length,7);
 assert.ok(registry.layouts.every(x=>x.selectable===false));
 const hero=heroResolver.resolve(base).heroes[0];
 for(const id of ['product-showcase','bento-grid','unknown']) assert.throws(()=>requireRenderableHero({...hero,layout:{...hero.layout,id}}),HeroRenderingError);
 assert.throws(()=>requireRenderableHero({...hero,layout:{...hero.layout,version:'2.0.0'}}),HeroRenderingError);
 const d=structuredClone(base);d.composition.sections[0].hero.layout.id='unknown';assert.throws(()=>render(d),/unsupported/);
});
test('behavior, arbitrary CSS/HTML, wrong versions and low contrast reject before render',()=>{
 for(const modify of [
  d=>{d.composition.sections[0].hero.layout.version='9.0.0';},
  d=>{d.customization.sections=[{section_id:'hero',hero:{schema_version:1,behavior:{kind:'parallax'}}}];},
  d=>{d.presentation.sections[0].hero.appearance.style='url(javascript:alert(1))';},
  d=>{d.presentation.sections[0].hero.appearance.palette.text='#F5F4EE';},
  d=>{d.presentation.sections[0].hero.appearance.palette.accent='#F5F4EE';},
  d=>{d.presentation.sections[0].hero.appearance.typography.family='external-font';},
 ]){const d=structuredClone(base);modify(d);assert.throws(()=>render(d));}
});
test('React escapes text and scopes cannot inject CSS, HTML or fragment URLs',()=>{
 const d=structuredClone(base);d.content.sections[0].data.title='<script>alert("x")</script>';
 const html=render(d);assert.ok(!html.includes('<script>'));assert.ok(html.includes('&lt;script&gt;'));
 for(const scope of ['bad scope','<img>','x" style="color:red',''])assert.throws(()=>render(base,{scope}));
 for(const continuationId of ['https://example.test','javascript:alert(1)','x" onclick="x'])assert.throws(()=>render(base,{continuationId}));
 assert.ok(!render(base,{continuationId:undefined}).includes('<a '));
 assert.ok(render(base,{scope:'separate'}).includes('id="separate-hero-title"'));
});
test('required Hero visibility and missing section reject explicitly',()=>{
 const d=structuredClone(base);d.composition.sections[0].visible=false;
 // Required Hero cannot be hidden under the accepted contracts.
 assert.throws(()=>render(d));
 assert.throws(()=>render(base,{sectionId:'missing'}),/missing/);
});
test('all palette, type, background and surface combinations pass actual full resolver',()=>{
 for(const c of fixtures.cases)for(const scale of ['compact','balanced','display'])for(const kind of ['flat','glass'])for(const dark of [false,true])for(const background of ['solid','gradient']) {
  const d=structuredClone(c.design);const a=d.presentation.sections[0].hero.appearance;
  a.palette=dark?{text:'#FFFFFF',surface:'#111111',accent:'#CCFFAA'}:{text:'#111111',surface:'#FFFFFF',accent:'#224433'};
  a.background=background==='solid'?{kind:'solid',color:'#123456'}:{kind:'gradient',angle:359,stops:[{color:'#123456',position:0},{color:'#FEDCBA',position:100}]};
  a.typography.scale=scale;a.surface=kind==='flat'?{kind}:{kind,opacity:85,blur:12};
  const html=render(d);assert.ok(html.includes(`data-hero-surface="${kind}"`));
 }
});

test('empty heading rejects explicitly; blank CTA never becomes a focus stop',()=>{
 const d=structuredClone(base);d.content.sections[0].data.title='  ';assert.throws(()=>render(d),/accessible text/);
 d.content.sections[0].data.title='Titre fictif';d.content.sections[0].data.cta_label='  ';assert.ok(!render(d).includes('<a '));
});
test('renderer registry is consistent with frozen declarations, not a replacement',()=>{
 const read=path=>JSON.parse(readFileSync(new URL('../../../contracts/hero/'+path,import.meta.url),'utf8'));
 const declared=read('capabilities.v1.json'),renderer=read('renderer.v1.json');
 assert.equal(declared.runtime_enabled,false);assert.ok(declared.layouts.every(x=>!x.implemented && !x.selectable));
 const textual=read('text-layouts.v1.json');
 for(const entry of renderer.layouts)assert.ok([...declared.layouts,...textual.layouts].some(x=>x.id===entry.id && x.version===entry.version));
 assert.equal(new Set(renderer.layouts.map(x=>x.id)).size,7);
 assert.deepEqual(renderer.appearance,declared.appearance.map(x=>x.id));assert.deepEqual(renderer.behavior,['none']);
});
