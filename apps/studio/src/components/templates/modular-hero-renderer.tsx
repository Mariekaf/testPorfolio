import type {CSSProperties} from 'react';
import {heroResolver} from '../../../../../packages/content-contracts/src/hero-runtime.ts';
import {HeroRenderingError,requireHeroRenderingEnabled,requireRenderableHero} from '../../../../../packages/content-contracts/src/hero-rendering.ts';
import styles from './modular-hero-renderer.module.css';

type Props={snapshot:unknown;sectionId:string;enabled?:boolean;scope?:string;continuationId?:string};
/** Explicit opt-in only. No fetch, writes, conversion, client JS, or legacy fallback. */
export default function ModularHeroRenderer({snapshot,sectionId,enabled=false,scope='modular-hero',continuationId}:Props){
  requireHeroRenderingEnabled(enabled);
  if(!/^[a-zA-Z][a-zA-Z0-9_-]{0,79}$/.test(scope)) throw new HeroRenderingError('Invalid Hero scope.');
  if(continuationId !== undefined && !/^[a-zA-Z][a-zA-Z0-9_-]{0,159}$/.test(continuationId)) throw new HeroRenderingError('Invalid continuation target.');
  const resolved=heroResolver.resolve(snapshot);
  const hero=resolved.heroes.find(item=>item.section_id===sectionId);
  if(!hero) throw new HeroRenderingError('Hero section is missing.');
  requireRenderableHero(hero);
  if(!hero.visible)return null;
  const {appearance,layout,content}=hero;
  if(!content.title.trim()) throw new HeroRenderingError('Hero heading must contain accessible text.');
  const background=appearance.background.kind==='solid'?appearance.background.color:
    `linear-gradient(${appearance.background.angle}deg, ${appearance.background.stops.map(stop=>`${stop.color} ${stop.position}%`).join(', ')})`;
  const variables:Record<string,string>={
    '--hero-text':appearance.palette.text,'--hero-surface':appearance.palette.surface,
    '--hero-accent':appearance.palette.accent,'--hero-background':background,
    '--hero-type':({compact:'0.85',balanced:'1',display:'1.15'})[appearance.typography.scale],
    '--hero-blur':appearance.surface.kind==='glass'?`${appearance.surface.blur}px`:'0px',
    '--hero-opacity':appearance.surface.kind==='glass'?String(appearance.surface.opacity/100):'1',
  };
  for(const bp of ['mobile','tablet','desktop'] as const){
    const setting=layout.settings[bp];
    variables[`--hero-space-${bp}`]=({compact:'1.25rem',normal:'2.5rem',airy:'4rem'})[setting.spacing];
    variables[`--hero-align-${bp}`]=setting.alignment==='start'?'left':'center';
    variables[`--hero-items-${bp}`]=setting.alignment==='start'?'start':'center';
    variables[`--hero-weight-${bp}`]=setting.emphasis==='strong'?'800':'600';
  }
  const heading=`${scope}-${sectionId}-title`;
  return <section className={styles.hero} data-hero-layout={layout.id} data-hero-version={layout.version}
    data-hero-surface={appearance.surface.kind} aria-labelledby={heading} style={variables as CSSProperties}>
    <div className={styles.frame}>
      <div className={styles.decoration} aria-hidden="true"><span/><span/><span/></div>
      <div className={styles.copy}>
        <p className={styles.eyebrow}>UX / UI DESIGN</p>
        <h1 id={heading} className={styles.title}>{content.title}</h1>
        <p className={styles.subtitle}>{content.subtitle}</p>
        {content.cta_label.trim() && continuationId && <a className={styles.cta} href={`#${continuationId}`}><span className={styles.ctaLabel}>{content.cta_label}</span><span className={styles.arrow} aria-hidden="true"/></a>}
      </div>
      {layout.id==='typographic' && <div className={styles.signature} aria-hidden="true">DESIGN<br/>WITH INTENT.</div>}
      {layout.id==='fullscreen' && <span className={styles.index} aria-hidden="true">01 — PORTFOLIO</span>}
    </div>
  </section>;
}
