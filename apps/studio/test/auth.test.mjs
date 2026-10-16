import {test} from 'node:test';
import assert from 'node:assert/strict';
import {authRequest,ApiError} from '../src/lib/auth.ts';

test('POST initializes CSRF first and uses same-origin cookies without caching',async()=>{
  const calls=[];
  const original=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{calls.push({url,options});return Response.json(url.endsWith('/csrf')?{csrf_token:'synthetic-csrf'}:{message:'ok'});};
  try {
    assert.deepEqual(await authRequest('logout',{}),{message:'ok'});
    assert.equal(calls.length,2);
    assert.equal(calls[0].url,'/api/v1/auth/csrf');
    assert.equal(calls[1].options.headers['X-CSRFToken'],'synthetic-csrf');
    assert.equal(calls[1].options.method,'POST');
    assert.equal(calls[1].options.credentials,'same-origin');
    assert.equal(calls[1].options.cache,'no-store');
  }finally{globalThis.fetch=original;}
});
test('private identity request performs no mutation',async()=>{
  const original=globalThis.fetch;let count=0;
  globalThis.fetch=async(url,options)=>{count++;assert.equal(url,'/api/v1/auth/me');assert.equal(options.method,'GET');assert.equal(options.body,undefined);return Response.json({});};
  try{await authRequest('me');assert.equal(count,1);}finally{globalThis.fetch=original;}
});
test('API errors preserve accessible field validation and session status',async()=>{
  const original=globalThis.fetch;
  globalThis.fetch=async()=>Response.json({error:{message:'Connectez-vous.',fields:{email:['Invalide']}}},{status:401});
  try{await assert.rejects(authRequest('me'),error=>error instanceof ApiError&&error.status===401&&error.fields.email[0]==='Invalide');}finally{globalThis.fetch=original;}
});
test('non-JSON server failures do not expose raw response bodies',async()=>{
  const original=globalThis.fetch;
  globalThis.fetch=async()=>new Response('PRIVATE_BACKEND_DETAIL',{status:502});
  try{await assert.rejects(authRequest('me'),error=>!error.message.includes('PRIVATE_BACKEND_DETAIL')&&error.message.includes('indisponible'));}finally{globalThis.fetch=original;}
});
