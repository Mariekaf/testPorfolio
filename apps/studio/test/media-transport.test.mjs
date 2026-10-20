import {test} from 'node:test';
import assert from 'node:assert/strict';
const {GET,POST}=await import('../src/app/api/v1/media/assets/route.ts');
test('bounded media transport preserves exact multipart bytes CSRF origin and cookies',async()=>{
 const original=fetch;let sent;globalThis.fetch=async(url,options)=>{sent=[url,options];return Response.json({results:[]},{status:201});};
 try{const request=new Request('http://127.0.0.1:3000/api/v1/media/assets',{method:'POST',headers:{Cookie:'portfolio_saas_session=synthetic','X-CSRFToken':'synthetic','Content-Type':'multipart/form-data; boundary=synthetic',Origin:'http://127.0.0.1:3000'},body:'synthetic multipart bytes'});const response=await POST(request);assert.equal(response.status,201);assert.equal(sent[1].headers.get('cookie'),'portfolio_saas_session=synthetic');assert.equal(sent[1].headers.get('x-csrftoken'),'synthetic');assert.equal(sent[1].headers.get('origin'),'http://127.0.0.1:3000');assert.equal(sent[1].headers.get('content-type'),'multipart/form-data; boundary=synthetic');assert.equal(new TextDecoder().decode(sent[1].body),'synthetic multipart bytes');assert.match(response.headers.get('cache-control'),/private.*no-store/);}finally{globalThis.fetch=original;}
});
test('media transport rejects oversized declaration without forwarding or changing other API routes',async()=>{
 const original=fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw new Error('must not forward');};
 try{const result=await POST(new Request('http://127.0.0.1:3000/api/v1/media/assets',{method:'POST',headers:{'Content-Length':String(4*8*1024*1024+65537)}}));assert.equal(result.status,413);assert.equal(calls,0);}finally{globalThis.fetch=original;}
});
test('listing transports query and upstream auth refusal verbatim',async()=>{
 const original=fetch;globalThis.fetch=async(url)=>{assert.match(url,/\/api\/v1\/media\/assets\?page=2$/);return Response.json({error:{code:'authentication_required',message:'Connexion requise.'}},{status:401});};
 try{const result=await GET(new Request('http://127.0.0.1:3000/api/v1/media/assets?page=2'));assert.equal(result.status,401);assert.equal((await result.json()).error.code,'authentication_required');}finally{globalThis.fetch=original;}
});
