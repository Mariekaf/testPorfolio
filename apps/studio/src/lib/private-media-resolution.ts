export type PrivateMedia=Record<string,{state:string;asset_id?:string;src?:string;width?:number;height?:number}>;
/** Closed URL projection: backend still checks session and account on every binary request. */
export function privateImage(identity:string,assets?:PrivateMedia){
 const value=assets&&Object.hasOwn(assets,identity)?assets[identity]:undefined;
 if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(identity)||!value||value.state!=='ready'||value.asset_id!==identity||value.src!==`/api/v1/media/assets/${identity}/file`||!Number.isInteger(value.width)||!Number.isInteger(value.height)||value.width!<1||value.height!<1||value.width!>2560||value.height!>2560)return {state:'missing'};
 return {state:'available',src:value.src,width:value.width,height:value.height};
}
