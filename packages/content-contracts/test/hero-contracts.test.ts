/** Shared corpus consumption and type contract checks, NOT a TS schema validator. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import type {HeroConfig, HeroFixtureCorpus, HeroLayoutId} from '../src/hero-contracts.ts';

const fixture = JSON.parse(readFileSync(new URL('../../../contracts/fixtures/hero/cases.v1.json', import.meta.url), 'utf8')) as HeroFixtureCorpus;
const layouts: HeroLayoutId[] = ['centered', 'split-screen', 'fullscreen', 'typographic', 'asymmetric', 'product-showcase', 'bento-grid'];
const colorOnly: HeroConfig = {schema_version: 1, appearance: {palette: {accent: '#123456'}}};
const plain: HeroConfig = {schema_version: 1, behavior: {kind: 'none'}};
// @ts-expect-error Arbitrary CSS is not a declared property.
const forbidden: HeroConfig = {schema_version: 1, css: 'body{}'};
// @ts-expect-error Future behavior is not enabled by this contract.
const future: HeroConfig = {schema_version: 1, behavior: {kind: 'parallax'}};
void forbidden; void future;

test('common UTF-8 corpus has unique typed cases and explicit expected results', () => {
  assert.equal(fixture.schema_version, 1);
  assert.equal(new Set(fixture.cases.map(c => c.id)).size, fixture.cases.length);
  for (const c of fixture.cases) {
    assert.ok(['hero', 'design', 'registry', 'selection'].includes(c.target));
    assert.equal(c.stage, 'semantic');
    assert.equal(typeof c.valid, 'boolean');
    assert.equal(typeof c.document, 'object');
  }
  assert.ok(JSON.stringify(fixture).includes('É02'));
});
test('every declared layout has positive color independence and negative selection vectors', () => {
  for (const id of layouts) {
    assert.equal(fixture.cases.find(c => c.id === `palette-independent-${id}`)?.valid, true);
    assert.equal(fixture.cases.find(c => c.id === `not-selectable-${id}`)?.valid, false);
  }
  assert.equal(colorOnly.layout, undefined);
  assert.equal(plain.behavior?.kind, 'none');
});
