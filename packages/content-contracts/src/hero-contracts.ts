/** E.02 declarations only. No resolver, renderer, parser or persistence activation.
 * TypeScript types are not runtime validation; JSON Schema + semantic checks apply.
 */
export type HeroLayoutId = 'centered' | 'split-screen' | 'fullscreen' | 'typographic'
  | 'asymmetric' | 'product-showcase' | 'bento-grid';
export type HeroSettings = {
  spacing?: 'compact' | 'normal' | 'airy';
  alignment?: 'start' | 'center';
  emphasis?: 'quiet' | 'strong';
};
export type HeroPalette = Partial<Record<'text' | 'surface' | 'accent', string>>;
export type HeroBackground = {kind: 'solid'; color: string} | {
  kind: 'gradient'; angle: number; stops: {color: string; position: number}[];
};
export type HeroSurface = {kind: 'flat'} | {kind: 'glass'; opacity: number; blur: number};
export type HeroAppearance = {
  palette?: HeroPalette;
  typography?: {family?: 'system-sans'; scale?: 'compact' | 'balanced' | 'display'};
  background?: HeroBackground;
  surface?: HeroSurface;
};
export type HeroConfig = {
  schema_version: 1;
  layout?: {
    id: HeroLayoutId; version: string; settings?: HeroSettings;
    responsive?: {tablet?: HeroSettings; desktop?: HeroSettings};
  };
  appearance?: HeroAppearance;
  behavior?: {kind: 'none'};
};
/** E.02 status describes the modular runtime, never the historical v1 renderer. */
export type HeroCapabilityDeclaration = {
  id: string; version: string; declared: true; implemented: false; selectable: false;
  requires: ('content-v2' | 'media-assets')[];
};
export type HeroCapabilityRegistry = {
  schema_version: 1; design_schema_version: 2; hero_schema_version: 1;
  runtime_enabled: false;
  layouts: (HeroCapabilityDeclaration & {id: HeroLayoutId})[];
  appearance: HeroCapabilityDeclaration[];
  behaviors: (HeroCapabilityDeclaration & {id: 'none'})[];
};
export type HeroFixtureCase = {
  id: string;
  target: 'hero' | 'design' | 'registry' | 'selection';
  stage: 'semantic';
  valid: boolean;
  document: unknown;
};
export type HeroFixtureCorpus = {
  schema_version: 1; description: string; cases: HeroFixtureCase[];
};
