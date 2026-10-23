/** Pure stdin/stdout parity protocol, no settings, SQL or renderer activation. */
import {readFileSync} from 'node:fs';
import {textHeroResolver} from '../../packages/content-contracts/src/hero-runtime.ts';
const cases=JSON.parse(readFileSync(0,'utf8'));
const results=cases.map(c=>{
 try{
  const document=c.reset?textHeroResolver.reset(c.document,'hero',c.reset):c.document;
  return {result:textHeroResolver.resolve(document),...(c.reset?{reset_document:document}:{})};
 }catch{return {error:true};}
});
process.stdout.write(JSON.stringify(results));
