'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {readyRequest,type ReadyData,type ReadyRecord} from '../../lib/ready-instances';
import ReadyPreview from './ready-preview';
import styles from './ready-editor.module.css';
export default function ReadySelection(){
 const [template,setTemplate]=useState<ReadyData|null>(null),[name,setName]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const key=useRef<string|null>(null),submitting=useRef(false);
 async function load(){try{setTemplate(await readyRequest('ready-templates'));setError('');}catch(e){setError((e as Error).message);}}
 useEffect(()=>{void load();},[]);
 async function create(e:React.FormEvent){e.preventDefault();if(submitting.current)return;submitting.current=true;setBusy(true);setError('');key.current??=crypto.randomUUID();
  try{const record=await readyRequest<ReadyRecord>('ready-portfolios','POST',{name},{'Idempotency-Key':key.current});window.location.assign(`/portfolios/${record.portfolio.id}/ready`);}
  catch(e){setError((e as Error).message);submitting.current=false;setBusy(false);}
 }
 return <section className={styles.editor}><Link href="/dashboard">← Mes portfolios</Link><h1>Un portfolio prêt à personnaliser</h1><p>Creative Editorial · une composition complète, vos contenus. Création privée et explicite ; aucun portfolio existant ne sera converti.</p>
 {error&&<p role="alert">{error}<button onClick={()=>void load()}>Réessayer la bibliothèque</button></p>}
 {!template?<p role="status">Chargement du template…</p>:<><div className={styles.selection}><div><span className="badge">MVP privé · non publiable</span><h2>Creative Editorial</h2><p>Typographie expressive, portrait, présentation, grille de projets et contact. Remplacez les contenus ; la direction artistique reste en place.</p><form onSubmit={create}><label className="field">Nom du portfolio<input required minLength={3} maxLength={100} value={name} disabled={busy} onChange={e=>{setName(e.target.value);key.current=null;}}/></label><button disabled={busy||name.trim().length<3}>{busy?'Création…':'Créer mon portfolio privé'}</button></form></div><div className={styles.miniature} aria-label="Miniature Creative Editorial"><div><span>VOTRE NOM / UX & UI</span><strong>Vos idées.<br/>Votre regard.</strong><i aria-hidden="true"/><span>PRÉSENTATION / PROJETS / CONTACT</span></div></div></div>
 <details><summary>Voir la composition réelle · brouillon vide</summary><ReadyPreview document={template.snapshot} scope="template-preview"/></details></>}
 </section>;
}
