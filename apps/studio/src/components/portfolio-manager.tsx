'use client';
import {useEffect,useRef,useState,type FormEvent,type KeyboardEvent} from 'react';
import Link from 'next/link';
import {makeSlug,portfolioRequest,PortfolioError,type Portfolio,type PortfolioPage,type PortfolioInput} from '../lib/portfolios';

type Mode='list'|'new'|'overview'|'settings';
function ArrowIcon(){return <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M5 15 15 5M5 5h10v10" strokeLinecap="round" strokeLinejoin="round"/></svg>;}
function Status({item}:{item:Portfolio}){return <div className="badges"><span className={'badge '+(item.management_state==='archived'?'archived':'')}>{item.management_state==='active'?'Actif':'Archivé'}</span><span className="badge">Brouillon · Privé</span></div>;}
function date(value:string){return new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'short',year:'numeric'}).format(new Date(value));}
function errorText(error:unknown){return error instanceof Error?error.message:'Impossible de contacter le service. Réessayez.';}

export default function PortfolioManager({mode,id}:{mode:Mode;id?:string}) {
  const [data,setData]=useState<PortfolioPage|null>(null),[item,setItem]=useState<Portfolio|null>(null);
  const [state,setState]=useState<'active'|'archived'>('active'),[page,setPage]=useState(1),[refresh,setRefresh]=useState(0);
  const [loading,setLoading]=useState(mode!=='new'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [fields,setFields]=useState<Record<string,string[]>>({}),[notFound,setNotFound]=useState(false);
  const [name,setName]=useState(''),[slug,setSlug]=useState(''),[description,setDescription]=useState(''),[customSlug,setCustomSlug]=useState(false),[blank,setBlank]=useState(false);
  const [deleting,setDeleting]=useState<Portfolio|null>(null);
  const dialog=useRef<HTMLDialogElement>(null),cancel=useRef<HTMLButtonElement>(null),alert=useRef<HTMLDivElement>(null);

  useEffect(()=>{
    if(mode==='new')return;
    const controller=new AbortController();let active=true;
    setLoading(true);setError('');setNotFound(false);setItem(null);setData(null);
    const path=mode==='list'?`?state=${state}&page=${page}`:`/${id}`;
    portfolioRequest<PortfolioPage|Portfolio>(path,'GET',undefined,undefined,controller.signal).then(result=>{
      if(!active)return;
      if(mode==='list')setData(result as PortfolioPage);
      else {const value=result as Portfolio;setItem(value);setName(value.name);setSlug(value.slug);setDescription(value.description);setCustomSlug(true);}
    }).catch(e=>{if(!active)return;setError(errorText(e));setNotFound(e instanceof PortfolioError&&e.status===404);}).finally(()=>{if(active)setLoading(false);});
    return()=>{active=false;controller.abort();};
  },[mode,id,state,page,refresh]);
  useEffect(()=>{if(deleting){dialog.current?.showModal();cancel.current?.focus();}else dialog.current?.close();},[deleting]);

  function changePage(next:number){setLoading(true);setData(null);setPage(next);}
  function changeState(next:'active'|'archived'){if(next===state)return;setLoading(true);setData(null);setState(next);setPage(1);}
  function trapDialogFocus(event:KeyboardEvent<HTMLDialogElement>){
    if(event.key!=='Tab')return;
    const buttons=Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'));
    if(!buttons.length){event.preventDefault();return;}
    if(event.shiftKey&&document.activeElement===buttons[0]){event.preventDefault();buttons[buttons.length-1].focus();}
    else if(!event.shiftKey&&document.activeElement===buttons[buttons.length-1]){event.preventDefault();buttons[0].focus();}
  }
  function fail(e:unknown){setError(errorText(e));if(e instanceof PortfolioError)setFields(e.fields);requestAnimationFrame(()=>alert.current?.focus());}
  async function save(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);setError('');setFields({});setNotice('');
    const payload:PortfolioInput={name:name.trim(),description};if(slug.trim())payload.slug=slug.trim();
    try{
      const value=await portfolioRequest<Portfolio>(mode==='new'?'':`/${id}`,mode==='new'?'POST':'PATCH',payload,item?.etag);
      if(mode==='new')window.location.assign('/portfolios/'+value.id);
      else {setItem(value);setName(value.name);setSlug(value.slug);setDescription(value.description);setNotice('Modifications enregistrées. Votre portfolio reste privé.');}
    }catch(e){fail(e);}finally{setBusy(false);}
  }
  async function action(target:Portfolio,kind:'duplicate'|'archive'|'restore'|'delete'){
    setBusy(true);setError('');setFields({});setNotice('');
    try{
      const value=await portfolioRequest<Portfolio>(`/${target.id}${kind==='delete'?'':'/'+kind}`,kind==='delete'?'DELETE':'POST',kind==='delete'?{confirm:true}:{},target.etag);
      setDeleting(null);
      if(kind==='duplicate'){window.location.assign('/portfolios/'+value.id);return;}
      if(kind==='delete'&&mode!=='list'){window.location.assign('/dashboard');return;}
      setNotice(kind==='delete'?'Portfolio supprimé de vos listes.':kind==='archive'?'Portfolio archivé.':'Portfolio restauré. Il reste privé.');
      if(mode==='list'){setPage(1);setRefresh(r=>r+1);}else setItem(value);
    }catch(e){setDeleting(null);fail(e);}finally{setBusy(false);}
  }
  function actions(target:Portfolio){return <details className="action-menu"><summary aria-label={'Actions pour '+target.name}>Actions <span aria-hidden="true">⌄</span></summary><div className="action-menu-content">
    {target.management_state==='active'?<><Link href={'/portfolios/'+target.id+'/settings'}>Modifier</Link><button disabled={busy} onClick={()=>void action(target,'duplicate')}>Dupliquer</button><button disabled={busy} onClick={()=>void action(target,'archive')}>Archiver</button></>:<button disabled={busy} onClick={()=>void action(target,'restore')}>Restaurer</button>}
    <button className="danger-text" disabled={busy} onClick={()=>setDeleting(target)}>Supprimer</button></div></details>;}
  function form(){return <form onSubmit={save} className="portfolio-form" aria-busy={busy}>
    <div className="field"><label htmlFor="portfolio-name">Nom du portfolio</label><input id="portfolio-name" required minLength={3} maxLength={100} value={name} aria-invalid={!!fields.name} aria-describedby={fields.name?'name-error':undefined} onChange={e=>{setName(e.target.value);if(!customSlug)setSlug(makeSlug(e.target.value));}}/>{fields.name&&<p id="name-error" className="field-error">{fields.name.join(' ')}</p>}</div>
    <div className="field"><label htmlFor="portfolio-slug">Identifiant du portfolio</label><input id="portfolio-slug" maxLength={110} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={slug} aria-invalid={!!fields.slug} aria-describedby="slug-hint slug-error" onChange={e=>{setCustomSlug(true);setSlug(e.target.value);}}/><p id="slug-hint" className="hint">Généré depuis le nom, puis modifiable. Aucune adresse publique n’est créée.</p><p id="slug-error" className="field-error">{fields.slug?.join(' ')}</p></div>
    <div className="field"><label htmlFor="portfolio-description">Description <span className="optional">(facultative)</span></label><textarea id="portfolio-description" maxLength={500} rows={4} value={description} onChange={e=>setDescription(e.target.value)} aria-invalid={!!fields.description} aria-describedby="description-error"/><p id="description-error" className="field-error">{fields.description?.join(' ')}</p><small className="character-count">{description.length}/500</small></div>
    {mode==='new'&&<div className="theme-note"><span className="theme-dot" aria-hidden="true"/><div><strong>Studio Neutral</strong><p>Thème initial · version 1.0.0</p></div><span className="badge">Par défaut</span></div>}
    <div className="form-actions"><button disabled={busy} type="submit">{busy?'Enregistrement…':mode==='new'?'Créer mon portfolio':'Enregistrer les modifications'}</button><Link className="button secondary" href={mode==='new'?'/dashboard':'/portfolios/'+id}>Annuler</Link></div>
  </form>;}

  return <div className="portfolio-content">
    {mode==='list'?<><section className="page-heading"><div><p className="eyebrow">UN ESPACE POUR CHAQUE AMBITION</p><h1>Mes portfolios<span className="accent">.</span></h1><p>Vos idées, vos projets, vos univers. Tous au même endroit.</p></div><Link className="button" href="/portfolios/new"><span aria-hidden="true">＋</span> Créer un portfolio</Link></section>
      <div className="portfolio-toolbar"><div className="filter-tabs" aria-label="Filtrer les portfolios"><button aria-pressed={state==='active'} onClick={()=>changeState('active')}>Actifs <span>{data?.active_count??'—'}</span></button><button aria-pressed={state==='archived'} onClick={()=>changeState('archived')}>Archives <span>{data?.archived_count??'—'}</span></button></div><span className="quiet-label">Publication manuelle uniquement</span></div></>:
      <Link className="back-link" href="/dashboard">← Mes portfolios</Link>}
    <div ref={alert} tabIndex={-1} role="alert" className={error?'notice error':''}>{error}{error&&!notFound&&mode!=='new'&&<button className="quiet" onClick={()=>{setFields({});setRefresh(r=>r+1);}}>Recharger la version actuelle</button>}</div>
    {notice&&<p role="status" className="notice success">{notice}</p>}
    {loading?<div className="loading-panel" role="status">Chargement de votre espace…</div>:mode==='list'&&data?<>
      {data.results.length===0?<section className="empty-state"><div className="empty-mark" aria-hidden="true">✳</div><p className="eyebrow">{state==='active'?'TOUT COMMENCE ICI':'VOS ARCHIVES'}</p><h2>{state==='active'?'Votre prochain chapitre vous attend.':'Aucun portfolio archivé.'}</h2><p>{state==='active'?'Créez un espace pour raconter votre travail, à votre manière.':'Les portfolios archivés resteront ici, prêts à être restaurés.'}</p>{state==='active'&&<Link className="button" href="/portfolios/new">Créer mon premier portfolio</Link>}</section>:
      <div className="portfolio-grid">{data.results.map((value,index)=><article className="portfolio-card" key={value.id}><Link href={'/portfolios/'+value.id} className={'portfolio-preview preview-'+index%3} aria-label={'Ouvrir '+value.name}><span className="preview-line"/><span className="preview-title">{value.name}</span><span className="preview-foot">VOTRE PROCHAIN UNIVERS <ArrowIcon/></span></Link><div className="card-body"><Status item={value}/><h2><Link href={'/portfolios/'+value.id}>{value.name}</Link></h2><p className="card-description">{value.description||'Votre espace de création personnel.'}</p><div className="card-meta"><small>Modifié le {date(value.updated_at)}</small>{actions(value)}</div><Link className="open-link" href={'/portfolios/'+value.id}>Ouvrir le portfolio <ArrowIcon/></Link></div></article>)}</div>}
      {data.count>12&&<nav className="pagination" aria-label="Pagination"><button className="secondary" disabled={page===1||busy} onClick={()=>changePage(page-1)}>Précédent</button><span>Page {page} sur {Math.ceil(data.count/12)}</span><button className="secondary" disabled={page*12>=data.count||busy} onClick={()=>changePage(page+1)}>Suivant</button></nav>}
    </>:mode==='new'?<section className="creation-panel"><p className="eyebrow">NOUVEAU PORTFOLIO</p><h1>{blank?'Posons les premières lignes.':'Comment souhaitez-vous commencer ?'}</h1><p>Un portfolio indépendant, privé et enregistré en brouillon.</p>
      {!blank?<div className="starting-options"><button className="starting-option" onClick={()=>setBlank(true)}><span className="option-icon" aria-hidden="true">＋</span><strong>Portfolio vierge</strong><span>Une structure minimale pour un univers qui vous ressemble.</span><span className="option-link">Commencer →</span></button><div className="starting-option unavailable" aria-disabled="true"><span className="option-icon" aria-hidden="true">▤</span><strong>Utiliser un template</strong><span>Des compositions préconçues à personnaliser.</span><span className="badge">Bientôt disponible</span></div></div>:form()}
    </section>:item?<div className="workspace"><aside className="workspace-nav"><p className="eyebrow">VOTRE PORTFOLIO</p><strong>{item.name}</strong><nav aria-label="Espace portfolio"><Link aria-current={mode==='overview'?'page':undefined} href={'/portfolios/'+item.id}>Vue d’ensemble</Link>{['Projets','Pages','Apparence','Publication'].map(label=><button key={label} disabled title="Bientôt disponible">{label}<span>Bientôt</span></button>)}{item.management_state==='active'?<Link aria-current={mode==='settings'?'page':undefined} href={'/portfolios/'+item.id+'/settings'}>Paramètres</Link>:<span className="unavailable-label">Paramètres indisponibles</span>}</nav></aside>
      <section className="workspace-main"><div className="workspace-title"><div><Status item={item}/><h1>{mode==='settings'?'Paramètres généraux':item.name}</h1></div>{actions(item)}</div>
        {item.management_state==='archived'?<div className="notice">Ce portfolio est archivé. Restaurez-le pour reprendre les modifications.<button disabled={busy} onClick={()=>void action(item,'restore')}>Restaurer le portfolio</button></div>:mode==='settings'?form():<><p className="workspace-description">{item.description||'Ajoutez une description pour poser les intentions de ce portfolio.'}</p><div className="overview-data"><div><span>Identifiant</span><strong>{item.slug}</strong></div><div><span>Thème initial</span><strong>Studio Neutral · {item.initial_theme_version}</strong></div><div><span>Dernière modification</span><strong>{date(item.updated_at)}</strong></div><div><span>Publication</span><strong>Privé · aucune publication</strong></div></div><Link className="button" href={'/portfolios/'+item.id+'/settings'}>Modifier les informations</Link><p className="hint roadmap-note">Les outils de contenu et de personnalisation seront disponibles dans une prochaine étape.</p></>}
      </section></div>:null}
    <dialog ref={dialog} aria-labelledby="delete-title" aria-describedby="delete-description" onKeyDown={trapDialogFocus} onCancel={e=>{e.preventDefault();if(!busy)setDeleting(null);}}><h2 id="delete-title">Supprimer ce portfolio ?</h2><p id="delete-description">« {deleting?.name} » disparaîtra de vos listes. Aucune restauration n’est disponible dans l’interface actuelle.</p><div className="form-actions"><button ref={cancel} className="secondary" disabled={busy} onClick={()=>setDeleting(null)}>Annuler</button><button className="danger" disabled={busy} onClick={()=>deleting&&void action(deleting,'delete')}>{busy?'Suppression…':'Confirmer la suppression'}</button></div></dialog>
  </div>;
}
