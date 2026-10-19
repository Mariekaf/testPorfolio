import Link from 'next/link';
import {readTemplate,type TemplateDescriptor} from '../../lib/template-catalogue.server';
export const dynamic='force-dynamic';
export default async function Page(){
 const {data}=await readTemplate<{results:TemplateDescriptor[]}>('');
 return <section className="dashboard-intro"><p className="eyebrow">TEMPLATES / APERÇUS</p><h1>Deux regards sur votre travail.</h1><p>Explorez les compositions Minimal et Editorial. Ces aperçus ne créent ni ne publient de portfolio.</p>{data?<><div className="portfolio-grid">{data.results.map(item=><article className="portfolio-card" key={item.id+'@'+item.version}><p>{item.category.toUpperCase()} / {item.version}</p><h2>{item.name}</h2><p>{item.description}</p><Link href={`/templates/${item.id}/${item.version}`}>Voir l’aperçu →</Link></article>)}</div>{data.results.length===0&&<p role="status">Aucun aperçu disponible actuellement.</p>}</>:<p role="alert">Bibliothèque temporairement indisponible. Réessayez plus tard.</p>}<p><Link href="/dashboard">← Retour au dashboard</Link></p></section>;
}
