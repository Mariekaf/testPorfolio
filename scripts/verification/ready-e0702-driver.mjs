/** stdin offline parity protocol; no settings or API imports. */
import {readFileSync} from 'node:fs';
import {loadReadyRegistry,strictReadyJson} from '../../packages/content-contracts/src/ready-registry.ts';
const request=JSON.parse(readFileSync(0,'utf8'));
try{
 if(request.mode==='raw'){strictReadyJson(Buffer.from(request.raw,'base64'));console.log(JSON.stringify({valid:true}));}
 else if(request.mode==='registry'){const r=loadReadyRegistry(request.root);const e=r.get();console.log(JSON.stringify({valid:true,digest:e.bundle_digest,status:e.status}));}
 else {
  const r=loadReadyRegistry(),v=r.validator();const results=request.cases.map(c=>{try{return {result:v.validate(c.document),readiness:v.readiness(c.document,c.facts)}}catch{return {error:true}}});
  console.log(JSON.stringify(results));
 }
}catch{console.log(JSON.stringify({error:true}));}
