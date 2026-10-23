import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import SessionShell from '../../components/session-shell';
export const dynamic='force-dynamic';
export default async function Layout({children}:{children:React.ReactNode}){
  const session=(await cookies()).get('portfolio_saas_session')?.value;
  if(!session)redirect('/login');
  let status=503;
  try{status=(await fetch((process.env.SAAS_API_ORIGIN||'http://127.0.0.1:8001')+'/api/v1/auth/me',{cache:'no-store',headers:{Cookie:'portfolio_saas_session='+encodeURIComponent(session)}})).status;}catch{}
  if(status===401||status===403)redirect('/login?reason=expired');
  if(status!==200)return <main><h1>Service temporairement indisponible</h1><p>Réessayez dans un instant.</p></main>;
  return <SessionShell>{children}</SessionShell>;
}
