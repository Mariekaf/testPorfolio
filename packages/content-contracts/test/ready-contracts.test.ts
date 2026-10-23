import {test} from 'node:test';import assert from 'node:assert/strict';
import {loadReadyRegistry,strictReadyJson} from '../src/ready-registry.ts';
import {readyFixtures,readyPrepare} from './ready-support.ts';
const r=loadReadyRegistry(),v=r.validator(),base=r.get().bundle.snapshot;
for(const c of readyFixtures.cases)test('ready contract: '+c.id,()=>{
 const doc=readyPrepare(base,c.changes),before=JSON.stringify(doc);
 if(c.valid){v.validate(doc);const state=v.readiness(doc,c.facts);assert.equal(state.content_ready,c.ready);assert.equal(state.publication_enabled,false);}
 else assert.throws(()=>v.validate(doc));
 assert.equal(JSON.stringify(doc),before);
});
test('ready registry returns independent copies',()=>{const a=r.get();a.bundle.snapshot.content.slots.identity_name.value='changed';assert.equal(r.get().bundle.snapshot.content.slots.identity_name.value,'');const d=structuredClone(base);d.customization.style_overrides.colors={accent:'#FFFFFF'};assert.equal(v.validate(d).palette.accent,'#FFFFFF');delete d.customization.style_overrides.colors;assert.equal(v.validate(d).palette.accent,'#D5EB90');assert.throws(()=>v.readiness(base,{publication_enabled:true}));});
for(const raw of ['{"x":1,"x":2}','{"x":{"a":1,"a":2}}','[1,]','{"x":NaN}','\uFEFF{}','{"x":"\\ud800"}'])test('strict offline JSON rejects '+JSON.stringify(raw),()=>assert.throws(()=>strictReadyJson(Buffer.from(raw))));
