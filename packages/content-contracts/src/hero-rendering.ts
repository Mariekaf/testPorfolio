/** E.05 implementation registry, separate from frozen E.02 declarations. */
import registry from '../../../contracts/hero/renderer.v1.json' with {type:'json'};
import type {EffectiveHero} from './hero-resolution.ts';
export class HeroRenderingError extends Error {
  constructor(message:string){super(message);this.name='HeroRenderingError';}
}
export function requireHeroRenderingEnabled(enabled:boolean):void {
  if(enabled !== true) throw new HeroRenderingError('Modular Hero rendering is disabled.');
}
export function requireRenderableHero(hero:EffectiveHero):void {
  const entry=registry.layouts.find(x=>x.id===hero.layout.id && x.version===hero.layout.version);
  if(!entry?.implemented) throw new HeroRenderingError('Hero layout is not implemented by this renderer.');
  for(const capability of ['palette',hero.appearance.background.kind,hero.appearance.typography.family,hero.appearance.surface.kind]) {
    if(!registry.appearance.includes(capability)) throw new HeroRenderingError('Hero appearance is not implemented.');
  }
  if(hero.behavior.kind!=='none') throw new HeroRenderingError('Hero behavior is not implemented.');
}
