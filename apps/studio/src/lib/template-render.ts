/** Shared, deterministic document resolution. No persistence or publication. */
export type SectionType = 'hero'|'about'|'projects'|'skills'|'contact';
export type Settings = {spacing:'compact'|'normal'|'airy';alignment:'start'|'center';emphasis:'quiet'|'strong'};
export type Section = {id:string;type:SectionType;variant:string;visible:boolean;required:boolean;toggleable:boolean;reorderable:boolean;presentation_policy:{[K in keyof Settings]:Settings[K][]}};
export type Project = {id:string;title:string;summary:string;url:string|null};
export type ContentData = {
 hero:{title:string;subtitle:string;cta_label:string};
 about:{heading:string;body:string};
 projects:{heading:string;items:Project[]};
 skills:{heading:string;items:string[]};
 contact:{heading:string;body:string;email:string|null};
};
export type ContentSection = {[K in SectionType]:{section_id:string;type:K;data:ContentData[K]}}[SectionType];
export type Snapshot = {
 schema_version:1;
 composition:{schema_version:1;template:{id:string;version:string};layout:'minimal-stack'|'editorial-grid';sections:Section[]};
 content:{schema_version:1;sections:ContentSection[]};
 presentation:{schema_version:1;theme:{id:'studio-neutral';version:'1.0.0'};sections:{section_id:string;settings:Settings}[]};
 customization:{schema_version:1;section_order?:string[];sections:{section_id:string;visible?:boolean;presentation?:Partial<Settings>}[]};
 experience:null;
};
export function safeProjectUrl(value:string|null):string|undefined {
 if(!value||/[\u0000-\u0020]/.test(value))return undefined;
 try{const url=new URL(value);return url.protocol==='https:'&&url.hostname&&!url.username&&!url.password?url.href:undefined;}catch{return undefined;}
}
export function effectiveSections(snapshot:Snapshot) {
 if(snapshot.schema_version!==1||snapshot.experience!==null||snapshot.presentation.theme.id!=='studio-neutral'||snapshot.presentation.theme.version!=='1.0.0')throw new Error('Unsupported render document');
 const source=snapshot.composition.sections;
 const ids=source.map(s=>s.id);
 const order=snapshot.customization.section_order??ids;
 if(new Set(ids).size!==ids.length||order.length!==ids.length||new Set(order).size!==ids.length||order.some(id=>!ids.includes(id)))throw new Error('Invalid section order');
 if(source.some((s,i)=>!s.reorderable&&order[i]!==s.id))throw new Error('Anchored section moved');
 return order.map(id=>{
  const section=source.find(s=>s.id===id)!;
  const content=snapshot.content.sections.find(s=>s.section_id===id);
  const base=snapshot.presentation.sections.find(s=>s.section_id===id);
  const override=snapshot.customization.sections.find(s=>s.section_id===id);
  if(!content||!base||content.type!==section.type)throw new Error('Missing section data');
  const visible=override?.visible??section.visible;
  if((section.required&&!visible)||(!section.toggleable&&visible!==section.visible))throw new Error('Protected section visibility');
  const settings={...base.settings,...override?.presentation};
  for(const key of ['spacing','alignment','emphasis'] as const)if(!(section.presentation_policy[key] as readonly string[]).includes(settings[key]))throw new Error('Unsupported setting');
  return {section,content,settings,visible};
 }).filter(s=>s.visible);
}
