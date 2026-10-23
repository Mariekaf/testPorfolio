/** MEDIA-only bounded transport. All authentication/CSRF/quota checks remain in Django. */
export const runtime='nodejs';
export const dynamic='force-dynamic';
const LIMIT=4*8*1024*1024+65536;
function target(request:Request){
 const url=new URL(process.env.SAAS_API_ORIGIN||'http://127.0.0.1:8001');
 if(url.protocol!=='http:'||!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||url.pathname!=='/'||url.username||url.password||url.search||url.hash)throw new Error('Invalid local API origin');
 return url.origin+'/api/v1/media/assets'+new URL(request.url).search;
}
function failure(code:string,message:string,status:number){return Response.json({error:{code,message}},{status,headers:{'Cache-Control':'private, no-store','Vary':'Cookie','X-Content-Type-Options':'nosniff'}});}
async function forward(request:Request){
 try{
  let body:Uint8Array<ArrayBuffer>|undefined;
  if(request.method==='POST'){
   const length=request.headers.get('content-length');
   if(length&&(!/^\d+$/.test(length)||Number(length)>LIMIT))return failure('payload_too_large','Import limité à 4 images de 8 Mio.',413);
   const reader=request.body?.getReader(),chunks:Uint8Array[]=[],limit=LIMIT;
   let size=0;
   if(reader)while(true){const part=await reader.read();if(part.done)break;size+=part.value.length;if(size>limit){await reader.cancel();return failure('payload_too_large','Import limité à 4 images de 8 Mio.',413);}chunks.push(part.value);}
   body=new Uint8Array(size);let offset=0;for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.length;}
  }
  const headers=new Headers();
  for(const name of ['cookie','x-csrftoken','content-type','origin','referer']){const value=request.headers.get(name);if(value)headers.set(name,value);}
  const upstream=await fetch(target(request),{method:request.method,headers,body,cache:'no-store',redirect:'error',signal:AbortSignal.any([request.signal,AbortSignal.timeout(30000)])});
  const output=new Headers(upstream.headers);output.delete('content-length');output.delete('content-encoding');output.delete('transfer-encoding');
  output.set('Cache-Control','private, no-store');output.set('Vary','Cookie');output.set('X-Content-Type-Options','nosniff');
  return new Response(upstream.body,{status:upstream.status,headers:output});
 }catch{return failure('media_unavailable','Le service d’images est temporairement indisponible. Vos contenus sont conservés.',503);}
}
export const GET=forward;
export const POST=forward;
