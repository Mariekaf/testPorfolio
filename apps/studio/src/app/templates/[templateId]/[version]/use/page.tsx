import TemplateCreate from '../../../../../components/templates/template-create';
import {readTemplate,type TemplateDescriptor} from '../../../../../lib/template-catalogue.server';
export default async function Page({params}:{params:Promise<{templateId:string;version:string}>}){
 const {templateId,version}=await params;
 const {data}=await readTemplate<TemplateDescriptor>(`/${encodeURIComponent(templateId)}/versions/${encodeURIComponent(version)}`);
 if(!data||data.availability!=='available')return <section><h1>Template indisponible</h1><p>Choisissez une autre composition dans la bibliothèque.</p></section>;
 return <TemplateCreate templateId={templateId} version={version}/>;
}
