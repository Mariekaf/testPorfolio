'use client';
import {useEffect,useRef,useState,type ReactNode} from 'react';
import Link from 'next/link';
import {instanceRequest,type DesignRecord} from '../../lib/template-instances';
import {portfolioRequest,PortfolioError,type Portfolio} from '../../lib/portfolios';
import type {Snapshot,ContentSection,Settings} from '../../lib/template-render';
import PortfolioRenderer from './portfolio-renderer';
import styles from './template-editor.module.css';
import PortfolioNavigation from '../portfolio-navigation';
import {useEditorNavigation} from '../use-editor-navigation';
import {editorPath} from '../../lib/portfolio-navigation';

const labels={hero:'Introduction',about:'À propos',projects:'Projets',skills:'Compétences',contact:'Contact'};
function message(e:unknown){return e instanceof Error?e.message:'Le service est indisponible.';}
export default function TemplateEditor({id}:{id:string}){
 const [record,setRecord]=useState<DesignRecord|null>(null),[draft,setDraft]=useState<Snapshot|null>(null),[portfolio,setPortfolio]=useState<Portfolio|null>(null);
 const [selected,setSelected]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[conflict,setConflict]=useState(false),[mobile,setMobile]=useState(false),[refresh,setRefresh]=useState(0);
 const saving=useRef(false);
 const dirty=!!draft&&!!record&&JSON.stringify({content:draft.content,customization:draft.customization})!==JSON.stringify({content:record.snapshot.content,customization:record.snapshot.customization});
 useEffect(()=>{let active=true;setError('');setRecord(null);setDraft(null);setPortfolio(null);
  Promise.all([instanceRequest<DesignRecord>(`/${id}/design`),portfolioRequest<Portfolio>(`/${id}`)]).then(([data,item])=>{if(active){setRecord(data);setDraft(structuredClone(data.snapshot));setSelected(data.snapshot.composition.sections[0].id);setPortfolio(item);setConflict(false);}}).catch(e=>{if(active)setError(message(e));});
  return()=>{active=false;};
 },[id,refresh]);
 const {panel,select:selectPanel,headingRef}=useEditorNavigation(dirty,id);

 function updateContent(next:ContentSection){if(!draft)return;setNotice('');setDraft({...draft,content:{...draft.content,sections:draft.content.sections.map(s=>s.section_id===next.section_id?next:s)}});}
 function override(sectionId:string,change:{visible?:boolean;presentation?:Partial<Settings>}){
  if(!draft)return;const values=draft.customization.sections.filter(s=>s.section_id!==sectionId);const previous=draft.customization.sections.find(s=>s.section_id===sectionId);
  const next={...previous,section_id:sectionId,...change};if(change.presentation)next.presentation={...previous?.presentation,...change.presentation};
  setNotice('');setDraft({...draft,customization:{...draft.customization,sections:[...values,next]}});
 }
 function move(sectionId:string,delta:number){
  if(!draft)return;const sections=draft.composition.sections;const order=[...(draft.customization.section_order??sections.map(s=>s.id))];
  const slots=order.map((key,index)=>sections.find(s=>s.id===key)!.reorderable?index:-1).filter(i=>i>=0);const index=slots.indexOf(order.indexOf(sectionId));
  if(index+delta<0||index+delta>=slots.length)return;
  [order[slots[index]],order[slots[index+delta]]]=[order[slots[index+delta]],order[slots[index]]];
  setDraft({...draft,customization:{...draft.customization,section_order:order}});setNotice('');
 }
 async function save(){
  if(!draft||!record||saving.current)return;saving.current=true;setBusy(true);setError('');setNotice('');
  try{const data=await instanceRequest<DesignRecord>(`/${id}/design`,'PUT',{content:draft.content,customization:draft.customization},{'If-Match':record.etag});setRecord(data);setDraft(structuredClone(data.snapshot));setConflict(false);setNotice('Modifications enregistrées. Votre portfolio reste privé.');}
  catch(e){setError(message(e));if(e instanceof PortfolioError&&e.status===412)setConflict(true);}
  finally{saving.current=false;setBusy(false);}
 }
 function field(label:string,value:string,update:(v:string)=>void,max:number,area=false,type='text'):ReactNode {
  return <label className={styles.field}>{label}{area?<textarea value={value} maxLength={max} rows={4} onChange={e=>update(e.target.value)}/>:<input type={type} value={value} maxLength={max} onChange={e=>update(e.target.value)}/>}</label>;
 }
 function fields(section:ContentSection){
  switch(section.type){
   case 'hero':return <>{field('Titre principal',section.data.title,v=>updateContent({...section,data:{...section.data,title:v}}),160)}{field('Sous-titre',section.data.subtitle,v=>updateContent({...section,data:{...section.data,subtitle:v}}),500,true)}{field('Libellé du CTA',section.data.cta_label,v=>updateContent({...section,data:{...section.data,cta_label:v}}),60)}</>;
   case 'about':return <>{field('Titre de présentation',section.data.heading,v=>updateContent({...section,data:{...section.data,heading:v}}),120)}{field('Description de présentation',section.data.body,v=>updateContent({...section,data:{...section.data,body:v}}),5000,true)}</>;
   case 'projects':return <>{section.data.items.length===0&&<p>Aucun projet pour le moment. Ajoutez votre premier projet.</p>}{field('Titre des projets',section.data.heading,v=>updateContent({...section,data:{...section.data,heading:v}}),120)}{section.data.items.map((project,index)=><fieldset key={project.id}><legend>Projet {index+1}</legend>{field(`Titre du projet ${index+1}`,project.title,v=>updateContent({...section,data:{...section.data,items:section.data.items.map(p=>p.id===project.id?{...p,title:v}:p)}}),160)}{field(`Résumé du projet ${index+1}`,project.summary,v=>updateContent({...section,data:{...section.data,items:section.data.items.map(p=>p.id===project.id?{...p,summary:v}:p)}}),1000,true)}{field(`Lien du projet ${index+1}`,project.url??'',v=>updateContent({...section,data:{...section.data,items:section.data.items.map(p=>p.id===project.id?{...p,url:v||null}:p)}}),2048,false,'url')}<p className="hint">Lien HTTPS uniquement. Aucun projet public n’est créé.</p><button className="secondary" onClick={()=>updateContent({...section,data:{...section.data,items:section.data.items.filter(p=>p.id!==project.id)}})}>Retirer le projet {index+1}</button></fieldset>)}<button className="secondary" disabled={section.data.items.length>=24} onClick={()=>updateContent({...section,data:{...section.data,items:[...section.data.items,{id:crypto.randomUUID(),title:'Nouveau projet',summary:'',url:null}]}})}>Ajouter un projet</button></>;
   case 'skills':return <>{field('Titre des compétences',section.data.heading,v=>updateContent({...section,data:{...section.data,heading:v}}),120)}{section.data.items.map((skill,index)=><div className={styles.skill} key={index}>{field(`Compétence ${index+1}`,skill,v=>updateContent({...section,data:{...section.data,items:section.data.items.map((s,i)=>i===index?v:s)}}),100)}<button className="quiet" aria-label={`Retirer la compétence ${index+1}`} onClick={()=>updateContent({...section,data:{...section.data,items:section.data.items.filter((_,i)=>i!==index)}})}>Retirer</button></div>)}<button className="secondary" disabled={section.data.items.length>=40} onClick={()=>updateContent({...section,data:{...section.data,items:[...section.data.items,'Nouvelle compétence']}})}>Ajouter une compétence</button></>;
   case 'contact':return <>{field('Titre du contact',section.data.heading,v=>updateContent({...section,data:{...section.data,heading:v}}),120)}{field('Texte du contact',section.data.body,v=>updateContent({...section,data:{...section.data,body:v}}),2000,true)}{field('Adresse e-mail de contact',section.data.email??'',v=>updateContent({...section,data:{...section.data,email:v||null}}),254,false,'email')}</>;
  }
 }
 if(!record||!draft||!portfolio||record.portfolio_id!==id||portfolio.id!==id)return <section><h1>Personnaliser le portfolio</h1>{error?<><p role="alert">{error}</p><Link href="/dashboard">Retour aux portfolios</Link><button onClick={()=>setRefresh(r=>r+1)}>Réessayer</button></>:<p role="status">Chargement du design…</p>}</section>;
 if(!editorPath(portfolio)||portfolio.source_template_id==='creative-editorial'||draft.schema_version!==1)return <section><h1>Éditeur indisponible pour cette version</h1><Link href={`/portfolios/${id}`}>Retour à la vue d’ensemble</Link></section>;
 const activeSection=panel==='projects'?draft.composition.sections.find(s=>s.type==='projects')!.id:selected;
 const section=draft.composition.sections.find(s=>s.id===activeSection)!;
 const content=draft.content.sections.find(s=>s.section_id===activeSection)!;
 const base=draft.presentation.sections.find(s=>s.section_id===activeSection)!.settings;
 const local=draft.customization.sections.find(s=>s.section_id===activeSection);
 const order=draft.customization.section_order??draft.composition.sections.map(s=>s.id);
 const editable=portfolio.management_state==='active';
 return <div className="portfolio-editor-frame"><PortfolioNavigation portfolio={portfolio} active="editor" panel={panel} onPanel={selectPanel}/><section className={styles.editor}><header className={styles.top}><div><Link href={`/portfolios/${id}`}>← Vue d’ensemble</Link><p className="eyebrow">{draft.composition.template.id.toUpperCase()} · BROUILLON PRIVÉ</p><h1>{portfolio.name}</h1><p role="status">{busy?'Enregistrement…':dirty?'Modifications non enregistrées':notice||'Toutes les modifications sont enregistrées.'}</p></div><button disabled={busy||!dirty||!editable||conflict} onClick={()=>void save()}>{busy?'Enregistrement…':'Enregistrer'}</button></header>
 {error&&<div role="alert" className="notice error">{error}{conflict&&<><p>Vos modifications locales restent dans l’éditeur. Recharger remplacera ce brouillon par la version du serveur.</p><button className="secondary" onClick={()=>{if(window.confirm('Remplacer les modifications locales par la version enregistrée ?')){setRecord(null);setDraft(null);setRefresh(r=>r+1);}}}>Recharger la version enregistrée</button></>}</div>}
 {!editable&&<p className="notice">Portfolio archivé : aperçu en lecture seule. Restaurez-le depuis la vue d’ensemble.</p>}
 <div className={styles.workspace}><aside className={styles.navigation} hidden={panel==='projects'}><h2>Sections</h2><nav aria-label="Sections du portfolio">{order.map(key=>{const s=draft.composition.sections.find(s=>s.id===key)!;return <button key={key} aria-current={selected===key?'true':undefined} onClick={()=>setSelected(key)}>{labels[s.type]}</button>;})}</nav></aside>
 <section className={styles.panel}><h2 data-editor-panel-heading tabIndex={-1} ref={element=>{headingRef.current=element;}}>{panel==='appearance'?`Apparence · ${labels[section.type]}`:labels[section.type]}</h2><fieldset disabled={busy||!editable} className={styles.controls}><legend className={styles.srOnly}>Personnalisation de la section</legend>{panel==='appearance'&&<button className="secondary" onClick={()=>selectPanel('sections')}>Modifier le contenu de cette section</button>}{panel!=='appearance'&&fields(content)}<div hidden={panel==='appearance'||panel==='projects'}><hr/><label className={styles.toggle}><input type="checkbox" checked={local?.visible??section.visible} disabled={section.required||!section.toggleable} onChange={e=>override(activeSection,{visible:e.target.checked})}/>Afficher cette section{section.required?' (obligatoire)':''}</label><div className={styles.order}><button className="secondary" disabled={!section.reorderable||order.filter(key=>draft.composition.sections.find(s=>s.id===key)!.reorderable).indexOf(activeSection)<=0} onClick={()=>move(activeSection,-1)}>Monter</button><button className="secondary" disabled={!section.reorderable||order.filter(key=>draft.composition.sections.find(s=>s.id===key)!.reorderable).indexOf(activeSection)>=draft.composition.sections.filter(s=>s.reorderable).length-1} onClick={()=>move(activeSection,1)}>Descendre</button></div></div><div hidden={panel==='projects'}><h3>Présentation</h3>{(['spacing','alignment','emphasis'] as const).map(key=><label key={key} className={styles.field}>{({spacing:'Espacement',alignment:'Alignement',emphasis:'Emphase'})[key]}<select aria-label={({spacing:'Espacement',alignment:'Alignement',emphasis:'Emphase'})[key]} value={local?.presentation?.[key]??base[key]} onChange={e=>override(activeSection,{presentation:{[key]:e.target.value} as Partial<Settings>})}>{section.presentation_policy[key].map(value=><option key={value} value={value}>{({compact:'Compact',normal:'Normal',airy:'Aéré',start:'À gauche',center:'Centré',quiet:'Discrète',strong:'Forte'})[value]}</option>)}</select></label>)}<button className="quiet" onClick={()=>{setDraft({...draft,customization:{...draft.customization,sections:draft.customization.sections.map(s=>s.section_id===activeSection?{section_id:s.section_id,...('visible' in s?{visible:s.visible}:{})}:s)}});}}>Réinitialiser la présentation</button></div></fieldset></section>
 <section className={styles.preview}><div className={styles.previewHead}><h2>Aperçu en direct</h2><div role="group" aria-label="Largeur de l’aperçu"><button aria-pressed={!mobile} onClick={()=>setMobile(false)}>Desktop</button><button aria-pressed={mobile} onClick={()=>setMobile(true)}>Mobile</button></div></div><div className={styles.previewFrame} data-mobile={mobile} data-testid="instance-preview"><PortfolioRenderer snapshot={draft} scope={'instance-'+id}/></div></section></div></section></div>;
}
