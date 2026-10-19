/** Test-only TSX/CSS loader. Uses the real component and CSS, no application route. */
import {registerHooks} from 'node:module';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
registerHooks({load(url,context,next){
  if(url.endsWith('.json') && !url.includes('/node_modules/'))return {format:'module',shortCircuit:true,source:'export default '+JSON.stringify(JSON.parse(readFileSync(new URL(url),'utf8')))+';'};
  if(url.endsWith('.module.css'))return {format:'module',shortCircuit:true,source:'export default new Proxy({}, {get:(_,key)=>String(key)});'};
  if(url.endsWith('.tsx'))return {format:'module',shortCircuit:true,source:ts.transpileModule(readFileSync(new URL(url),'utf8'),{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.ESNext}}).outputText};
  return next(url,context);
}});
export const {default:Renderer}=await import('../../apps/studio/src/components/templates/modular-hero-renderer.tsx');
export const fixtures=JSON.parse(readFileSync(new URL('../../contracts/fixtures/hero/rendering.v1.json',import.meta.url),'utf8'));
