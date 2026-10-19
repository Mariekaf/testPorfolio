/** Offline parity transport, invoked by Python tests. Outputs synthetic fixtures only. */
import {createHeroResolver} from '../src/hero-resolution.ts';
import {readContracts, readResolutionFixtures, prepare} from './hero-resolution-support.ts';
const fixture=readResolutionFixtures(), resolver=createHeroResolver(readContracts());
const results=fixture.cases.map((c:any)=>{
  const input=prepare(fixture.base_design,c.changes);
  try {
    const resetDocument=c.reset ? resolver.reset(input,c.reset.section_id,c.reset.path) : undefined;
    return {id:c.id,result:resolver.resolve(resetDocument ?? input),...(c.reset ? {reset_document:resetDocument} : {})};
  } catch { return {id:c.id,error:true}; }
});
process.stdout.write(JSON.stringify(results));
