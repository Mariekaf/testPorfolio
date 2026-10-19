/** Cross-language test driver: stdin snapshots only, no configuration or database. */
import {readFileSync} from 'node:fs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer} from './hero-rendering-support.mjs';
const documents=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(documents.map(snapshot=>renderToStaticMarkup(React.createElement(Renderer,
  {snapshot,sectionId:'hero',enabled:true,continuationId:'projects'})))));
