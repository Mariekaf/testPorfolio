'use client';
import {useMemo} from 'react';
import CreativeEditorialView from './creative-editorial-view';
import {readyValidator} from './ready-browser-contracts';
export default function ReadyPreview({document,scope='private-preview',demonstration=false}:{document:unknown;scope?:string;demonstration?:boolean}){
 const result=useMemo(()=>{try{return {effective:readyValidator.validate(document)};}catch{return {error:true};}},[document]);
 if(!result.effective)return <p role="alert">Aperçu indisponible : vérifiez les champs, les liens vers des sections visibles et les contrastes. Vos saisies sont conservées.</p>;
 // No fixture context: user references never become trusted local demonstration assets.
 return <CreativeEditorialView document={document} effective={result.effective} scope={scope} enabled embedded demonstration={demonstration}/>;
}
