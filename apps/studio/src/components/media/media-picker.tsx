'use client';
import {useEffect,useRef,useState} from 'react';
import type {MediaReference} from '../../../../../packages/content-contracts/src/ready-fixture-media.ts';
import MediaLibrary from './media-library';
import {mediaRequest,type Asset} from '../../lib/media';
import styles from './library.module.css';
import PrivateImage from './private-image';
export default function MediaPicker({label,value,onChange}:{label:string;value:MediaReference|null;onChange:(value:MediaReference|null)=>void}){
 const [open,setOpen]=useState(false),[asset,setAsset]=useState<Asset|null>(null),[unavailable,setUnavailable]=useState(false);
 const dialog=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null),close=useRef<HTMLButtonElement>(null);
 useEffect(()=>{let active=true;setAsset(null);setUnavailable(false);if(value?.asset_id)mediaRequest<Asset>('/assets/'+value.asset_id).then(r=>{if(active)setAsset(r);}).catch(()=>{if(active)setUnavailable(true);});return()=>{active=false;};},[value?.asset_id]);
 useEffect(()=>{if(open){dialog.current?.showModal();close.current?.focus();}else if(dialog.current?.open){dialog.current.close();trigger.current?.focus();}},[open]);
 function select(asset:Asset){onChange({asset_id:asset.id,alt:value?.alt||label,decorative:false,focal_point:value?.focal_point||{x:.5,y:.5}});setOpen(false);}
 function trap(event:React.KeyboardEvent){if(event.key!=='Tab')return;const nodes=dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),a[href]');if(!nodes?.length)return;const first=nodes[0],last=nodes[nodes.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
 return <fieldset><legend>{label}</legend>{asset&&<PrivateImage className={styles.preview} src={asset.thumbnail_url} width={asset.width} height={asset.height} alt={'Image sélectionnée : '+asset.original_name}/>}
 {unavailable&&<p role="status">Cette image est indisponible. Remplacez-la ou retirez sa référence ; vos autres contenus sont conservés.</p>}
 <button ref={trigger} className="secondary" onClick={()=>setOpen(true)}>{value?'Remplacer '+label.toLowerCase():'Choisir dans ma bibliothèque — '+label.toLowerCase()}</button>
 {value&&<><label className={styles.field}>Texte alternatif {label}<input maxLength={240} value={value.alt} onChange={e=>onChange({...value,alt:e.target.value})}/></label><p className="hint">Décrivez brièvement l’image. Le cadrage n’altère pas le fichier original traité.</p>{(['x','y'] as const).map(axis=><label key={axis} className={styles.field}>Cadrage {label} {axis==='x'?'horizontal':'vertical'}<input type="range" min="0" max="1" step="0.01" value={value.focal_point[axis]} onChange={e=>onChange({...value,focal_point:{...value.focal_point,[axis]:Number(e.target.value)}})}/></label>)}<button className="secondary" onClick={()=>onChange(null)}>Retirer {label.toLowerCase()}</button></>}
 <dialog ref={dialog} className={styles.dialog} aria-label={'Choisir une image pour '+label.toLowerCase()} onKeyDown={trap} onCancel={e=>{e.preventDefault();setOpen(false);}}><div className={styles.toolbar}><h2>Ma bibliothèque · {label}</h2><button ref={close} className="secondary" onClick={()=>setOpen(false)}>Fermer la bibliothèque</button></div>{open&&<MediaLibrary onSelect={select}/>}</dialog>
 </fieldset>;
}
