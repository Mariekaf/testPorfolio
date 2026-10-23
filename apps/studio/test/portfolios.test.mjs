import {test} from 'node:test';
import assert from 'node:assert/strict';
import {portfolioRequest,PortfolioError,makeSlug} from '../src/lib/portfolios.ts';

test('names produce valid ASCII slugs including French accents',()=>{
  assert.equal(makeSlug(' Études UX / été 2026 '),'etudes-ux-ete-2026');
  assert.equal(makeSlug('東京'),'');
});
test('list uses canonical URL, session cookies and no cache',async()=>{
  const old=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{assert.equal(url,'/api/v1/portfolios?state=archived&page=2');assert.equal(options.credentials,'same-origin');assert.equal(options.cache,'no-store');return Response.json({results:[]});};
  try{assert.deepEqual(await portfolioRequest('?state=archived&page=2'),{results:[]});}finally{globalThis.fetch=old;}
});
test('conditional mutation obtains CSRF and forwards exact ETag and JSON',async()=>{
  const old=globalThis.fetch;const calls=[];
  globalThis.fetch=async(url,options)=>{calls.push({url,options});return Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic-csrf'}:{version:2});};
  try{await portfolioRequest('/synthetic','PATCH',{name:'Synthetic'},'"portfolio:synthetic:1"');assert.equal(calls.length,2);assert.equal(calls[1].options.headers['If-Match'],'"portfolio:synthetic:1"');assert.equal(calls[1].options.headers['X-CSRFToken'],'synthetic-csrf');assert.deepEqual(JSON.parse(calls[1].options.body),{name:'Synthetic'});}finally{globalThis.fetch=old;}
});
test('confirmed deletion accepts empty 204 response without JSON parsing',async()=>{
  const old=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{if(url.endsWith('/csrf'))return Response.json({csrf_token:'synthetic'});assert.equal(options.method,'DELETE');assert.deepEqual(JSON.parse(options.body),{confirm:true});return new Response(null,{status:204});};
  try{assert.equal(await portfolioRequest('/synthetic','DELETE',{confirm:true},'"tag"'),undefined);}finally{globalThis.fetch=old;}
});
test('slug and version conflicts retain field validation and status',async()=>{
  const old=globalThis.fetch;
  globalThis.fetch=async()=>Response.json({error:{message:'Conflit.',fields:{slug:['Déjà utilisé.']}}},{status:409});
  try{await assert.rejects(portfolioRequest(),e=>e instanceof PortfolioError&&e.status===409&&e.fields.slug[0]==='Déjà utilisé.');}finally{globalThis.fetch=old;}
});
test('non-JSON network failures expose a generic message',async()=>{
  const old=globalThis.fetch;globalThis.fetch=async()=>new Response('PRIVATE_PROXY_DETAIL',{status:502});
  try{await assert.rejects(portfolioRequest(),e=>e instanceof PortfolioError&&!e.message.includes('PRIVATE_PROXY_DETAIL'));}finally{globalThis.fetch=old;}
});
