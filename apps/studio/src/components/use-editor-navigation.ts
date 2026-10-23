'use client';
import {useEffect,useRef,useState} from 'react';
import {readPanel,sameEditor,type Panel} from '../lib/portfolio-navigation';

type NavigationEvent = Event & {navigationType?:string;destination?:{url:string}};
type Entry = {id:string;token:string;kind:'boundary'|'live'};
/** A local panel never loads or saves a design. Keep Next's history state opaque. */
export function useEditorNavigation(dirty:boolean,id:string) {
  const [panel,setPanel]=useState<Panel|null>(null);
  const headingRef=useRef<HTMLElement|null>(null);
  const latest=useRef(dirty);latest.current=dirty;
  const identity=useRef(''),token=useRef(''),approvedExit=useRef(false);
  useEffect(()=>{
    if(identity.current!==id){identity.current=id;token.current=crypto.randomUUID();}
    approvedExit.current=false;
    const current=history.state?.portfolioEditor as Entry|undefined;
    if(current?.id!==id||current.token!==token.current){
      const marker={id,token:token.current};
      // Install the boundary before any panel changes (also while clean).
      // Strict Mode's effect replay reuses the same token and does not duplicate it.
      history.replaceState({...history.state,portfolioEditor:{...marker,kind:'boundary'}},'',location.href);
      history.pushState({...history.state,portfolioEditor:{...marker,kind:'live'}},'',location.href);
    }else if(current.kind==='boundary'){
      // Returning with Forward after an accepted exit starts a protected live
      // editor again, rather than editing on the boundary entry itself.
      history.pushState({...history.state,portfolioEditor:{...current,kind:'live'}},'',location.href);
    }
    const sync=()=>setPanel(readPanel(location.search));sync();
    const confirmLeave=()=>!latest.current||window.confirm('Des modifications ne sont pas enregistrées. Quitter sans sauvegarder ?');
    const navigation=(window as unknown as {navigation?:EventTarget}).navigation;
    const traverse=(e:NavigationEvent)=>{
      // Retain the original pre-navigation guard where cancellation is supported.
      // Local panel traversals and an explicitly accepted boundary exit are exempt.
      if(e.cancelable&&e.navigationType==='traverse'&&e.destination&&!sameEditor(location.href,e.destination.url)&&!approvedExit.current&&!confirmLeave())e.preventDefault();
    };
    const before=(e:BeforeUnloadEvent)=>{if(latest.current&&!approvedExit.current){e.preventDefault();e.returnValue='';}};
    const leave=(e:Event)=>{if(!confirmLeave())e.preventDefault();};
    const click=(e:MouseEvent)=>{
      const link=(e.target as Element).closest?.('a[href]') as HTMLAnchorElement|null;
      if(!link||link.target==='_blank'||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
      if(!sameEditor(location.href,link.href)&&!confirmLeave()){e.preventDefault();e.stopImmediatePropagation();}
    };
    const pop=()=>{
      const entry=history.state?.portfolioEditor as Entry|undefined;
      if(entry?.id===id&&entry.token===token.current&&entry.kind==='boundary'){
        // Next's Window popstate listener runs before later listeners, even with
        // capture=true. A same-editor boundary keeps it from unmounting the draft
        // before the user can decline a one-step Back out of the editor.
        if(!confirmLeave()){history.forward();return;}
        approvedExit.current=true;history.back();return;
      }
      sync();
    };
    navigation?.addEventListener('navigate',traverse);
    window.addEventListener('beforeunload',before);
    window.addEventListener('portfolio-before-leave',leave);
    document.addEventListener('click',click,true);
    window.addEventListener('popstate',pop);
    return()=>{navigation?.removeEventListener('navigate',traverse);window.removeEventListener('beforeunload',before);window.removeEventListener('portfolio-before-leave',leave);document.removeEventListener('click',click,true);window.removeEventListener('popstate',pop);};
  },[id]);
  useEffect(()=>{
    if(panel===null)return;
    const frame=requestAnimationFrame(()=>headingRef.current?.focus());
    return()=>cancelAnimationFrame(frame);
  },[panel]);
  function select(next:Panel){
    const url=new URL(location.href);url.searchParams.set('panel',next);
    if(url.href!==location.href){
      // Preserve the active Next page, rather than navigating to another server
      // search-parameter entry. Our own panel state is the only changed UI state.
      const entry:Entry={id,token:token.current,kind:'live'};
      history.pushState({...history.state,portfolioEditor:entry},'',url);
    }
    setPanel(next);
  }
  return {panel,select,headingRef};
}
