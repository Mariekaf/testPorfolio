import {test} from 'node:test';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
registerHooks({resolve(specifier,context,next){return next(specifier==='./portfolios'?'./portfolios.ts':specifier,context);}});
const {instanceRequest,creationIntent}=await import('../src/lib/template-instances.ts');
import {PortfolioError} from '../src/lib/portfolios.ts';

test('creation obtains CSRF and sends the exact idempotency key with private credentials',async()=>{
 const original=globalThis.fetch,calls=[];globalThis.fetch=async(url,options)=>{calls.push({url,options});return Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{id:'created'});};
 try{await instanceRequest('/from-template','POST',{name:'Synthetic'},{'Idempotency-Key':'synthetic-key'});assert.equal(calls[1].options.headers['Idempotency-Key'],'synthetic-key');assert.equal(calls[1].options.headers['X-CSRFToken'],'synthetic');assert.equal(calls[1].options.credentials,'same-origin');assert.equal(calls[1].options.cache,'no-store');}finally{globalThis.fetch=original;}
});
test('save sends content and customization with exact version precondition',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async(url,options)=>{if(url.endsWith('/csrf'))return Response.json({csrf_token:'synthetic'});assert.equal(options.headers['If-Match'],'"portfolio:synthetic:7"');assert.deepEqual(JSON.parse(options.body),{content:{},customization:{}});return Response.json({version:8});};
 try{assert.equal((await instanceRequest('/synthetic/design','PUT',{content:{},customization:{}},{'If-Match':'"portfolio:synthetic:7"'})).version,8);}finally{globalThis.fetch=original;}
});
test('conflict and expired session surface errors without discarding caller state',async()=>{
 const original=globalThis.fetch;
 try{for(const status of [401,412]){globalThis.fetch=async(url)=>Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic'}:{error:{message:'Synthetic conflict'}},{status:url.endsWith('/csrf')?200:status});await assert.rejects(instanceRequest('/synthetic/design'),e=>e instanceof PortfolioError&&e.status===status);}}finally{globalThis.fetch=original;}
});
test('new creation intents have distinct keys and explicit timestamps',()=>{
 const a=creationIntent(),b=creationIntent();assert.notEqual(a.key,b.key);assert.match(a.key,/^[a-f0-9-]{36}$/);assert.ok(a.createdAt<=Date.now());
});
