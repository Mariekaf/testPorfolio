'use client';
import {useEffect, useRef, useState, type FormEvent} from 'react';
import Link from 'next/link';
import {ApiError, authRequest} from '../lib/auth';
type Mode = 'register'|'login'|'forgot-password'|'reset-password';
const titles = {register:'Créer votre compte',login:'Heureux de vous retrouver', 'forgot-password':'Un nouveau mot de passe', 'reset-password':'Choisir votre mot de passe'};
export default function AuthForm({mode}:{mode:Mode}) {
  const [busy,setBusy]=useState(false), [message,setMessage]=useState(''), [fields,setFields]=useState<Record<string,string[]>>({});
  const [visible,setVisible]=useState(false), [link,setLink]=useState<Record<string,string>|null>(null);
  const notice=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    if(mode==='reset-password') {
      const hash=new URLSearchParams(window.location.hash.slice(1));
      setLink({uid:hash.get('uid')||'',token:hash.get('token')||''});
      window.history.replaceState(null,'',window.location.pathname);
    }
    if(mode==='login') {
      const reason=new URLSearchParams(window.location.search).get('reason');
      if(reason==='registered') setMessage('Compte créé. Connectez-vous pour continuer.');
      if(reason==='expired') setMessage('Votre session a expiré. Reconnectez-vous.');
      if(reason==='reset') setMessage('Mot de passe modifié. Vous pouvez vous connecter.');
    }
  },[mode]);
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true);setMessage('');setFields({});
    const data=Object.fromEntries(new FormData(event.currentTarget)) as Record<string,string>;
    if(data.password_confirmation!==undefined && data.password!==data.password_confirmation) {
      setFields({password_confirmation:['Les mots de passe ne correspondent pas.']});setBusy(false);return;
    }
    const route={register:'register',login:'login','forgot-password':'password-reset','reset-password':'password-reset/confirm'}[mode];
    try {
      const response=await authRequest(route,{...data,...(mode==='reset-password'?link:{})}) as {message?:string};
      if(mode==='forgot-password') setMessage(response.message||'Demande enregistrée.');
      else window.location.replace(mode==='login'?'/dashboard':'/login?reason='+(mode==='register'?'registered':'reset'));
    } catch(error) {
      setMessage(error instanceof Error?error.message:'Connexion impossible. Réessayez.');
      if(error instanceof ApiError) setFields(error.fields);
      notice.current?.focus();
    } finally {setBusy(false);}
  }
  function field(name:string,label:string,type='text',autoComplete?:string) {
    const password=name.startsWith('password');
    return <div className="field" key={name}><label htmlFor={name}>{label}</label>
      <input id={name} name={name} type={password&&visible?'text':type} required autoComplete={autoComplete}
        maxLength={password?128:name==='email'?254:100} minLength={password&&mode!=='login'?12:1}
        aria-invalid={!!fields[name]} aria-describedby={fields[name]?name+'-error':undefined}/>
      {fields[name]&&<p id={name+'-error'} className="field-error">{fields[name].join(' ')}</p>}</div>;
  }
  const passwords=mode!=='forgot-password';
  const invalidLink=mode==='reset-password'&&(!link?.uid||!link?.token);
  return <main className="auth-shell"><header><Link className="brand" href="/">studio ✳</Link></header>
    <section className="auth-card"><p className="eyebrow">VOTRE ESPACE CRÉATIF</p><h1>{titles[mode]}</h1>
      <div ref={notice} tabIndex={-1} role="status" aria-live="polite">{message}</div>
      {invalidLink?<p>Lien absent ou invalide. <Link href="/forgot-password">Demander un nouveau lien</Link>.</p>:<form onSubmit={submit} aria-busy={busy}>
        {mode==='register'&&<>{field('first_name','Prénom','text','given-name')}{field('last_name','Nom','text','family-name')}</>}
        {mode!=='reset-password'&&field('email','Adresse e-mail','email','email')}
        {passwords&&<>{field('password','Mot de passe','password',mode==='login'?'current-password':'new-password')}
          {mode!=='login'&&<><p className="hint">12 caractères minimum. Évitez les mots courants et vos informations personnelles.</p>{field('password_confirmation','Confirmer le mot de passe','password','new-password')}</>}
          <label className="show-password"><input type="checkbox" checked={visible} onChange={e=>setVisible(e.target.checked)}/> Afficher le mot de passe</label></>}
        <button type="submit" disabled={busy}>{busy?'Veuillez patienter…':mode==='login'?'Se connecter':mode==='register'?'Créer mon compte':mode==='forgot-password'?'Recevoir un lien':'Enregistrer le mot de passe'}</button>
      </form>}
      <nav aria-label="Compte"><Link href="/login">Connexion</Link><Link href="/register">Inscription</Link><Link href="/forgot-password">Mot de passe oublié</Link></nav>
    </section></main>;
}
