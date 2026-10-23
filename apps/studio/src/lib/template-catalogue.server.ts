import {cookies} from 'next/headers';
import {redirect,notFound} from 'next/navigation';
export type TemplateDescriptor={schema_version:1;id:string;version:string;name:string;category:string;description:string;availability:'available'|'unavailable'|'retired'};
export async function readTemplate<T>(path:string):Promise<{data:T|null}> {
 const session=(await cookies()).get('portfolio_saas_session')?.value;
 if(!session)redirect('/login');
 let response:Response;
 try{response=await fetch((process.env.SAAS_API_ORIGIN||'http://127.0.0.1:8001')+'/api/v1/templates'+path,{cache:'no-store',headers:{Cookie:'portfolio_saas_session='+encodeURIComponent(session)}});}catch{return {data:null};}
 if(response.status===401||response.status===403)redirect('/login?reason=expired');
 if(response.status===404)notFound();
 if(!response.ok)return {data:null};
 return {data:await response.json() as T};
}
