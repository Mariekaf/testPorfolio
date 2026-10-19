import type {CSSProperties} from 'react';
import {effectiveSections,safeProjectUrl,type Snapshot,type ContentSection} from '../../lib/template-render';
import theme from '../../../../../contracts/themes/studio-neutral.v1.json';
import styles from './portfolio-renderer.module.css';

function Content({content,anchor,demonstration}:{content:ContentSection;anchor:string;demonstration:boolean}) {
 switch(content.type){
  case 'hero':return <><p className={styles.eyebrow}>UX/UI DESIGN{demonstration?' · PROFIL FICTIF':''}</p><h1>{content.data.title}</h1><p className={styles.intro}>{content.data.subtitle}</p><a className={styles.action} href={`#${anchor}`}>{content.data.cta_label}<svg aria-hidden="true" width="15" height="15" viewBox="0 0 20 20"><path d="M4 16 16 4M4 4h12v12" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></a></>;
  case 'about':return <><h2>{content.data.heading}</h2><p className={styles.body}>{content.data.body}</p></>;
  case 'projects':return <><div className={styles.sectionHeading}><h2>{content.data.heading}</h2><span>01 — 03 / ÉTUDES FICTIVES</span></div><div className={styles.projects}>{content.data.items.map((project,index)=>{
   const href=safeProjectUrl(project.url);
   return <article className={styles.project} key={project.id}><div className={styles.art} data-art={index%3} aria-hidden="true"><div className={styles.artWindow}><span className={styles.artLabel}>{['CLAIR','TEMPO','LISIÈRE'][index%3]}</span><div className={styles.artRows}><i/><i/><i/></div><div className={styles.artBlocks}><i/><i/><i/></div></div><span className={styles.artNumber}>0{index+1}</span></div><div className={styles.projectText}><p className={styles.eyebrow}>ÉTUDE DE CAS / 0{index+1}</p><h3>{href?<a href={href} target="_blank" rel="noopener noreferrer">{project.title}</a>:project.title}</h3><p>{project.summary}</p></div></article>;
  })}</div></>;
  case 'skills':return <><h2>{content.data.heading}</h2><ul className={styles.skills}>{content.data.items.map((skill,i)=><li key={i}>{skill}</li>)}</ul></>;
  case 'contact':return <><p className={styles.eyebrow}>LA SUITE COMMENCE ICI</p><h2>{content.data.heading}</h2><p className={styles.body}>{content.data.body}</p>{content.data.email&&<p>{content.data.email}</p>}</>;
 }
}
/** Exact same renderer accepts a validated catalogue OR future instance snapshot. */
export default function PortfolioRenderer({snapshot,scope='portfolio-preview',demonstration=false}:{snapshot:Snapshot;scope?:string;demonstration?:boolean}) {
 const sections=effectiveSections(snapshot);
 const projectId=sections.find(s=>s.section.type==='projects')?.section.id??sections[0]?.section.id;
 const tokens=theme.tokens.light;
 const variables={'--tpl-bg':tokens.background,'--tpl-surface':tokens.surface,'--tpl-text':tokens.text,'--tpl-muted':tokens.muted,'--tpl-accent':tokens.accent,'--tpl-line':tokens.line} as CSSProperties;
 return <div className={styles.container} style={variables}><article className={styles.portfolio} data-layout={snapshot.composition.layout} data-template={snapshot.composition.template.id} aria-label={`Portfolio ${snapshot.composition.template.id}`}>
  <header className={styles.masthead}><span>Portfolio · UX/UI<span aria-hidden="true"> ✳</span></span><span>DESIGNER UX/UI{demonstration?' / DÉMONSTRATION':''}</span></header>
  <div className={styles.sections}>{sections.map(({section,content,settings},index)=><section key={section.id} id={`${scope}-${section.id}`} className={styles.section} data-section={section.type} data-variant={section.variant} data-spacing={settings.spacing} data-align={settings.alignment} data-emphasis={settings.emphasis}>
   <span className={styles.sectionIndex} aria-hidden="true">0{index+1} / {section.type==='about'?'À PROPOS':section.type.toUpperCase()}</span><div className={styles.sectionContent}><Content content={content} anchor={`${scope}-${projectId}`} demonstration={demonstration}/></div>
  </section>)}</div><footer className={styles.footer}><span>Portfolio · UX/UI Design</span>{demonstration&&<span>Contenus et projets fictifs</span>}</footer>
 </article></div>;
}
