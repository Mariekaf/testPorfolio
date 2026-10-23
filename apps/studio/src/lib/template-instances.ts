import {PortfolioError} from './portfolios';
import type {Snapshot} from './template-render';
export type DesignRecord={portfolio_id:string;version:number;etag:string;snapshot:Snapshot};
export async function instanceRequest<T>(path:string,method='GET',payload?:unknown,headers:Record<string,string>={}):Promise<T>{
 if(method!=='GET'){
  const csrf=await fetch('/api/v1/auth/csrf',{credentials:'same-origin',cache:'no-store'});
  if(!csrf.ok)throw new PortfolioError('Votre session doit être vérifiée.',csrf.status);
  headers={...headers,'X-CSRFToken':(await csrf.json()).csrf_token,'Content-Type':'application/json'};
 }
 const response=await fetch('/api/v1/portfolios'+path,{method,credentials:'same-origin',cache:'no-store',headers,body:method==='GET'?undefined:JSON.stringify(payload)});
 const data=await response.json().catch(()=>({}));
 // Keep local edits in memory on 401: the user decides when to reconnect.
 if(!response.ok)throw new PortfolioError(data.error?.message||'Connexion impossible. Réessayez.',response.status,data.error?.fields);
 return data as T;
}
export function creationIntent(){return {key:crypto.randomUUID(),createdAt:Date.now()};}
