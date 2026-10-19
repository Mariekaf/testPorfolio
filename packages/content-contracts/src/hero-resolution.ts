/** E.03 offline/pure resolution. Nothing imports this from the active Studio.
 * Schemas and registry are explicit trusted build inputs, never user documents.
 */
import {Ajv2020} from 'ajv/dist/2020.js';
import type {AnySchemaObject} from 'ajv';
import type {HeroSettings, HeroLayoutId, HeroBackground, HeroSurface} from './hero-contracts.ts';

type Data = Record<string, any>;
export type HeroResolutionContracts = {schemas: Record<string, AnySchemaObject>; capabilities: unknown};
export type EffectiveHero = {
  section_id: string; visible: boolean; content: {title: string; subtitle: string; cta_label: string};
  layout: {id: HeroLayoutId; version: string; settings: Record<'mobile'|'tablet'|'desktop', Required<HeroSettings>>};
  appearance: {
    palette: Record<'text'|'surface'|'accent', string>;
    typography: {family:'system-sans'; scale:'compact'|'balanced'|'display'};
    background: HeroBackground; surface: HeroSurface;
  };
  behavior: {kind: 'none'};
};
export type HeroResolution = {schema_version: 1; design_schema_version: 2; heroes: EffectiveHero[]};
export class HeroResolutionError extends Error {
  constructor() { super('Invalid or unsupported Hero contract.'); this.name = 'HeroResolutionError'; }
}
function requireValue(value: unknown): asserts value { if (!value) throw new HeroResolutionError(); }
const own = (object: Data, key: string) => Object.hasOwn(object, key);
const layouts = ['centered','split-screen','fullscreen','typographic','asymmetric','product-showcase','bento-grid'];
const appearanceIds = ['palette','solid','gradient','system-sans','flat','glass'];
const variants: Record<string, string[]> = {
  hero:['hero-centered','hero-split'], about:['about-compact','about-column'],
  projects:['projects-grid','projects-featured'], skills:['skills-list','skills-sidebar'], contact:['contact-simple','contact-panel'],
};
const schemaBase = 'https://portfolio-contracts.invalid/schemas/';

/** Match Python's UTF-8 JSON size policy, including separators ', ' and ': '. */
function boundedJson(value: unknown): string {
  const ancestors = new Set<object>();
  function inspect(v: unknown, depth: number): void {
    requireValue(depth <= 128);
    if (typeof v === 'string') { requireValue(!/[\uD800-\uDFFF]/u.test(v)); return; }
    if (v === null || typeof v === 'boolean') return;
    if (typeof v === 'number') { requireValue(Number.isFinite(v)); return; }
    requireValue(typeof v === 'object' && !ancestors.has(v as object));
    requireValue(Array.isArray(v) || Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null);
    ancestors.add(v as object);
    for (const [key, child] of Object.entries(v as object)) { inspect(key, depth+1); inspect(child, depth+1); }
    ancestors.delete(v as object);
  }
  inspect(value, 0);
  const compact = JSON.stringify(value);
  let inString = false, escaped = false, serialized = '';
  for (const char of compact) {
    serialized += char;
    if (inString) { if (escaped) escaped = false; else if (char === '\\') escaped = true; else if (char === '"') inString = false; }
    else if (char === '"') inString = true;
    else if (char === ',' || char === ':') serialized += ' ';
  }
  requireValue(new TextEncoder().encode(serialized).length <= 262144);
  return compact;
}

export function contrastRatio(first: string, second: string): number {
  function luminance(color: string): number {
    requireValue(typeof color === 'string' && /^#[0-9A-Fa-f]{6}$/.test(color) && color.length === 7);
    const channels = [1,3,5].map(i => parseInt(color.slice(i,i+2),16)/255)
      .map(x => x <= .04045 ? x/12.92 : ((x+.055)/1.055)**2.4);
    return channels[0]*.2126 + channels[1]*.7152 + channels[2]*.0722;
  }
  const values = [luminance(first), luminance(second)].sort((a,b)=>b-a);
  return (values[0]+.05)/(values[1]+.05);
}
function checkAppearance(value: Data, complete=false): void {
  const palette = value.palette ?? {};
  if (complete) requireValue(['text','surface','accent'].every(key=>own(palette,key)) && Object.keys(palette).length===3);
  if (own(palette,'surface')) for (const key of ['text','accent']) if (own(palette,key)) requireValue(contrastRatio(palette[key],palette.surface)>=4.5);
  if (value.background?.kind==='gradient') {
    const positions = value.background.stops.map((s: Data)=>s.position);
    requireValue(positions.every((p: number,i: number)=>i===0 || p>positions[i-1]));
  }
}

const resetPaths = new Set(['','layout','appearance','behavior','layout/settings','layout/responsive',
  'appearance/palette','appearance/typography','appearance/background','appearance/surface']);
for (const key of ['spacing','alignment','emphasis']) resetPaths.add(`layout/settings/${key}`);
for (const breakpoint of ['tablet','desktop']) {
  resetPaths.add(`layout/responsive/${breakpoint}`);
  for (const key of ['spacing','alignment','emphasis']) resetPaths.add(`layout/responsive/${breakpoint}/${key}`);
}
for (const key of ['text','surface','accent']) resetPaths.add(`appearance/palette/${key}`);
for (const key of ['family','scale']) resetPaths.add(`appearance/typography/${key}`);

export function createHeroResolver(contracts: HeroResolutionContracts) {
  // Clone trusted inputs once: changing the caller's registry later has no effect.
  const schemas = structuredClone(contracts.schemas);
  const capabilities = structuredClone(contracts.capabilities) as Data;
  const ajv = new Ajv2020({strict: true, strictTypes: false, strictRequired: false,
    allErrors:false, coerceTypes:false, removeAdditional:false, useDefaults:false});
  // Same format policy as pinned Python jsonschema: email '@', canonical UUID.
  // URI syntax is not a registered Python format; HTTPS safety is semantic below.
  ajv.addFormat('email', {type:'string', validate:(s: string)=>s.includes('@')});
  ajv.addFormat('uuid', {type:'string', validate:(s:string)=>s.length===36 && /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(s)});
  ajv.addFormat('uri', true);
  for (const [key, schema] of Object.entries(schemas)) {
    requireValue(!schema.$id && key === new URL(key,schemaBase).href.slice(schemaBase.length));
    ajv.addSchema({...schema, $id:new URL(key,schemaBase).href});
  }
  function checkSchema(key: string, value: unknown) {
    boundedJson(value);
    const validate = ajv.getSchema(new URL(key,schemaBase).href);
    requireValue(validate && validate(value));
  }
  checkSchema('hero/capabilities.v1.json',capabilities);
  for (const [group, expected] of [['layouts',layouts],['appearance',appearanceIds],['behaviors',['none']]] as const) {
    const entries = capabilities[group] as Data[];
    requireValue(entries.length===expected.length && new Set(entries.map(e=>e.id)).size===expected.length);
    for (const entry of entries) {
      requireValue((expected as readonly string[]).includes(entry.id) && entry.version==='1.0.0' && !entry.implemented && !entry.selectable);
      const needs = group==='layouts' && entry.id==='product-showcase' ? ['content-v2','media-assets'] : group==='layouts' && entry.id==='bento-grid' ? ['content-v2'] : [];
      requireValue(JSON.stringify(entry.requires)===JSON.stringify(needs));
    }
  }
  function declared(layout: Data) { requireValue(capabilities.layouts.some((e: Data)=>e.id===layout.id && e.version===layout.version)); }
  function checkSettings(settings: Data, policy: Data) { requireValue(Object.entries(settings).every(([key,value])=>policy[key].includes(value))); }
  function checkHero(hero: Data) {
    checkSchema('hero/hero-config.v1.json',hero);
    if (hero.layout) declared(hero.layout);
    if (hero.appearance) checkAppearance(hero.appearance);
  }
  function checkDesign(input: unknown): asserts input is Data {
    checkSchema('templates/documents/snapshot.v2.json',input);
    const doc = input as Data;
    const sections = doc.composition.sections as Data[];
    const ids = sections.map(s=>s.id);
    requireValue(new Set(ids).size===ids.length);
    const byId = new Map(sections.map(s=>[s.id,s]));
    const index = doc.composition.layout==='minimal-stack' ? 0 : 1;
    for (const section of sections) {
      requireValue(variants[section.type].includes(section.variant) && section.variant===variants[section.type][index]);
      requireValue(!section.required || section.visible);
      for (const values of Object.values(section.presentation_policy) as unknown[][]) requireValue(new Set(values).size===values.length);
    }
    for (const name of ['content','presentation']) {
      const refs = doc[name].sections.map((s:Data)=>s.section_id);
      requireValue(refs.length===ids.length && new Set(refs).size===ids.length && refs.every((id:string)=>byId.has(id)));
    }
    const projects = new Set<string>();
    for (const section of doc.content.sections) {
      requireValue(section.type===byId.get(section.section_id)!.type);
      if (section.type==='projects') for (const project of section.data.items) {
        requireValue(!projects.has(project.id)); projects.add(project.id);
        if (project.url!==null) {
          requireValue(!/[\x00-\x20]/.test(project.url));
          requireValue(/^https:\/\/[^/?#]+/i.test(project.url));
          const url = new URL(project.url);
          requireValue(url.protocol==='https:' && url.hostname && !url.username && !url.password);
        }
      }
    }
    for (const presentation of doc.presentation.sections) {
      const source = byId.get(presentation.section_id)!;
      checkSettings(presentation.settings,source.presentation_policy);
      requireValue(own(presentation,'hero')===(source.type==='hero'));
      if (source.type!=='hero') continue;
      const layout = source.hero.layout;
      declared(layout); requireValue(!['product-showcase','bento-grid'].includes(layout.id));
      const allowed = source.hero.policy.layouts as Data[];
      for (const pair of allowed) declared(pair);
      requireValue(new Set(allowed.map(p=>`${p.id}@${p.version}`)).size===allowed.length);
      requireValue(allowed.some(p=>p.id===layout.id && p.version===layout.version));
      checkAppearance(presentation.hero.appearance,true);
      checkSettings(layout.settings,source.presentation_policy);
      for (const settings of Object.values(layout.responsive ?? {}) as Data[]) checkSettings(settings,source.presentation_policy);
    }
    const overrides = doc.customization.sections as Data[];
    requireValue(new Set(overrides.map(s=>s.section_id)).size===overrides.length);
    for (const override of overrides) {
      const source = byId.get(override.section_id); requireValue(source);
      if (own(override,'visible')) requireValue((source.toggleable || override.visible===source.visible) && (!source.required || override.visible));
      checkSettings(override.presentation ?? {},source.presentation_policy);
      if (!own(override,'hero')) continue;
      requireValue(source.type==='hero'); checkHero(override.hero);
      if (override.hero.layout) {
        const layout = override.hero.layout;
        requireValue(!['product-showcase','bento-grid'].includes(layout.id));
        requireValue(source.hero.policy.layouts.some((p:Data)=>p.id===layout.id && p.version===layout.version));
        checkSettings(layout.settings ?? {},source.presentation_policy);
        for (const settings of Object.values(layout.responsive ?? {}) as Data[]) checkSettings(settings,source.presentation_policy);
      }
    }
    const order = doc.customization.section_order ?? ids;
    requireValue(order.length===ids.length && new Set(order).size===ids.length && order.every((id:string)=>byId.has(id)));
    requireValue(sections.every((s,i)=>s.reorderable || order[i]===s.id));
  }
  function resolve(input: unknown): HeroResolution {
    try {
      checkDesign(input);
      const doc = input;
      const heroes: EffectiveHero[] = [];
      const order = doc.customization.section_order ?? doc.composition.sections.map((s:Data)=>s.id);
      for (const identity of order) {
        const section = doc.composition.sections.find((s:Data)=>s.id===identity);
        if (section.type!=='hero') continue;
        const presentation = doc.presentation.sections.find((s:Data)=>s.section_id===identity);
        const content = doc.content.sections.find((s:Data)=>s.section_id===identity);
        const override = doc.customization.sections.find((s:Data)=>s.section_id===identity) ?? {};
        const hero = override.hero ?? {};
        const source = section.hero.layout;
        const local = hero.layout ?? {};
        const appearance = structuredClone(presentation.hero.appearance);
        for (const [key,value] of Object.entries(hero.appearance ?? {})) {
          if (key==='palette' || key==='typography') Object.assign(appearance[key],structuredClone(value));
          else appearance[key] = structuredClone(value);
        }
        const id = local.id ?? source.id, version = local.version ?? source.version;
        const base = {...presentation.settings,...override.presentation,...source.settings,...local.settings};
        const settings: Data = {};
        for (const breakpoint of ['mobile','tablet','desktop']) {
          settings[breakpoint] = {...base,...(breakpoint==='mobile' ? {} : source.responsive?.[breakpoint]),
            ...(breakpoint==='mobile' ? {} : local.responsive?.[breakpoint])};
          checkSettings(settings[breakpoint],section.presentation_policy);
        }
        const behavior = structuredClone(hero.behavior ?? {kind:'none'});
        checkHero({schema_version:1,layout:{id,version,settings:settings.mobile,
          responsive:{tablet:settings.tablet,desktop:settings.desktop}},appearance,behavior});
        checkAppearance(appearance,true);
        heroes.push({section_id:identity,visible:override.visible ?? section.visible,content:structuredClone(content.data),
          layout:{id,version,settings:settings as EffectiveHero['layout']['settings']},appearance,behavior});
      }
      return {schema_version:1,design_schema_version:2,heroes};
    } catch { throw new HeroResolutionError(); }
  }
  function reset(input: unknown, sectionId: string, path: readonly string[] = []): unknown {
    try {
      checkDesign(input);
      requireValue(Array.isArray(path) && path.every(k=>typeof k==='string' && !k.includes('/')) && resetPaths.has(path.join('/')));
      requireValue(input.composition.sections.some((s:Data)=>s.id===sectionId && s.type==='hero'));
      const result = structuredClone(input);
      const override = result.customization.sections.find((s:Data)=>s.section_id===sectionId);
      if (override?.hero) {
        if (!path.length) delete override.hero;
        else {
          let current = override.hero;
          const parents: [Data,string][] = [];
          let found = true;
          for (const key of path.slice(0,-1)) {
            if (!own(current,key)) { found=false; break; }
            parents.push([current,key]); current=current[key];
          }
          if (found) {
            delete current[path[path.length-1]];
            for (const [parent,key] of parents.reverse()) if (!Object.keys(parent[key]).length) delete parent[key];
          }
        }
      }
      resolve(result);
      return result;
    } catch { throw new HeroResolutionError(); }
  }
  return Object.freeze({resolve,reset});
}
