import {readFileSync} from 'node:fs';
export const readyFixtures=JSON.parse(readFileSync(new URL('../../../contracts/fixtures/ready/validation.v1.json',import.meta.url),'utf8'));
export function readyPrepare(base:any,changes:any[]){
 const result=structuredClone(base);
 for(const change of changes){const keys=change.path.slice(1).split('/');let node=result;for(const key of keys.slice(0,-1)){if(node[key]===undefined)node[key]={};node=node[key];}node[keys.at(-1)!]=structuredClone(change.value);}
 return result;
}
