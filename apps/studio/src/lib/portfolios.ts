export type Portfolio = {id:string;account_id:string;name:string;slug:string;description:string;management_state:'active'|'archived';publication_state:'draft';visibility:'private';version:number;etag:string;initial_theme_id:string;initial_theme_version:string;source_template_id:string|null;source_template_version:string|null;created_at:string;updated_at:string};
export type PortfolioInput = {name:string;slug?:string;description?:string};
export type PortfolioPage = {count:number;active_count:number;archived_count:number;page:number;page_size:number;results:Portfolio[]};
export class PortfolioError extends Error {
  status:number;fields:Record<string,string[]>;
  constructor(message:string,status:number,fields:Record<string,string[]>={}){super(message);this.status=status;this.fields=fields;}
}
export function makeSlug(name:string):string {
  return name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,110).replace(/-$/,'');
}
export async function portfolioRequest<T>(path='',method='GET',payload?:Record<string,unknown>,tag?:string,signal?:AbortSignal):Promise<T>{
  const headers:Record<string,string>={};
  if(method!=='GET'){
    const csrf=await fetch('/api/v1/auth/csrf',{cache:'no-store',credentials:'same-origin',signal});
    if(!csrf.ok)throw new PortfolioError('Service indisponible.',csrf.status);
    headers['X-CSRFToken']=(await csrf.json()).csrf_token;
    headers['Content-Type']='application/json';
    if(tag)headers['If-Match']=tag;
  }
  const response=await fetch('/api/v1/portfolios'+path,{method,headers,body:method!=='GET'?JSON.stringify(payload||{}):undefined,credentials:'same-origin',cache:'no-store',signal});
  if(response.status===204)return undefined as T;
  const data=await response.json().catch(()=>({}));
  if(!response.ok){
    if(response.status===401&&typeof window!=='undefined')window.location.replace('/login?reason=expired');
    throw new PortfolioError(data.error?.message||'Le service est indisponible. Réessayez.',response.status,data.error?.fields);
  }
  return data as T;
}
