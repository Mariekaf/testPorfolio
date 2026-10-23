'use client';
import Link from 'next/link';
import {PANELS,PANEL_LABELS,editorPath,templateName,type Panel,type PortfolioContext} from '../lib/portfolio-navigation';
import styles from './portfolio-navigation.module.css';
export default function PortfolioNavigation({portfolio,active,panel,onPanel,supported=true,unavailableReason}:{portfolio:PortfolioContext;active:'overview'|'settings'|'editor';panel?:Panel|null;onPanel?:(panel:Panel)=>void;supported?:boolean;unavailableReason?:string}) {
  const path=supported?editorPath(portfolio):null;
  const template=templateName(portfolio.source_template_id);
  return <aside className={styles.navigation}>
    <Link className={styles.back} href="/dashboard">← Mes portfolios</Link>
    <p className="eyebrow">PORTFOLIO SÉLECTIONNÉ</p><strong>{portfolio.name}</strong>
    <p className={styles.context}>{template} · {portfolio.management_state==='archived'?'Archivé · lecture seule':'Brouillon privé'}</p>
    <nav aria-label="Espace portfolio">
      <Link aria-current={active==='overview'?'page':undefined} href={`/portfolios/${portfolio.id}`}>Vue d’ensemble</Link>
      {PANELS.map(key=>path?<a key={key} href={`${path}?panel=${key}`} aria-current={active==='editor'&&(panel??'sections')===key?'page':undefined} onClick={e=>{if(onPanel&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey&&e.button===0){e.preventDefault();onPanel(key);}}}>{PANEL_LABELS[key]}</a>:<span key={key} className={styles.unavailable}>{PANEL_LABELS[key]} — indisponible</span>)}
      {portfolio.management_state==='active'?<Link aria-current={active==='settings'?'page':undefined} href={`/portfolios/${portfolio.id}/settings`}>Paramètres</Link>:<span className={styles.unavailable}>Paramètres — restaurez le portfolio</span>}
    </nav>
    {!path&&<p className={styles.context}>{unavailableReason||(portfolio.source_template_id?'Cette version ne dispose pas d’un éditeur compatible.':'Aucun template associé. Créez un autre portfolio depuis la bibliothèque.')}</p>}
    {!portfolio.source_template_id&&<Link href="/templates">Choisir un template pour un nouveau portfolio</Link>}
    <p className={styles.context}>Publication publique indisponible</p>
  </aside>;
}
