import {loadReadyRegistry} from '../../../../../packages/content-contracts/src/ready-registry.ts';
import type {FixtureMediaContext} from '../../../../../packages/content-contracts/src/ready-fixture-media.ts';
import CreativeEditorialView from './creative-editorial-view.tsx';
let validator:ReturnType<ReturnType<typeof loadReadyRegistry>['validator']>|undefined;
export default function CreativeEditorialRenderer(props:{document:unknown;media?:FixtureMediaContext;enabled?:boolean;scope?:string;demonstration?:boolean}){
 if(props.enabled!==true)throw new Error('Creative Editorial rendering is disabled.');
 const effective=(validator??=loadReadyRegistry().validator()).validate(props.document);
 return <CreativeEditorialView {...props} effective={effective}/>;
}
