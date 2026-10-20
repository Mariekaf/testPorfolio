import type {CSSProperties} from 'react';
import {resolveFixtureMedia,type MediaReference,type FixtureMediaContext} from '../../../../../packages/content-contracts/src/ready-fixture-media.ts';
import styles from './creative-editorial-renderer.module.css';

type Data=Record<string,any>;
const nonblank=(text:string)=>text.replace(/[\s\u0085\uFEFF]/g,'').length>0;
const labels:Record<string,string>={hero:'Accueil',about:'Présentation',projects:'Projets',contact:'Contact'};
function link(target:Data|null,scope:string):string|undefined{
 if(!target)return undefined;
 return target.kind==='section'?`#${scope}-${target.section_id}`:target.kind==='email'?`mailto:${target.address}`:target.url;
}
function RichText({blocks}:{blocks:Data[]}){
 return <>{blocks.filter(p=>p.children.some((c:Data)=>nonblank(c.text))).map((p,i)=><p key={i}>{p.children.map((c:Data,n:number)=>{
  let text=<span>{c.text}</span>;
  if(c.marks.includes('emphasis'))text=<em>{text}</em>;
  if(c.marks.includes('strong'))text=<strong>{text}</strong>;
  return <span key={n}>{text}</span>;
 })}</p>)}</>;
}
function ImageSlot({reference,media,kind}:{reference:MediaReference|null;media?:FixtureMediaContext;kind:'portrait'|'cover'|'logo'}){
 const resolved=resolveFixtureMedia(reference,media);
 if(resolved.state==='available')return <img className={styles.image} src={resolved.src} width={resolved.width} height={resolved.height}
  alt={reference!.alt} loading={kind==='portrait'||kind==='logo'?'eager':'lazy'} decoding="async"
  style={{objectPosition:`${reference!.focal_point.x*100}% ${reference!.focal_point.y*100}%`}}/>;
 if(kind==='logo')return null;
 const description=resolved.state==='processing'?'Image en préparation':'Image à compléter ou indisponible';
 return <div className={styles.imagePlaceholder} data-media-state={resolved.state} role="img" aria-label={description}>
  <div className={styles.placeholderArt} aria-hidden="true"><i/><i/><i/></div><span>{description}</span>
 </div>;
}
/** Isolated, explicit opt-in. No routes, writes, conversion, uploads or public rendering. */
export default function CreativeEditorialView({document,effective,media,enabled=false,scope='creative',demonstration=false,embedded=false}:{
 document:unknown;effective:Data;media?:FixtureMediaContext;enabled?:boolean;scope?:string;demonstration?:boolean;embedded?:boolean;
}){
 if(enabled!==true)throw new Error('Creative Editorial rendering is disabled.');
 if(!/^[a-z][a-z0-9-]{0,60}$/.test(scope))throw new Error('Invalid preview scope.');
 const doc=document as Data,s=doc.content.slots,p=effective.palette;
 const visible=new Set<string>(effective.visible_sections),projects=s.selected_projects.items.filter((item:Data)=>nonblank(item.title));
 const navigationSections=['about','projects','contact'].filter(id=>visible.has(id));
 const href=(value:Data)=>nonblank(value.label)?link(value.target,scope):undefined;
 const contact=href(s.contact_link),socials=s.socials.items.filter((item:Data)=>nonblank(item.label));
 const Main=embedded?'div':'main';
 const variables={'--ce-bg':p.background,'--ce-surface':p.surface,'--ce-text':p.text,'--ce-accent':p.accent,
  '--ce-font':effective.font_ref.id==='system-serif'?'ui-serif,Georgia,"Times New Roman",serif':'ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif'} as CSSProperties;
 return <article className={styles.portfolio} style={variables} data-ready-template="creative-editorial" data-ready-version="1.0.0" aria-label="Aperçu du portfolio Creative Editorial">
  <a className={styles.skipLink} href={`#${scope}-hero`}>Aller au contenu</a>
  <div className={styles.previewNote}>{demonstration?'Démonstration synthétique · contenus et illustrations fictifs':'Brouillon · aperçu local non publié'}</div>
  <header id={`${scope}-navigation`} className={styles.navigation} data-ready-section="navigation">
   <a className={styles.identity} href={`#${scope}-hero`}>
    <span className={styles.logo}><ImageSlot reference={s.brand_logo.value} media={media} kind="logo"/></span>
    <span>{nonblank(s.identity_name.value)?s.identity_name.value:'Identité à compléter'}</span>
   </a>
   {navigationSections.length>0&&<nav aria-label="Navigation du portfolio"><ul>{navigationSections.map(id=><li key={id}><a href={`#${scope}-${id}`}>{labels[id]}</a></li>)}</ul></nav>}
  </header>
  <Main>
   <section className={styles.hero} id={`${scope}-hero`} tabIndex={-1} data-ready-section="hero" aria-labelledby={`${scope}-title`}>
    <div className={styles.heroCopy}>
     <p className={styles.eyebrow}>PORTFOLIO / UX &amp; UI</p>
     <h1 id={`${scope}-title`}>{nonblank(s.hero_title.value)?s.hero_title.value:'Votre titre — brouillon'}</h1>
     {nonblank(s.hero_subtitle.value)&&<p className={styles.heroSubtitle}>{s.hero_subtitle.value}</p>}
     {href(s.hero_cta)&&<a className={styles.button} href={href(s.hero_cta)}><span className={styles.actionLabel}>{s.hero_cta.label}</span><span className={styles.arrow} aria-hidden="true"/></a>}
    </div>
    <div className={styles.heroPortrait}><ImageSlot reference={s.hero_portrait.value} media={media} kind="portrait"/><span className={styles.orbit} aria-hidden="true"/></div>
    <span className={styles.heroRule} aria-hidden="true"/>
   </section>
   {visible.has('about')&&<section id={`${scope}-about`} tabIndex={-1} className={styles.about} data-ready-section="about" aria-labelledby={`${scope}-about-heading`}>
    <div className={styles.sectionLabel}><span aria-hidden="true">01 /</span><span>Présentation</span></div>
    <h2 id={`${scope}-about-heading`}>{nonblank(s.about_heading.value)?s.about_heading.value:'Présentation'}</h2>
    <div className={styles.aboutBody}><RichText blocks={s.about_body.blocks}/></div>
   </section>}
   {visible.has('projects')&&<section id={`${scope}-projects`} tabIndex={-1} className={styles.projects} data-ready-section="projects" aria-labelledby={`${scope}-projects-heading`}>
    <div className={styles.sectionLabel}><span aria-hidden="true">02 /</span><span>Projets sélectionnés</span></div>
    <h2 id={`${scope}-projects-heading`}>{nonblank(s.projects_heading.value)?s.projects_heading.value:'Projets sélectionnés'}</h2>
    <div className={styles.projectGrid}>{projects.map((item:Data,index:number)=><article className={styles.project} key={item.id} data-project-id={item.id}>
     <div className={styles.projectCover}><ImageSlot reference={item.cover} media={media} kind="cover"/></div>
     <div className={styles.projectMeta}><span aria-hidden="true">{String(index+1).padStart(2,'0')}</span><div>
      <h3>{item.target?<a href={link(item.target,scope)} rel="noopener noreferrer">{item.title}<span className={styles.arrow} aria-hidden="true"/></a>:item.title}</h3>
      {nonblank(item.summary)&&<p>{item.summary}</p>}
     </div></div>
    </article>)}</div>
   </section>}
   {visible.has('contact')&&<section id={`${scope}-contact`} tabIndex={-1} className={styles.contact} data-ready-section="contact" aria-labelledby={`${scope}-contact-heading`}>
    <div className={styles.sectionLabel}><span aria-hidden="true">03 /</span><span>Contact</span></div>
    <h2 id={`${scope}-contact-heading`}>{nonblank(s.contact_heading.value)?s.contact_heading.value:'Contact'}</h2>
    {contact&&<a className={styles.contactLink} href={contact}><span className={styles.actionLabel}>{s.contact_link.label}</span><span className={styles.arrow} aria-hidden="true"/></a>}
    {socials.length>0&&<ul className={styles.socials} aria-label="Réseaux et liens">{socials.map((item:Data)=><li key={item.network}><a href={link(item.target,scope)} rel="noopener noreferrer">{item.label}</a></li>)}</ul>}
   </section>}
  </Main>
  <footer id={`${scope}-footer`} className={styles.footer} data-ready-section="footer">{nonblank(s.footer_note.value)&&<p>{s.footer_note.value}</p>}<a href={`#${scope}-hero`}>Retour en haut ↑</a></footer>
 </article>;
}
