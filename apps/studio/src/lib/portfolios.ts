export type Portfolio = {id:string;name:string;slug:string;description:string;portfolio_type:'personal'|'professional'|'business';status:string;visibility:string;created_at:string;updated_at:string};
export type PortfolioInput = {name:string;slug?:string;description?:string;portfolio_type:string};
export class PortfolioError extends Error {constructor(message:string,public status:number){super(message);}}
export async function portfolioRequest(path='',method='GET',payload?:Record<string,string>):Promise<any>{
  const headers:Record<string,string>={};
  if(method!=='GET'){
    const csrf=await fetch('/api/v1/auth/csrf',{cache:'no-store',credentials:'same-origin'});
    if(!csrf.ok)throw new PortfolioError('Service indisponible.',csrf.status);
    headers['X-CSRFToken']=(await csrf.json()).csrf_token;
    if(payload)headers['Content-Type']='application/json';
  }
  const response=await fetch('/api/v1/portfolios/'+path,{method,headers,body:payload?JSON.stringify(payload):undefined,credentials:'same-origin',cache:'no-store'});
  if(response.status===204)return null;
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new PortfolioError(data.error?.message||'Une erreur est survenue.',response.status);
  return data;
}
