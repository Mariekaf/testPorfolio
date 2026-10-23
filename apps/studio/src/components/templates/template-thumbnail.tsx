'use client';
import {useEffect,useRef,useState} from 'react';
import type {Snapshot} from '../../lib/template-render';
import PortfolioRenderer from './portfolio-renderer';
export default function TemplateThumbnail({snapshot}:{snapshot:Snapshot}){
 const root=useRef<HTMLDivElement>(null),[width,setWidth]=useState(0);
 useEffect(()=>{const node=root.current;if(!node)return;const observer=new ResizeObserver(entries=>setWidth(entries[0].contentRect.width));observer.observe(node);return()=>observer.disconnect();},[]);
 return <div ref={root} style={{width:'100%',height:'100%',overflow:'hidden'}}><div style={{width:1000,transform:`scale(${width/1000})`,transformOrigin:'top left'}}><PortfolioRenderer snapshot={snapshot} demonstration scope={'card-'+snapshot.composition.template.id}/></div></div>;
}
