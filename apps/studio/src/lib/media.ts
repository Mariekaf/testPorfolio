import {PortfolioError} from './portfolios';
export type Asset={id:string;original_name:string;width:number;height:number;size:number;thumbnail_size:number;thumbnail_url:string;file_url:string;etag:string;status:string};
export type MediaPage={count:number;page:number;page_size:number;results:Asset[]};
export async function mediaRequest<T>(path:string,method='GET',body?:FormData|Record<string,unknown>,tag?:string):Promise<T>{
 const headers:Record<string,string>={};
 try{
  if(method!=='GET'){
   const csrf=await fetch('/api/v1/auth/csrf',{cache:'no-store',credentials:'same-origin'});
   if(!csrf.ok)throw new PortfolioError('Reconnectez-vous pour accéder à vos images.',csrf.status);
   headers['X-CSRFToken']=(await csrf.json()).csrf_token;
   if(!(body instanceof FormData))headers['Content-Type']='application/json';
   if(tag)headers['If-Match']=tag;
  }
  const response=await fetch('/api/v1/media'+path,{method,headers,credentials:'same-origin',cache:'no-store',body:method==='GET'?undefined:body instanceof FormData?body:JSON.stringify(body)});
  if(response.status===204)return undefined as T;
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new PortfolioError(data.error?.message||'Le service d’images est indisponible.',response.status);
  return data as T;
 }catch(error){if(error instanceof PortfolioError)throw error;throw new PortfolioError('Connexion impossible. Vos contenus sont conservés.',0);}
}
