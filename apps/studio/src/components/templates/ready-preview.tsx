'use client';
import {useEffect,useMemo,useState} from 'react';
import CreativeEditorialView from './creative-editorial-view';
import {readyValidator} from './ready-browser-contracts';
import {readyRequest,type ReadyData} from '../../lib/ready-instances';
import type {PrivateMedia} from '../../lib/private-media-resolution';
export default function ReadyPreview({document,scope='private-preview',demonstration=false,portfolioId}:{document:unknown;scope?:string;demonstration?:boolean;portfolioId?:string}){
 const [media,setMedia]=useState<PrivateMedia>({}),[mediaError,setMediaError]=useState(''),[retry,setRetry]=useState(0);
 const doc=document as ReadyData;
 const ids=useMemo(()=>{try{const s=doc.content.slots;return JSON.stringify([s.brand_logo.value?.asset_id,s.hero_portrait.value?.asset_id,...s.selected_projects.items.map((p:ReadyData)=>p.cover?.asset_id)]);}catch{return '[]';}},[document]);
 const result=useMemo(()=>{try{return {effective:readyValidator.validate(document)};}catch{return {error:true};}},[document]);
 const valid=Boolean(result.effective);
 useEffect(()=>{let active=true;setMedia({});setMediaError('');if(!portfolioId||!valid)return;const timer=setTimeout(()=>{readyRequest<{assets:PrivateMedia}>(`ready-portfolios/${portfolioId}/media`,'POST',{content:doc.content}).then(r=>{if(active)setMedia(r.assets);}).catch(()=>{if(active)setMediaError('Images indisponibles pour le moment. Réessayez ou rouvrez le brouillon.');});},150);return()=>{active=false;clearTimeout(timer);};},[portfolioId,ids,valid,retry]);
 if(!result.effective)return <p role="alert">Aperçu indisponible : vérifiez les champs, les liens vers des sections visibles et les contrastes. Vos saisies sont conservées.</p>;
 return <>{mediaError&&<div role="status">{mediaError}<button onClick={()=>setRetry(n=>n+1)}>Réessayer les images</button></div>}<CreativeEditorialView privateMedia={portfolioId?media:undefined} document={document} effective={result.effective} scope={scope} enabled embedded demonstration={demonstration}/></>;
}
