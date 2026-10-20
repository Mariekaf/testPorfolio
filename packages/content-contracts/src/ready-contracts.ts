/** E0702 offline validation only. No application imports, API, DB, upload or renderer. */
import {Ajv2020} from 'ajv/dist/2020.js';
import type {AnySchemaObject} from 'ajv';
type Data=Record<string,any>;
export const READY_LIMIT=262144;
export const READY_ROLES=['descriptor','snapshot','style-policy','fonts','responsive','demo-content'];
export class ReadyContractError extends Error {constructor(){super('Invalid or unsupported ready template contract.');this.name='ReadyContractError';}}
export function requireReady(value:unknown):asserts value {if(!value)throw new ReadyContractError();}
export function readyBudget(v:any,depth=0):number {
 requireReady(depth<=32);
 if(v===null)return 4;
 if(typeof v==='boolean')return 5;
 if(typeof v==='string'){
  requireReady(!/[\uD800-\uDFFF]/u.test(v));
  return 2+[...v].reduce((n,c)=>n+Math.max(c.codePointAt(0)!<32||c==='\\'||c==='"'?6:0,new TextEncoder().encode(c).length),0);
 }
 if(typeof v==='number'){requireReady(Number.isFinite(v)&&Math.abs(v)<=Number.MAX_SAFE_INTEGER);return 24;}
 if(Array.isArray(v))return 2+v.length+v.reduce((n,x)=>n+readyBudget(x,depth+1),0);
 requireReady(v&&typeof v==='object'&&(Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null));
 return 2+Object.keys(v).length*2+Object.entries(v).reduce((n,[k,x])=>n+readyBudget(k,depth+1)+readyBudget(x,depth+1),0);
}
function stable(v:any):string {return JSON.stringify(v,(_k,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);}
const nonblank=(s:string)=>s.replace(/[\x09-\x0D\x20\x85\xA0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF]/g,'').length>0;
const equal=(a:unknown,b:unknown)=>stable(a)===stable(b);
function contrast(a:string,b:string):number {
 const lum=(s:string)=>[.2126,.7152,.0722].reduce((n,w,i)=>{const c=parseInt(s.slice(1+i*2,3+i*2),16)/255;return n+w*(c<=.04045?c/12.92:((c+.055)/1.055)**2.4);},0);
 const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
const expected=[
 ['navigation','creative-navigation.v1',{identity:'identity_name',logo:'brand_logo'}],
 ['hero','creative-hero.v1',{title:'hero_title',subtitle:'hero_subtitle',portrait:'hero_portrait',cta:'hero_cta'}],
 ['about','creative-about.v1',{heading:'about_heading',body:'about_body'}],
 ['projects','creative-projects.v1',{heading:'projects_heading',items:'selected_projects'}],
 ['contact','creative-contact.v1',{heading:'contact_heading',link:'contact_link',socials:'socials'}],
 ['footer','creative-footer.v1',{note:'footer_note'}],
] as const;
export function createReadySchemas(schemas:Record<string,AnySchemaObject>){
 const ajv=new Ajv2020({strict:true,strictTypes:false,strictRequired:false,coerceTypes:false,removeAdditional:false,useDefaults:false});
 ajv.addFormat('uri',true);ajv.addFormat('email',true);
 ajv.addFormat('uuid',{type:'string',validate:(s:string)=>/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(s)&&s.length===36});
 for(const [name,schema]of Object.entries(schemas)){requireReady(/^[a-z0-9.-]+\.json$/.test(name)&&!schema.$id);ajv.addSchema({...structuredClone(schema),$id:'https://ready.invalid/'+name});}
 return function check(name:string,value:unknown){
  requireReady(readyBudget(value)<=READY_LIMIT);
  const validator=ajv.getSchema('https://ready.invalid/'+name);requireReady(validator&&validator(value));
 };
}
export function createReadyValidator(schemas:Record<string,AnySchemaObject>,input:unknown){try{return readyValidator(schemas,input);}catch{throw new ReadyContractError();}}
function readyValidator(schemas:Record<string,AnySchemaObject>,input:unknown){
 const check=createReadySchemas(schemas),b=structuredClone(input) as Data;
 for(const [role,schema] of [['descriptor','descriptor.v2.json'],['style-policy','style-policy.v1.json'],['fonts','fonts.v1.json'],['responsive','responsive.v1.json'],['demo-content','content.v2.json']])check(schema,b[role]);
 requireReady(equal(Object.keys(b).sort(),[...READY_ROLES].sort()));
 const d=b.descriptor;
 requireReady(equal(d.template,{id:'creative-editorial',version:'1.0.0'}));
 requireReady(equal(d.renderer,{id:'ready-portfolio',version:'1.0.0'})&&d.status==='draft');
 requireReady(equal(d.required_capabilities,['typed-slots-v2','ready-renderer-v1','safe-media-v1','manual-publication-v1']));
 requireReady(equal(d.customization_policy,b['style-policy'].reference)&&equal(d.customization_policy,{id:'creative-editorial-style',version:'1.0.0'}));
 for(const palette of Object.values(b['style-policy'].palettes) as Data[]){
  requireReady(Object.values(palette).every(c=>typeof c==='string'&&c.length===7&&/^#[0-9A-Fa-f]{6}$/.test(c)));
  for(const k of ['background','surface'])requireReady(contrast(palette.text,palette[k])>=4.5);
  requireReady(contrast(palette.accent,palette.surface)>=4.5);
 }
 requireReady(equal(d.publication_policy,{required_text_slots:['identity_name','hero_title'],project_slot:'selected_projects',min_real_projects:1,contact_slots:['contact_link','socials']}));
 function validate(input:unknown){
  try{
   check('snapshot.v3.json',input);const doc=input as Data,slots=doc.content.slots as Data;
   requireReady(equal(doc.composition.template,d.template));
   requireReady(equal(doc.composition.sections,expected.map(([id,variant,slot_bindings])=>({id,variant,slot_bindings}))));
   requireReady(equal(doc.composition.responsive_profile,b.responsive.reference));
   requireReady(equal(Object.keys(slots).sort(),Object.keys(d.slots).sort()));
   const links:Data[]=[],images:Data[]=[],projectIds=new Set<string>();
   for(const [key,definition]of Object.entries(d.slots) as [string,Data][]){
    const value=slots[key];requireReady(value.type===definition.type);
    switch(value.type){
     case 'text':requireReady([...value.value].length<=definition.max_length);break;
     case 'rich_text':{
      const text=value.blocks.flatMap((p:Data)=>p.children.map((c:Data)=>c.text)).join('');
      requireReady([...text].length<=definition.max_length&&readyBudget(value)<=12288);break;
     }
     case 'image':case 'logo':if(value.value!==null)images.push(value.value);break;
     case 'link':if(value.target!==null){links.push(value.target);}break;
     case 'project_list':
      requireReady(value.items.length<=definition.max_items);
      for(const p of value.items){requireReady(!projectIds.has(p.id));projectIds.add(p.id);if(p.cover!==null)images.push(p.cover);if(p.target!==null){requireReady(p.target.kind==='external');links.push(p.target);}}
      break;
     case 'social_links':{
      requireReady(value.items.length<=definition.max_items);const networks=new Set<string>();
      const domains:Data={linkedin:'linkedin.com',behance:'behance.net',dribbble:'dribbble.com',github:'github.com'};
      for(const item of value.items){
       requireReady(!networks.has(item.network)&&item.target.kind==='external');networks.add(item.network);links.push(item.target);
       if(item.network!=='other'){const host=new URL(item.target.url).hostname,domain=domains[item.network];requireReady(host===domain||host.endsWith('.'+domain));}
      }
     }
    }
   }
   const visible=new Set(['navigation','hero','footer']);
   if(slots.about_body.blocks.some((p:Data)=>p.children.some((c:Data)=>nonblank(c.text))))visible.add('about');
   if(slots.selected_projects.items.some((p:Data)=>nonblank(p.title)))visible.add('projects');
   if(slots.contact_link.target!==null&&nonblank(slots.contact_link.label)||slots.socials.items.some((s:Data)=>nonblank(s.label)))visible.add('contact');
   for(const target of links){
    if(target.kind==='external'){
     requireReady(/^[\x00-\x7F]*$/.test(target.url)&&!/[\x00-\x20\x7F]/.test(target.url));
     const match=/^https:\/\/([A-Za-z0-9][A-Za-z0-9.-]*)(?::([0-9]{1,5}))?([/?#][^\s\\]*)?$/.exec(target.url);
     requireReady(match&&match[0]===target.url);
     requireReady(match[1].split('.').every(x=>x&&x.length<=63&&!x.startsWith('-')&&!x.endsWith('-')));
     requireReady(!match[2]||Number(match[2])>=1&&Number(match[2])<=65535);
     requireReady(!/%(?![0-9A-Fa-f]{2})/.test(target.url));
    }else if(target.kind==='email'){
     const match=/^[A-Za-z0-9._+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$/.exec(target.address);requireReady(match&&match[0]===target.address);
     const [local,host]=target.address.split('@');requireReady(!local.startsWith('.')&&!local.endsWith('.')&&!local.includes('..'));
     requireReady(host.split('.').every((x:string)=>x&&x.length<=63&&!x.startsWith('-')&&!x.endsWith('-')));
    }else requireReady(target.kind==='section'&&visible.has(target.section_id));
   }
   for(const image of images)requireReady(!image.decorative);
   const style=b['style-policy'],presentation=doc.presentation,overrides=doc.customization.style_overrides;
   requireReady(equal(presentation.style_policy,style.reference)&&equal(presentation.defaults,b.snapshot.presentation.defaults));
   const palette={...style.palettes[overrides.palette_id??presentation.defaults.palette_id],...overrides.colors};
   requireReady(Object.values(palette).every(c=>typeof c==='string'&&c.length===7&&/^#[0-9A-Fa-f]{6}$/.test(c)));
   const font=overrides.font_ref??presentation.defaults.font_ref;
   requireReady(style.allowed_font_refs.some((f:Data)=>equal(f,font))&&b.fonts.fonts.some((f:Data)=>equal(f.reference,font)));
   for(const background of ['background','surface'])requireReady(contrast(palette.text,palette[background])>=4.5);
   requireReady(contrast(palette.accent,palette.surface)>=4.5);
   return {schema_version:3,visible_sections:expected.map(([id])=>id).filter(id=>visible.has(id)),palette,font_ref:structuredClone(font)};
  }catch{throw new ReadyContractError();}
 }
 function readiness(doc:any,facts:Data){
  validate(doc);check('assessment-facts.v1.json',facts);const slots=doc.content.slots,errors:string[]=[];
  for(const key of d.publication_policy.required_text_slots)if(!nonblank(slots[key].value))errors.push('required:'+key);
  if(!facts.account_id||!slots.selected_projects.items.some((p:Data)=>(facts.verified_user_project_ids??[]).includes(p.id)&&nonblank(p.title)))errors.push('real_project_required');
  const contact=slots.contact_link.target;
  if(!(contact&&['email','external'].includes(contact.kind)&&nonblank(slots.contact_link.label))&&!slots.socials.items.some((s:Data)=>nonblank(s.label)))errors.push('contact_required');
  const assets:string[]=[];
  for(const value of Object.values(slots) as Data[]){
   if(['image','logo'].includes(value.type)&&value.value!==null){assets.push(value.value.asset_id);if(!nonblank(value.value.alt))errors.push('alt_required:'+value.value.asset_id);}
   if(value.type==='project_list')for(const p of value.items)if(p.cover!==null){assets.push(p.cover.asset_id);if(!nonblank(p.cover.alt))errors.push('alt_required:'+p.cover.asset_id);}
  }
  for(const id of [...new Set(assets)].sort()){
   const asset=facts.assets?.[id];if(!asset||!facts.account_id||asset.account_id!==facts.account_id||asset.state!=='ready'||asset.rights_confirmed!==true)errors.push('media_unresolved:'+id);
  }
  return {content_ready:errors.length===0,publication_enabled:false,errors};
 }
 validate(b.snapshot);validate({...b.snapshot,content:b['demo-content']});
 return {validate,readiness};
}
