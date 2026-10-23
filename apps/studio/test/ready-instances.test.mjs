import {test} from 'node:test';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
registerHooks({resolve(specifier,context,next){return next(specifier==='./portfolios'?'./portfolios.ts':specifier,context);}});
const {readyRequest}=await import('../src/lib/ready-instances.ts');
const {PortfolioError}=await import('../src/lib/portfolios.ts');
test('ready creation uses private session CSRF exact intention and no public API',async()=>{
 const before=globalThis.fetch,calls=[];globalThis.fetch=async(url,options)=>{calls.push([url,options]);return Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{version:1});};
 try{await readyRequest('ready-portfolios','POST',{name:'Synthetic'},{'Idempotency-Key':'intent'});assert.equal(calls[1][0],'/api/v1/ready-portfolios');assert.equal(calls[1][1].headers['X-CSRFToken'],'synthetic');assert.equal(calls[1][1].headers['Idempotency-Key'],'intent');assert.equal(calls[1][1].credentials,'same-origin');assert.equal(calls[1][1].cache,'no-store');}finally{globalThis.fetch=before;}
});
test('ready update retains exact ETag and only requested mutable fields',async()=>{
 const before=globalThis.fetch;globalThis.fetch=async(url,options)=>{if(url.endsWith('/csrf'))return Response.json({csrf_token:'synthetic'});assert.equal(options.method,'PUT');assert.equal(options.headers['If-Match'],'"v2"');assert.deepEqual(JSON.parse(options.body),{content:{},customization:{}});return Response.json({version:3});};
 try{assert.equal((await readyRequest('ready-portfolios/id','PUT',{content:{},customization:{}},{'If-Match':'"v2"'})).version,3);}finally{globalThis.fetch=before;}
});
test('ready failures surface status without mutating caller draft',async()=>{
 const before=globalThis.fetch;const draft={content:{slots:{hero_title:{value:'Keep me'}}},customization:{}};
 try{for(const status of [400,401,403,404,409,412,428,503]){globalThis.fetch=async(url)=>Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{error:{message:'Synthetic error'}},{status:url.endsWith('/csrf')?200:status});await assert.rejects(readyRequest('ready-portfolios/id','PUT',draft),e=>e instanceof PortfolioError&&e.status===status);assert.equal(draft.content.slots.hero_title.value,'Keep me');}}finally{globalThis.fetch=before;}
});
test('network failure readable and input retained; server details not exposed',async()=>{
 const before=globalThis.fetch;globalThis.fetch=async()=>{throw new TypeError('internal network details');};
 try{await assert.rejects(readyRequest('ready-portfolios/id'),e=>e.status===0&&e.message==='Connexion impossible. Vos saisies sont conservées.');}finally{globalThis.fetch=before;}
});
