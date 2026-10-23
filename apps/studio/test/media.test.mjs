import {test} from 'node:test';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
registerHooks({resolve(s,c,n){return n(s==='./portfolios'?'./portfolios.ts':s,c);}});
const {mediaRequest}=await import('../src/lib/media.ts');
const {privateImage}=await import('../src/lib/private-media-resolution.ts');
const identity='11111111-1111-4111-8111-111111111111';
test('multipart upload preserves browser boundary and sends session CSRF only',async()=>{
 const original=fetch,calls=[];globalThis.fetch=async(url,options)=>{calls.push([url,options]);return Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{results:[]});};
 try{const form=new FormData();form.append('files',new Blob(['synthetic']),'synthetic.png');form.append('rights','true');await mediaRequest('/assets','POST',form);assert.equal(calls[1][1].body,form);assert.equal(calls[1][1].headers['Content-Type'],undefined);assert.equal(calls[1][1].headers['X-CSRFToken'],'synthetic');assert.equal(calls[1][1].credentials,'same-origin');assert.equal(calls[1][1].cache,'no-store');}finally{globalThis.fetch=original;}
});
test('asset delete includes confirmation CSRF and exact asset precondition',async()=>{
 const original=fetch;globalThis.fetch=async(url,options)=>{if(url.endsWith('/csrf'))return Response.json({csrf_token:'synthetic'});assert.equal(options.method,'DELETE');assert.equal(options.headers['If-Match'],'"asset-version"');assert.deepEqual(JSON.parse(options.body),{confirm:true});return new Response(null,{status:204});};
 try{await mediaRequest('/assets/'+identity,'DELETE',{confirm:true},'"asset-version"');}finally{globalThis.fetch=original;}
});
test('media status failures preserve caller data and expose readable error',async()=>{
 const original=fetch,form=new FormData();form.append('rights','true');
 try{for(const status of [400,401,403,404,409,412,413,428,503]){globalThis.fetch=async(url)=>Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{error:{message:'Erreur synthétique'}},{status:url.endsWith('/csrf')?200:status});await assert.rejects(mediaRequest('/assets','POST',form),e=>e.status===status);assert.equal(form.get('rights'),'true');}}finally{globalThis.fetch=original;}
});
test('private projection accepts only exact same-origin asset URL and sane dimensions',()=>{
 const valid={state:'ready',asset_id:identity,src:`/api/v1/media/assets/${identity}/file`,width:900,height:1125};
 assert.equal(privateImage(identity,{[identity]:valid}).state,'available');
 for(const patch of [{src:'https://external.invalid/x'},{asset_id:'other'},{state:'processing'},{width:0},{height:30000},{src:'/../.local/file'}])assert.equal(privateImage(identity,{[identity]:{...valid,...patch}}).state,'missing');
 assert.equal(privateImage('../x',{'../x':{...valid,asset_id:'../x',src:'/api/v1/media/assets/../x/file'}}).state,'missing');
 assert.equal(privateImage(identity,Object.create({[identity]:valid})).state,'missing');
});
test('network error never exposes private endpoint details',async()=>{
 const original=fetch;globalThis.fetch=async()=>{throw new Error('sensitive path');};
 try{await assert.rejects(mediaRequest('/assets'),e=>e.message==='Connexion impossible. Vos contenus sont conservés.');}finally{globalThis.fetch=original;}
});
