import {test} from 'node:test';
import assert from 'node:assert/strict';
import {editorPath,readPanel,sameEditor,templateName} from '../src/lib/portfolio-navigation.ts';
const base={id:'11111111-1111-4111-8111-111111111111',name:'Synthetic',management_state:'active',source_template_version:'1.0.0'};
test('three known template families have distinct contextual editor destinations',()=>{
 for(const [source,suffix] of [['minimal','edit'],['editorial','edit'],['creative-editorial','ready']])assert.equal(editorPath({...base,source_template_id:source}),`/portfolios/${base.id}/${suffix}`);
});
test('blank unknown versions templates and unsafe identifiers cannot manufacture editor links',()=>{
 for(const change of [{source_template_id:null},{source_template_id:'unknown'},{source_template_version:'9.0.0'},{id:'../media'},{id:'javascript:alert(1)'}])assert.equal(editorPath({...base,source_template_id:'minimal',...change}),null);
});
test('panel query is closed, duplicate ambiguous values cannot select a panel',()=>{
 for(const panel of ['projects','sections','appearance'])assert.equal(readPanel(`?panel=${panel}`),panel);
 for(const query of ['','?panel=publish','?panel=projects&panel=appearance','?panel=<script>','?panel='])assert.equal(readPanel(query),null);
});
test('panel history stays in the editor while context and origin changes are exits',()=>{
 const start='http://127.0.0.1:3011/portfolios/'+base.id+'/edit?panel=projects';
 assert.ok(sameEditor(start,start.replace('projects','appearance')));
 assert.ok(sameEditor(start,start+'#preview'));
 for(const target of [start.replace('/edit','/settings'),start.replace(base.id,'22222222-2222-4222-8222-222222222222'),start.replace(':3011',':3012'),start.replace('/edit','/ready')])assert.equal(sameEditor(start,target),false);
});
test('archive does not turn read-only access into a different template or a public link',()=>{
 assert.equal(editorPath({...base,source_template_id:'minimal',management_state:'archived'}),`/portfolios/${base.id}/edit`);
});

test('unknown templates are never labelled Editorial by default',()=>{assert.equal(templateName('unregistered'),'Template non pris en charge');assert.equal(templateName(null),'Sans template');});
