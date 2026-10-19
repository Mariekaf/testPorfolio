import TemplatePreview from '../../../../components/templates/template-preview';
import type {Snapshot} from '../../../../lib/template-render';
import {readTemplate} from '../../../../lib/template-catalogue.server';
export const dynamic='force-dynamic';
export default async function Page({params}:{params:Promise<{templateId:string;version:string}>}){
 const {templateId,version}=await params;
 const {data}=await readTemplate<Snapshot>(`/${encodeURIComponent(templateId)}/versions/${encodeURIComponent(version)}/preview`);
 if(!data)return <section><h1>Aperçu indisponible</h1><p>Réessayez plus tard ; aucun portfolio n’a été créé.</p></section>;
 return <TemplatePreview snapshot={data}/>;
}
