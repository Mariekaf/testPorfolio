import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHeroResolver, contrastRatio, HeroResolutionError} from '../src/hero-resolution.ts';
import {readContracts, readResolutionFixtures, prepare} from './hero-resolution-support.ts';
const fixture=readResolutionFixtures(), resolver=createHeroResolver(readContracts());
function freeze(value:any):any {
  if (value && typeof value==='object') {Object.freeze(value);for (const child of Object.values(value)) freeze(child);}
  return value;
}
for (const c of fixture.cases) test(c.id,()=>{
  const input=prepare(fixture.base_design,c.changes), before=structuredClone(input);
  freeze(input);
  const run=()=>{
    const reset=c.reset ? resolver.reset(input,c.reset.section_id,c.reset.path) : input;
    if (c.reset) assert.deepEqual(resolver.reset(reset,c.reset.section_id,c.reset.path),reset);
    return resolver.resolve(reset);
  };
  if (c.error) assert.throws(run,HeroResolutionError);
  else assert.deepEqual(run(),c.expected);
  assert.deepEqual(input,before);
});
test('result and breakpoint maps do not alias inputs, contracts, or each other',()=>{
  const contracts=readContracts(), r=createHeroResolver(contracts), input=structuredClone(fixture.base_design);
  const first=r.resolve(input), second=r.resolve(input);
  first.heroes[0].layout.settings.mobile.spacing='airy';
  first.heroes[0].appearance.palette.text='#123456';
  first.heroes[0].content.title='changed';
  assert.deepEqual(second,fixture.cases[0].expected);
  assert.equal(first.heroes[0].layout.settings.desktop.spacing,'normal');
  assert.deepEqual(r.resolve(input),second);
  (contracts.capabilities as any).layouts[0].selectable=true;
  assert.deepEqual(r.resolve(input),second);
});
test('WCAG thresholds are not rounded',()=>{
  assert.equal(contrastRatio('#000000','#FFFFFF'),21);
  assert.ok(contrastRatio('#767676','#FFFFFF')>=4.5);
  assert.ok(contrastRatio('#777777','#FFFFFF')<4.5);
});
test('bad non-JSON values and oversized input fail closed',()=>{
  for (const value of [undefined,NaN,Infinity,()=>{},new Date(),null]) assert.throws(()=>resolver.resolve(value),HeroResolutionError);
  const doc=structuredClone(fixture.base_design);doc.content.sections[0].data.title='a'.repeat(262145);
  assert.throws(()=>resolver.resolve(doc),HeroResolutionError);
  const cyclic:any={};cyclic.self=cyclic;assert.throws(()=>resolver.resolve(cyclic),HeroResolutionError);
});
test('runtime registry remains inactive and contracts are not mutated at construction',()=>{
  const contracts=freeze(readContracts()), before=JSON.stringify(contracts);
  assert.deepEqual(createHeroResolver(contracts).resolve(fixture.base_design),fixture.cases[0].expected);
  assert.equal(JSON.stringify(contracts),before);
  assert.equal((contracts.capabilities as any).runtime_enabled,false);
  for(const c of (contracts.capabilities as any).layouts) assert.equal(c.selectable,false);
});
