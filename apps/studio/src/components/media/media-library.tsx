'use client';
import {useEffect,useRef,useState} from 'react';
import {mediaRequest,type Asset,type MediaPage} from '../../lib/media';
import styles from './library.module.css';
import PrivateImage from './private-image';
export default function MediaLibrary({onSelect}:{onSelect?:(asset:Asset)=>void}){
 const [data,setData]=useState<MediaPage|null>(null),[page,setPage]=useState(1),[error,setError]=useState(''),[status,setStatus]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0);
 const form=useRef<HTMLFormElement>(null),uploading=useRef(false),input=useRef<HTMLInputElement>(null);
 useEffect(()=>{let active=true;setError('');setData(null);mediaRequest<MediaPage>(`/assets?page=${page}`).then(r=>{if(active)setData(r);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[page,refresh]);
 async function upload(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();if(uploading.current)return;const files=input.current?.files;
  if(!files?.length||files.length>4||[...files].some(f=>f.size>8*1024*1024)){setError('Sélectionnez de 1 à 4 images de 8 Mio maximum.');return;}
  const payload=new FormData();for(const file of files)payload.append('files',file);payload.append('rights','true');
  uploading.current=true;setBusy(true);setError('');setStatus('Vérification et préparation des images…');
  try{const result=await mediaRequest<{results:Asset[]}>('/assets','POST',payload);setStatus(`${result.results.length} image(s) importée(s). Choisissez une image ci-dessous.`);form.current?.reset();setPage(1);setRefresh(n=>n+1);}
  catch(e){setError((e as Error).message);setStatus('Import non confirmé. Actualisez la bibliothèque avant de réessayer.');}
  finally{uploading.current=false;setBusy(false);}
 }
 async function remove(asset:Asset){
  if(!window.confirm('Retirer cette image de la bibliothèque ? Si elle est utilisée par un portfolio ou une révision, la suppression sera refusée. Les fichiers non utilisés sont retenus 7 jours avant purge explicite.'))return;
  setBusy(true);setError('');try{await mediaRequest(`/assets/${asset.id}`,'DELETE',{confirm:true},asset.etag);setStatus('Image retirée. Rétention privée de 7 jours avant purge explicite.');setPage(1);setRefresh(n=>n+1);}catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 return <section className={styles.library} aria-label="Bibliothèque privée de médias"><p>Vos images restent privées. JPEG, PNG ou WebP statiques · 8 Mio par fichier · 4 fichiers par import · 200 images et 200 Mio par compte.</p>
 <form ref={form} className={styles.upload} onSubmit={upload}><label>Images à importer<input ref={input} type="file" accept="image/jpeg,image/png,image/webp" multiple required disabled={busy}/></label><label><input name="rights" type="checkbox" required disabled={busy}/> Je dispose des droits nécessaires pour utiliser ces images.</label><button disabled={busy}>{busy?'Préparation…':'Importer une image'}</button></form>
 {error&&<div role="alert" className={styles.error}>{error}<button className="secondary" disabled={busy} onClick={()=>setRefresh(n=>n+1)}>Réessayer la bibliothèque</button></div>}
 <p role="status">{status||(!data&&!error?'Chargement de votre bibliothèque…':'')}</p>
 {data&&<>{data.count===0?<p>Aucune image pour le moment. Importez votre première image.</p>:<><p>{data.count} image(s) · page {data.page}</p><div className={styles.grid}>{data.results.map(asset=><article key={asset.id} className={styles.card}><PrivateImage src={asset.thumbnail_url} alt={'Miniature : '+asset.original_name} loading="lazy" width={asset.width} height={asset.height}/><p>{asset.original_name}</p><p>{asset.width} × {asset.height} px · {Math.ceil((asset.size+asset.thumbnail_size)/1024)} Kio</p>{onSelect&&<button disabled={busy} onClick={()=>onSelect(asset)} aria-label={'Choisir '+asset.original_name}>Choisir</button>}<button className="secondary" disabled={busy} onClick={()=>void remove(asset)} aria-label={'Supprimer '+asset.original_name}>Supprimer</button></article>)}</div></>}
 <nav className={styles.pager} aria-label="Pages de médias"><button className="secondary" disabled={busy||page===1} onClick={()=>setPage(n=>n-1)}>Précédente</button><span>Page {page}</span><button className="secondary" disabled={busy||page*12>=data.count} onClick={()=>setPage(n=>n+1)}>Suivante</button></nav></>}
 </section>;
}
