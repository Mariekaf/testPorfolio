import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import Dashboard from './dashboard';
export const dynamic = 'force-dynamic';
export default async function Page() {
  const session=(await cookies()).get('portfolio_saas_session')?.value;
  if(!session) redirect('/login');
  const origin=process.env.SAAS_API_ORIGIN || 'http://127.0.0.1:8001';
  let status=503;
  try {
    const response=await fetch(origin+'/api/v1/auth/me',{cache:'no-store',headers:{Cookie:'portfolio_saas_session='+encodeURIComponent(session)}});
    status=response.status;
  } catch { /* No sensitive network details in the UI. */ }
  if(status===401 || status===403) redirect('/login?reason=expired');
  if(status!==200) return <main><h1>Service temporairement indisponible</h1><p>Réessayez dans un instant.</p></main>;
  return <Dashboard/>;
}
