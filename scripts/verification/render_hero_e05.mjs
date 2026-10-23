/** Generates static verification pages from the exact server renderer, no DB/server. */
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer,fixtures} from './hero-rendering-support.mjs';
const output=process.argv[2];
if(!output)throw new Error('Pass a NEW output directory outside the repository.');
const directory=resolve(output);
// Exclusive creation prevents replacing any existing directory/data.
mkdirSync(directory,{recursive:false});
const css=readFileSync(new URL('../../apps/studio/src/components/templates/modular-hero-renderer.module.css',import.meta.url),'utf8');
for(const c of fixtures.cases){
 const html=renderToStaticMarkup(React.createElement(Renderer,{snapshot:c.design,sectionId:'hero',enabled:true,scope:c.id,continuationId:'projects'}));
 const document=`<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${c.id} — Hero E05</title><style>body{margin:0}#projects{box-sizing:border-box;overflow-wrap:anywhere;padding:2rem;font:1rem system-ui;background:#fff;color:#111}${css}</style></head><body><main>${html}<section id="projects" tabindex="-1" aria-label="Projets fictifs"><h2>Études de cas — démonstration fictive</h2><p>Recherche UX et interfaces accessibles.</p></section></main></body></html>`;
 writeFileSync(join(directory,c.id+'.html'),document,{encoding:'utf8',flag:'wx'});
}
console.log('Four isolated HTML references generated; no application, DB or configuration accessed.');
