"use client";
import {useCallback,useEffect,useState} from 'react';
import {portfolioRequest,type Portfolio} from '../../lib/portfolios';
export default function Portfolios(){
  const [items,setItems]=useState<Portfolio[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const [name,setName]=useState(''),[slug,setSlug]=useState(''),[description,setDescription]=useState(''),[kind,setKind]=useState('personal');
  const [editing,setEditing]=useState<string|null>(null),[busy,setBusy]=useState(false);
  const load=useCallback(async()=>{try{const data=await portfolioRequest();setItems(data.results||[]);setError('');}catch(e){setError(e instanceof Error?e.message:'Service indisponible.');}finally{setLoading(false);}},[]);
  useEffect(()=>{void load();},[load]);
  async function save(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{
    const payload:Record<string,string>={name,description,portfolio_type:kind};if(slug.trim())payload.slug=slug.trim();
    await portfolioRequest(editing?editing+'/':'',editing?'PATCH':'POST',payload);
    setEditing(null);setName('');setSlug('');setDescription('');setKind('personal');await load();
  }catch(e){setError(e instanceof Error?e.message:'Enregistrement impossible.');}finally{setBusy(false);}}
  function edit(p:Portfolio){setEditing(p.id);setName(p.name);setSlug(p.slug);setDescription(p.description);setKind(p.portfolio_type);}
  async function act(p:Portfolio,action:'delete'|'duplicate'){
    if(action==='delete'&&!window.confirm('Supprimer ce portfolio ? Cette action le retirera de votre liste.'))return;
    setBusy(true);setError('');try{await portfolioRequest(p.id+'/'+(action==='duplicate'?'duplicate/':''),action==='delete'?'DELETE':'POST');await load();}
    catch(e){setError(e instanceof Error?e.message:'Opération impossible.');}finally{setBusy(false);}}
  return <section aria-label="Mes portfolios" style={{maxWidth:860,margin:'2rem auto',padding:'1rem'}}>
    <h2>Mes portfolios</h2>{loading?<p role="status">Chargement…</p>:items.length===0?<p>Vous n'avez pas encore de portfolio. Créez le premier ci-dessous.</p>:<ul style={{listStyle:'none',padding:0}}>{items.map(p=><li key={p.id} style={{border:'1px solid #777',borderRadius:8,padding:16,marginBottom:12}}>
      <strong>{p.name}</strong> — {p.status==='draft'?'Brouillon':p.status}<p>{p.description||'Aucune description'}</p><small>{p.slug} · Modifié le {new Date(p.updated_at).toLocaleDateString('fr-FR')}</small>
      <div style={{display:'flex',gap:12,flexWrap:'wrap',marginTop:10}}><button disabled={busy} onClick={()=>edit(p)}>Modifier</button><button disabled={busy} onClick={()=>void act(p,'duplicate')}>Dupliquer</button><button disabled={busy} onClick={()=>void act(p,'delete')}>Supprimer</button></div>
    </li>)}</ul>}
    <h3>{editing?'Modifier le portfolio':'Créer un portfolio'}</h3><form onSubmit={e=>void save(e)} style={{display:'grid',gap:12,maxWidth:500}}>
      <label>Nom <input required minLength={3} maxLength={100} value={name} onChange={e=>setName(e.target.value)}/></label>
      <label>Slug (facultatif, généré automatiquement) <input maxLength={110} value={slug} onChange={e=>setSlug(e.target.value)}/></label>
      <label>Description <textarea maxLength={500} value={description} onChange={e=>setDescription(e.target.value)}/></label>
      <label>Type <select value={kind} onChange={e=>setKind(e.target.value)}><option value="personal">Personnel</option><option value="professional">Professionnel</option><option value="business">Entreprise</option></select></label>
      <div style={{display:'flex',gap:12}}><button disabled={busy} type="submit">{busy?'Enregistrement…':editing?'Enregistrer':'Créer'}</button>{editing&&<button type="button" onClick={()=>{setEditing(null);setName('');setSlug('');setDescription('');setKind('personal');}}>Annuler</button>}</div>
    </form>{error&&<p role="alert">{error}</p>}
  </section>;
}
