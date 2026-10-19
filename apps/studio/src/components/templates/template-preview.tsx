'use client';
import {useState} from 'react';
import Link from 'next/link';
import type {Snapshot} from '../../lib/template-render';
import PortfolioRenderer from './portfolio-renderer';
import styles from './template-preview.module.css';
export default function TemplatePreview({snapshot}:{snapshot:Snapshot}){
 const [mode,setMode]=useState<'desktop'|'mobile'>('desktop');
 return <section className={styles.preview}><div className={styles.toolbar}><div><Link href="/templates">← Tous les aperçus</Link><h1>{snapshot.composition.template.id==='minimal'?'Minimal':'Editorial'} <span>{snapshot.composition.template.version}</span></h1><p>Template de démonstration · Aucun portfolio créé</p><Link className="button" href={`/templates/${snapshot.composition.template.id}/${snapshot.composition.template.version}/use`}>Utiliser ce template</Link></div><div className={styles.switcher} role="group" aria-label="Largeur de l’aperçu"><button onClick={()=>setMode('desktop')} aria-pressed={mode==='desktop'}>Desktop</button><button onClick={()=>setMode('mobile')} aria-pressed={mode==='mobile'}>Mobile</button></div></div><div className={styles.canvas}><div className={styles.frame} data-mode={mode} data-testid="template-frame"><PortfolioRenderer snapshot={snapshot} demonstration/></div></div></section>;
}
