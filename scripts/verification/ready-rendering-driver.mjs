/** stdin SSR transport for pure Python integration tests. No application/server. */
import {readFileSync} from 'node:fs';import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';
import {Renderer} from './ready-rendering-support.mjs';
const cases=JSON.parse(readFileSync(0,'utf8'));
const output=cases.map(c=>renderToStaticMarkup(React.createElement(Renderer,{document:c.document,media:c.media,enabled:true,demonstration:true})));
process.stdout.write(JSON.stringify(output));
