"use client";
import {useEffect,useRef,useState,type ReactNode} from 'react';
import Link from 'next/link';
import {ApiError,authRequest,type Session} from '../lib/auth';

export default function SessionShell({children}:{children:ReactNode}) {
  const [dark,setDark]=useState<boolean|null>(null);
  useEffect(()=>{let saved:string|null=null;try{saved=localStorage.getItem('portfolio-studio-theme');}catch{}setDark(saved==='dark'||(saved!=='light'&&window.matchMedia('(prefers-color-scheme: dark)').matches));},[]);
  function toggleTheme(){const next=!dark;setDark(next);try{localStorage.setItem('portfolio-studio-theme',next?'dark':'light');}catch{}}
  useEffect(()=>{if(dark===null)return;document.documentElement.dataset.studioTheme=dark?'dark':'light';return()=>{delete document.documentElement.dataset.studioTheme;};},[dark]);
  const leaving=useRef(false);
  const [session,setSession]=useState<Session|null>(null),[error,setError]=useState('');
  useEffect(()=>{
    let active=true, expiry:ReturnType<typeof setTimeout>;
    const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('portfolio-session'):null;
    function expired(){if(leaving.current)return;leaving.current=true;setSession(null);window.location.replace('/login?reason=expired');}
    async function check(){
      if(leaving.current)return;
      try {
        const data=await authRequest('me') as Session;
        if(!active||leaving.current)return;
        const remaining=Date.parse(data.expires_at)-Date.now();
        if(!Number.isFinite(remaining)||remaining<=0){expired();return;}
        setSession(data);setError('');clearTimeout(expiry);
        expiry=setTimeout(expired,remaining);
      }catch(e){if(!active||leaving.current)return;setSession(null);if(e instanceof ApiError&&(e.status===401||e.status===403))expired();else setError('Connexion au service indisponible.');}
    }
    const hide=()=>setSession(null);
    channel?.addEventListener('message',expired);
    window.addEventListener('focus',check);window.addEventListener('pageshow',check);window.addEventListener('pagehide',hide);
    const interval=setInterval(check,30000);void check();
    return()=>{active=false;clearInterval(interval);clearTimeout(expiry);channel?.close();window.removeEventListener('focus',check);window.removeEventListener('pageshow',check);window.removeEventListener('pagehide',hide);};
  },[]);
  async function logout(){
    if(!window.dispatchEvent(new Event('portfolio-before-leave',{cancelable:true})))return;
    leaving.current=true;setSession(null);
    try{await authRequest('logout',{});if(typeof BroadcastChannel!=='undefined'){const channel=new BroadcastChannel('portfolio-session');channel.postMessage('logout');channel.close();}window.location.replace('/login');}
    catch{leaving.current=false;setError('Déconnexion non confirmée. Réessayez.');}
  }
  return <main className="studio-shell"><header className="studio-header"><Link href="/dashboard" className="brand">studio <span aria-hidden="true">✳</span></Link><div className="header-actions"><button className="quiet" onClick={toggleTheme} aria-label={dark?'Activer le mode clair':'Activer le mode sombre'}>{dark?'Clair':'Sombre'}</button><button className="quiet" onClick={logout}>Se déconnecter</button></div></header>
    {session?<><div className="account-note">Votre espace personnel <span aria-hidden="true">/</span> {session.user.first_name}</div>{children}</>:<section className="loading-panel"><p role="status">{error||'Vérification de votre session…'}</p></section>}
  </main>;
}
