/** Test tooling only: reads public repository contracts, never local configuration. */
import {readFileSync} from 'node:fs';
import type {HeroResolutionContracts} from '../src/hero-resolution.ts';
export function readContracts(): HeroResolutionContracts {
  const root = new URL('../../../contracts/',import.meta.url);
  const paths = ['hero/hero-config.v1.json','hero/capabilities.v1.json',
    'templates/documents/snapshot.v2.json','templates/documents/composition.v2.json',
    'templates/documents/presentation.v2.json','templates/documents/customization.v2.json',
    'templates/documents/content.v1.json'];
  return {schemas:Object.fromEntries(paths.map(path=>[path,JSON.parse(readFileSync(new URL('schemas/'+path,root),'utf8'))])),
    capabilities:JSON.parse(readFileSync(new URL('hero/capabilities.v1.json',root),'utf8'))};
}
export function prepare(base: any, changes: any[]): any {
  const result = structuredClone(base);
  for (const change of changes) {
    const keys: string[] = change.path.split('/').slice(1);
    let node = result;
    for (const key of keys.slice(0,-1)) node=node[key];
    const key = keys[keys.length-1];
    if (change.remove) { if (Array.isArray(node)) node.splice(Number(key),1); else delete node[key]; }
    else node[key]=structuredClone(change.value);
  }
  return result;
}
export function readResolutionFixtures(): any {
  return JSON.parse(readFileSync(new URL('../../../contracts/fixtures/hero/resolution.v1.json',import.meta.url),'utf8'));
}
