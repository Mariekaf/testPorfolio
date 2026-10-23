import {PortfolioError,type Portfolio} from './portfolios';
export type ReadyData=Record<string,any>;
export type ReadyRecord={portfolio:Portfolio;snapshot:ReadyData;etag:string;version:number;media_status:string};
export async function readyRequest<T>(path:string,method='GET',data?:unknown,extra:Record<string,string>={}):Promise<T>{
 try {
 const headers={...extra};
 if(method!=='GET'){
  const csrf=await fetch('/api/v1/auth/csrf',{credentials:'same-origin',cache:'no-store'});
  if(!csrf.ok)throw new PortfolioError('Votre session doit être vérifiée.',csrf.status);
  headers['X-CSRFToken']=(await csrf.json()).csrf_token;headers['Content-Type']='application/json';
 }
 const response=await fetch('/api/v1/'+path,{method,headers,credentials:'same-origin',cache:'no-store',body:method==='GET'?undefined:JSON.stringify(data)});
 const body=await response.json().catch(()=>({}));
 if(!response.ok)throw new PortfolioError(body.error?.message||'Connexion impossible. Vos saisies sont conservées.',response.status,body.error?.fields);
 return body as T;
 }catch(error){if(error instanceof PortfolioError)throw error;throw new PortfolioError('Connexion impossible. Vos saisies sont conservées.',0);}
}
