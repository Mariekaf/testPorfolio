'use client';
import {useEffect,useState,type CSSProperties} from 'react';
export default function PrivateImage({src,alt,width,height,className,style,loading='lazy'}:{src:string;alt:string;width:number;height:number;className?:string;style?:CSSProperties;loading?:'lazy'|'eager'}){
 const [failed,setFailed]=useState(false);useEffect(()=>setFailed(false),[src]);
 const safe=/^\/api\/v1\/media\/assets\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/(file|thumbnail)$/.test(src);
 if(failed||!safe)return <div role="img" aria-label="Image indisponible" className={className}>Image indisponible · remplacez-la depuis votre bibliothèque.</div>;
 return <img src={src} alt={alt} width={width} height={height} className={className} style={style} loading={loading} decoding="async" onError={()=>setFailed(true)}/>;
}
