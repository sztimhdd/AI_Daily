// T04: replay the complete writing-facing materials, not the two-source route fixture.
// CLI generates inputs/probe code only. It never makes network calls.
// Replay requires fresh user approval, verified isolation, and manual execution.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {fixture: historyFixture} = require('./fixtures/writer-news-557.cjs');
const root = path.join(__dirname, '../..');
const source = file => fs.readFileSync(path.join(root, file), 'utf8');
function runNode(file, json) {
 return vm.runInNewContext(`(function(){${source('src/n8n/'+file)}\n})()`,
  {$input:{all:()=>[{json}], first:()=>({json})}}, {filename:file, timeout:1000})[0].json;
}
function configure(order, reference) {
 assert.ok(typeof reference==='string' && reference.trim(), 'fresh authorization reference required');
 order.task_config={language:'zh-CN',content_type:'zhihu_longform'};
 order.writer_invocation_decision={schema:'writer_invocation_decision.v1',status:'authorized',
  authorization_kind:'controlled_test',scope:'writer_draft',content_id:order.content_id,
  story_id:order.story_id,story_mode:order.story_mode,title:order.writing_input.title,
  reader_promise:order.writing_input.approved_story.proposal.reader_promise,
  target_language:'zh-CN',decision_source:{type:'user_chat_authorization',reference},side_effects_isolated:true};
 order.test_context={kind:'isolated_cn_draft_test',formal_hitl:false,model_calls_allowed:true,
  publication_allowed:false,source_execution:'557',fixture_source:'tests/n8n/fixtures/writer-news-557.cjs'};
 return order;
}
function fixture(reference, negative='') {
 const h=historyFixture();
 if(negative==='unfinished-research')h.candidate.research_requests=[{question:'Unresolved required test question',required_for_story:true}];
 const order=configure(runNode('prepare-writing-handoff.js',h),reference);
 if(negative==='missing-decision')delete order.writer_invocation_decision;
 if(negative==='wrong-language')order.writer_invocation_decision.target_language='en-US';
 if(negative==='missing-source')order.writing_input.materials.sources=order.writing_input.materials.sources.filter(s=>s.ref!=='supplementary:S01');
 return order;
}
function probe(reference) {
 assert.ok(typeof reference==='string'&&reference.trim());
 const base=source('tests/n8n/fixtures/handoff.cjs').replace('module.exports={reassessed,direct,clone};','return {reassessed,direct,clone};');
 const material=source('tests/n8n/fixtures/writer-news-557.cjs')
  .replace("const {reassessed, clone} = require('./handoff.cjs');",'const {reassessed, clone} = history;')
  .replace('module.exports={fixture};','return fixture();');
 return '// TEMP T04: approved isolated manual replay. Delete after this test. No network IO here.\n'
  +`const history=(()=>{${base}\n})();\nconst material=(()=>{${material}\n})();\n`
  +`const prepared=(($input)=>{${source('src/n8n/prepare-writing-handoff.js')}\n})({all:()=>[{json:material}]})[0].json;\n`
  +`const assert={ok:(condition,message)=>{if(!condition)throw new Error(message);}};\n`
  +`return [{json:(${configure.toString()})(prepared,${JSON.stringify(reference)})}];\n`;
}
function assertDraft(article, order) {
 assert.ok(typeof article==='string'&&article.trim().length>=500,'complete article text missing');
 assert.equal((article.match(/^#\s+\S.+$/gm)||[]).length,1,'exactly one H1 required');
 assert.ok(/[\u4e00-\u9fff]/.test(article),'Chinese text missing');
 assert.ok(!/\b(?:initial|supplementary):(?:C|QT|S)\d+\b|writer_brief\.v3|writer_context\.v1|writer_invocation_decision/.test(article),'internal metadata leak');
 const allowed=new Set(order.writing_input.materials.sources.filter(s=>s.claim_eligible).map(s=>s.url));
 const urls=[...article.matchAll(/\]\((https?:\/\/[^\s)]+)\)/g)].map(m=>m[1]);
 assert.ok(urls.length>0,'no source links');
 for(const url of urls)assert.ok(allowed.has(url),'unsupported URL: '+url);
 return {characters:article.length,source_link_count:urls.length,unique_source_links:new Set(urls).size};
}
module.exports={fixture,probe,assertDraft};
const reference='fixture-only: not reusable execution permission';
if(process.argv[2]==='--probe')console.log(probe(process.argv[3]));
else if(process.argv[2]==='--payload')console.log(JSON.stringify(fixture(process.argv[3],process.argv[4]),null,2));
else if(process.argv[2]==='--article')console.log(JSON.stringify(assertDraft(fs.readFileSync(process.argv[3],'utf8'),fixture(reference)),null,2));
else require('node:test').test('full writing fixture uses real preparation/mapper/gate and preserves all material boundaries',()=>{
 const x=fixture(reference),before=JSON.stringify(x);
 const y=runNode('writer-invocation-gate.js',runNode('writer-context-builder.js',x));
 assert.equal(JSON.stringify(x),before,'original order mutated');
 const m=x.writing_input.materials;
 assert.deepEqual([m.sources.length,m.claims.length,m.quotations.length],[8,10,5]);
 assert.equal(m.sources.filter(s=>!s.claim_eligible).length,2);
 assert.equal(m.claims.reduce((n,c)=>n+c.support.length,0),23);
 assert.equal(x.writing_input.selected_quotations.length,3);
 assert.equal(y.writer_brief.movements.length,6);
 assert.equal(y.writer_brief.evidence_boundaries.open_questions.length,1);
 assert.equal(y.writer_brief.article_intent.thesis,null);
 assert.equal(y.writer_invocation_receipt.historical_writing_authorized,false);
 assert.ok(!JSON.stringify(y.writer_brief).includes('formal_hitl'));
 assert.ok(y.writer_brief.movements[1].job.includes('区分选择模型'));
 const native=vm.runInNewContext(`(function(){${probe(reference)}\n})()`,{}, {timeout:2000})[0].json;
 assert.equal(JSON.stringify(native),JSON.stringify(x),'native probe differs from saved fixture');
 for(const [negative,error]of [['missing-decision',/explicit invocation decision missing/],['wrong-language',/target language mismatch/],['missing-source',/missing\/ineligible material source/]])
  assert.throws(()=>runNode('writer-invocation-gate.js',runNode('writer-context-builder.js',fixture(reference,negative))),error);
 assert.throws(()=>fixture(reference,'unfinished-research'),/unfinished current research/);
 assert.throws(()=>assertDraft('',x),/complete article/);
});
