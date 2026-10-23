/** Standalone static preview exporter. No auth, API, database or application routes. */
import {mkdirSync,readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import {resolve,join,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer,demonstrations} from './ready-rendering-support.mjs';
import {loadReadyRegistry} from '../../packages/content-contracts/src/ready-registry.ts';
const target=process.argv[2];if(!target)throw new Error('Pass a NEW output directory outside the repository.');
const directory=resolve(target),repository=resolve(fileURLToPath(new URL('../../',import.meta.url)));
if(directory===repository||directory.startsWith(repository+sep))throw new Error('Export outside the repository only.');
mkdirSync(directory,{recursive:false});mkdirSync(join(directory,'__ready_assets'));
const assets=new URL('../../contracts/fixtures/ready-rendering/assets/',import.meta.url);
const manifest=JSON.parse(readFileSync(new URL('index.v1.json',assets),'utf8'));
for(const source of manifest.sources){
 if(!/^[a-z0-9-]+\.svg$/.test(source.file))throw new Error('Invalid synthetic asset.');
 const raw=readFileSync(new URL(source.file,assets));
 if(raw.length!==source.bytes||createHash('sha256').update(raw).digest('hex')!==source.sha256)throw new Error('Synthetic asset checksum mismatch.');
 copyFileSync(new URL(source.file,assets),join(directory,'__ready_assets',source.file));
}
const css=readFileSync(new URL('../../apps/studio/src/components/templates/creative-editorial-renderer.module.css',import.meta.url),'utf8');
const variant=structuredClone(demonstrations.cases[0]);variant.id='paper-serif';variant.document.customization.style_overrides={palette_id:'paper-cobalt',font_ref:{id:'system-serif',version:'1.0.0'}};
const cases=[...demonstrations.cases,variant,{id:'empty-draft',document:loadReadyRegistry().get().bundle.snapshot}];
for(const c of cases){
 const html=renderToStaticMarkup(React.createElement(Renderer,{document:c.document,media:c.media,enabled:true,scope:'preview',demonstration:c.id!=='empty-draft'}));
 writeFileSync(join(directory,c.id+'.html'),`<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Creative Editorial — ${c.id}</title><style>body{margin:0}${css}</style></head><body>${html}</body></html>`,{encoding:'utf8',flag:'wx'});
}
writeFileSync(join(directory,'index.html'),`<!doctype html><html lang="fr"><meta charset="utf-8"><title>Prévisualisation synthétique isolée</title><h1>Creative Editorial — démonstration synthétique</h1><p>Aucun compte, stockage ou site public.</p><ul>${cases.map(c=>`<li><a href="${c.id}.html">${c.id}</a></li>`).join('')}</ul></html>`,{encoding:'utf8',flag:'wx'});
console.log('Four isolated previews exported with verified original synthetic assets; no API/database accessed.');
