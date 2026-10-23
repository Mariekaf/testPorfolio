import Link from 'next/link';
import {readTemplate,type TemplateDescriptor} from '../../lib/template-catalogue.server';
import type {Snapshot} from '../../lib/template-render';
import TemplateThumbnail from '../../components/templates/template-thumbnail';
import styles from '../../components/templates/template-editor.module.css';
export const dynamic='force-dynamic';
export default async function Page({searchParams}:{searchParams:Promise<{category?:string}>}){
 const {category}=await searchParams;
 const {data}=await readTemplate<{results:TemplateDescriptor[]}>(category?'?category='+encodeURIComponent(category):'');
 const previews=data?await Promise.all(data.results.map(item=>readTemplate<Snapshot>(`/${item.id}/versions/${item.version}/preview`))):[];
 return <section><header className={styles.libraryHeading}><Link href="/dashboard">← Mes portfolios</Link><p className="eyebrow">LA BIBLIOTHÈQUE</p><h1>Deux regards sur votre travail.</h1><p>Choisissez votre point de départ. Composez ensuite un portfolio qui vous ressemble.</p></header><nav className={styles.filters} aria-label="Catégories de templates">{[['','Tous'],['minimal','Minimal'],['editorial','Editorial']].map(([value,label])=><Link key={value} aria-current={(category||'')===value?'page':undefined} href={value?'/templates?category='+value:'/templates'}>{label}</Link>)}</nav>{data?<><div className={styles.libraryGrid}>{data.results.map((item,index)=><article className={styles.libraryCard} key={item.id+'@'+item.version}><div className={styles.thumbnail} aria-hidden="true" inert>{previews[index].data&&<TemplateThumbnail snapshot={previews[index].data!}/>}</div><div className={styles.cardBody}><p className="eyebrow">{item.category.toUpperCase()} / {item.version}</p><h2>{item.name}</h2><p>{item.description}</p><div className={styles.cardActions}><Link className="button secondary" href={`/templates/${item.id}/${item.version}`}>Voir l’aperçu</Link><Link className="button" href={`/templates/${item.id}/${item.version}/use`}>Utiliser ce template</Link></div></div></article>)}</div>{data.results.length===0&&<p role="status">Aucun template disponible actuellement.</p>}</>:<p role="alert">Bibliothèque temporairement indisponible. Réessayez plus tard.</p>}</section>;
}
