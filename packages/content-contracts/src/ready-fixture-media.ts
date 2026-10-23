/** E0703 controlled synthetic media ONLY. Not an upload/storage implementation. */
import manifest from '../../../contracts/fixtures/ready-rendering/assets/index.v1.json' with {type:'json'};
export type MediaReference={asset_id:string;alt:string;decorative:boolean;focal_point:{x:number;y:number}};
export type FixtureMediaContext={accountId:string;assets:Record<string,{accountId:string;state:string;rightsConfirmed:boolean;sourceId:string}>};
export type FixtureMediaResult={state:'available'|'missing'|'processing'|'rejected'|'unauthorized'|'invalid';src?:string;width?:number;height?:number};
export function resolveFixtureMedia(reference:MediaReference|null,context?:FixtureMediaContext):FixtureMediaResult{
 if(!reference||!reference.alt.replace(/[\s\u0085\uFEFF]/g,''))return {state:'missing'};
 const item=context?.assets&&Object.hasOwn(context.assets,reference.asset_id)?context.assets[reference.asset_id]:undefined;
 if(!item)return {state:'missing'};
 if(!context?.accountId||item.accountId!==context.accountId||item.rightsConfirmed!==true)return {state:'unauthorized'};
 if(item.state==='processing')return {state:'processing'};
 if(item.state==='rejected')return {state:'rejected'};
 if(item.state!=='ready')return {state:'invalid'};
 const source=manifest.sources.find(s=>s.id===item.sourceId);
 if(!source||! /^[a-z0-9-]+\.svg$/.test(source.file))return {state:'invalid'};
 return {state:'available',src:'/__ready_assets/'+source.file,width:source.width,height:source.height};
}
