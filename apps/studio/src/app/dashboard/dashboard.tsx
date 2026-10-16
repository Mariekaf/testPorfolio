"use client";
import {useEffect,useRef,useState} from 'react';
import {ApiError,authRequest,type Session} from '../../lib/auth';
import Portfolios from './portfolios';
export default function Dashboard() {
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
    leaving.current=true;setSession(null);
    try{await authRequest('logout',{});if(typeof BroadcastChannel!=='undefined'){const channel=new BroadcastChannel('portfolio-session');channel.postMessage('logout');channel.close();}window.location.replace('/login');}
    catch{leaving.current=false;setError('Déconnexion non confirmée. Réessayez.');}
  }
  return <main><header><span className="brand">studio ✳</span><button onClick={logout}>Se déconnecter</button></header>
    <section className="intro"><p className="eyebrow">VOTRE TABLEAU DE BORD</p>
      {session?<><h1>Bienvenue, {session.user.first_name}.</h1><p>Votre espace est prêt. Créez et gérez vos portfolios privés ci-dessous.</p></>:<p role="status">{error||'Vérification de votre session…'}</p>}
    </section>{session&&<Portfolios/>}</main>;
}
