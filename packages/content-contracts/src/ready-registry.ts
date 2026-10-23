/** Node-only offline Git bundle loader. Never imported by Studio/public routes. */
import {readFileSync,lstatSync,realpathSync} from 'node:fs';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import type {AnySchemaObject} from 'ajv';
import {createReadySchemas,createReadyValidator,requireReady,ReadyContractError,readyBudget,READY_LIMIT,READY_ROLES} from './ready-contracts.ts';
type Data=Record<string,any>;
/** JSON.parse alone loses duplicate keys. Scan bounded JSON first, then parse. */
export function strictReadyJson(raw:Uint8Array):any {try{return parseReadyJson(raw);}catch{throw new ReadyContractError();}}
function parseReadyJson(raw:Uint8Array):any {
 requireReady(raw.byteLength<=READY_LIMIT);const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(raw);let i=0;
 function whitespace(){while(/[\x20\t\r\n]/.test(text[i]??'x'))i++;}
 function string(){const start=i++;while(i<text.length){const c=text[i++];if(c==='\\'){i++;continue;}if(c==='"')return JSON.parse(text.slice(start,i));}throw new ReadyContractError();}
 function value(depth:number){
  requireReady(depth<=32);whitespace();const c=text[i];
  if(c==='"'){string();return;}
  if(c==='{'||c==='['){
   const object=c==='{',end=object?'}':']',keys=new Set<string>();i++;whitespace();if(text[i]===end){i++;return;}
   while(i<text.length){
    if(object){requireReady(text[i]==='"');const key=string();requireReady(!keys.has(key));keys.add(key);whitespace();requireReady(text[i++]===':');}
    value(depth+1);whitespace();if(text[i]===end){i++;return;}requireReady(text[i++ ]===',');whitespace();
   }
   throw new ReadyContractError();
  }
  const match=/^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(text.slice(i));requireReady(match);i+=match[0].length;
 }
 value(0);whitespace();requireReady(i===text.length);const data=JSON.parse(text);requireReady(readyBudget(data)<=READY_LIMIT);return data;
}
export function readReadySchemas():Record<string,AnySchemaObject>{
 const root=new URL('../../../contracts/schemas/ready/',import.meta.url),names=['content.v2.json','snapshot.v3.json','descriptor.v2.json','style-policy.v1.json','fonts.v1.json','responsive.v1.json','manifest.v2.json','assessment-facts.v1.json'];
 return Object.fromEntries(names.map(name=>[name,strictReadyJson(readFileSync(new URL(name,root)))]));
}
export function loadReadyRegistry(rootPath:string|URL=new URL('../../../contracts/ready-templates/',import.meta.url)){
 try{
  const root=typeof rootPath==='string'?resolve(rootPath):resolve(fileURLToPath(rootPath));
  requireReady(!lstatSync(root).isSymbolicLink());const canonical=realpathSync(root);
  function read(relative:string){
   requireReady(typeof relative==='string'&&!relative.includes('\\'));
   const parts=relative.split('/');requireReady(parts.every(p=>p&&p!=='.'&&p!=='..'&&!p.includes(':')));
   let path=root;for(const p of parts){path=resolve(path,p);requireReady(!lstatSync(path).isSymbolicLink());}
   const real=realpathSync(path);requireReady(real.startsWith(canonical+sep)&&lstatSync(path).isFile()&&lstatSync(path).size<=READY_LIMIT);
   return readFileSync(path);
  }
  const schemas=readReadySchemas(),check=createReadySchemas(schemas),manifest=strictReadyJson(read('manifest.v2.json'));
  check('manifest.v2.json',manifest);const entries=new Map<string,Data>(),seen=new Set<string>();
  for(const entry of manifest.entries){
   const identity=entry.template,key=identity.id+'@'+identity.version;requireReady(!entries.has(key));
   requireReady(['draft','deprecated','retired','quarantined'].includes(entry.status));
   const bundle:Data={},roles=new Set<string>();
   for(const file of entry.files){
    requireReady(!roles.has(file.role)&&!seen.has(file.path.toLowerCase()));
    requireReady(file.path===`${identity.id}/${identity.version}/${file.role}.json`);roles.add(file.role);seen.add(file.path.toLowerCase());
    const raw=read(file.path);requireReady(raw.length===file.bytes&&createHash('sha256').update(raw).digest('hex')===file.sha256);
    bundle[file.role]=strictReadyJson(raw);
   }
   requireReady([...READY_ROLES].sort().join(',')===[...roles].sort().join(','));
   const files=[...entry.files].sort((a:Data,b:Data)=>a.path<b.path?-1:a.path>b.path?1:0).map((f:Data)=>({path:f.path,bytes:f.bytes,sha256:f.sha256}));
   const digest=createHash('sha256').update(JSON.stringify(files),'utf8').digest('hex');requireReady(digest===entry.bundle_digest);
   createReadyValidator(schemas,bundle);requireReady(identity.id===bundle.descriptor.template.id&&identity.version===bundle.descriptor.template.version);
   entries.set(key,{template:identity,status:entry.status,bundle_digest:digest,bundle});
  }
  return {
   get(id='creative-editorial',version='1.0.0'){const entry=entries.get(id+'@'+version);requireReady(entry);return structuredClone(entry);},
   validator(id='creative-editorial',version='1.0.0'){const entry=entries.get(id+'@'+version);requireReady(entry);return createReadyValidator(schemas,entry.bundle);}
  };
 }catch{throw new ReadyContractError();}
}
