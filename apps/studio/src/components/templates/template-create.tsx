'use client';
import {useRef,useState,type FormEvent} from 'react';
import Link from 'next/link';
import {creationIntent,instanceRequest} from '../../lib/template-instances';
import {makeSlug,type Portfolio} from '../../lib/portfolios';
import styles from './template-editor.module.css';
export default function TemplateCreate({templateId,version}:{templateId:string;version:string}){
 const [name,setName]=useState(''),[slug,setSlug]=useState(''),[custom,setCustom]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const intent=useRef<ReturnType<typeof creationIntent>|null>(null),payload=useRef<string|null>(null),sending=useRef(false);
 async function submit(event:FormEvent){
  event.preventDefault();if(sending.current)return;sending.current=true;setBusy(true);setError('');
  const body={name:name.trim(),...(slug.trim()?{slug:slug.trim()}:{}),template_id:templateId,template_version:version};
  const encoded=JSON.stringify(body);
  if(payload.current!==encoded){intent.current=creationIntent();payload.current=encoded;}
  if(!intent.current)intent.current=creationIntent();
  if(Date.now()-intent.current.createdAt>=24*3600*1000){setError('Cette intention a expiré. Vérifiez vos portfolios avant de recommencer.');setBusy(false);sending.current=false;return;}
  try{const item=await instanceRequest<Portfolio>('/from-template','POST',body,{'Idempotency-Key':intent.current.key});window.location.assign(`/portfolios/${item.id}/edit`);}
  catch(e){setError(e instanceof Error?e.message:'Création impossible.');setBusy(false);sending.current=false;}
 }
 return <section className={styles.create}><Link href={`/templates/${templateId}/${version}`}>← Revoir le template</Link><p className="eyebrow">UN NOUVEAU DÉPART</p><h1>Votre portfolio, votre regard.</h1><p>{templateId==='minimal'?'Minimal':'Editorial'} · {version} · Brouillon privé</p><form onSubmit={submit} aria-busy={busy}><label htmlFor="template-name">Nom du portfolio</label><input id="template-name" required minLength={3} maxLength={100} value={name} disabled={busy} onChange={e=>{setName(e.target.value);if(!custom)setSlug(makeSlug(e.target.value));}}/><label htmlFor="template-slug">Identifiant du portfolio</label><input id="template-slug" value={slug} maxLength={110} pattern="[a-z0-9]+(-[a-z0-9]+)*" disabled={busy} onChange={e=>{setCustom(true);setSlug(e.target.value);}}/><p className="hint">Un identifiant dans votre espace. Aucune adresse publique n’est créée.</p>{error&&<p role="alert" className="notice error">{error}</p>}<button disabled={busy} type="submit">{busy?'Création en cours…':'Créer et personnaliser'}</button></form><p><Link href="/dashboard">Voir mes portfolios</Link></p></section>;
}
