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
// The native writer-only replay has a fresh, explicit test envelope. The complete
// historical research receipt stays in execution 557 and the enriched fixture.
function nativeFixture(reference,negative='') {
 const x=fixture(reference,negative);
 x.preparation_source={schema:'controlled_test_fixture.v1',content_id:x.content_id,
  story_id:x.story_id,story_mode:x.story_mode,writing_authorized:false,research_loop_authorized:false,
  source_execution:'557',fixture_source:'tests/n8n/fixtures/writer-news-557.cjs',formal_hitl:false,
  scope:'Writer material replay only; full historical receipts remain in original execution. No historical approval is asserted.'};
 x.writing_input.topic_brief='公告日历史写作材料回放；非当前新闻核验。';
 x.writing_input.quotation_validation={collection_present:true,quotation_count:3,checked_count:3,valid:true,matching:'whitespace_only',errors:[]};
 x.test_context={kind:'isolated_cn_draft_test',formal_hitl:false,model_calls_allowed:true,publication_allowed:false,source_execution:'557'};
 return x;
}
function probe(reference) {
 return '// TEMP writer-only replay. Fresh user permission and unpinned model required.\n'
  +'return [{json:'+JSON.stringify(nativeFixture(reference))+'}];\n';
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
// Fixture-specific observed regressions from real run 592; not a general fact checker.
function assertKnownRegressions(article,order) {
 const stats=assertDraft(article,order);
 const prose=article.replace(/https?:\/\/[^\s)]+/g,'');
 for(const pattern of [/8\s*月\s*16\s*日/,/70\s*亿/,/两个月后/,/^##\s*路由不是选模型/m,/我们只读到/])
  assert.ok(!pattern.test(prose),'observed metadata/scope/time regression: '+pattern);
 const quotes=order.writing_input.selected_quotations.map(q=>q.text_original.replace(/\s+/g,' ').trim());
 const blocks=[...article.matchAll(/^>\s*(.+)$/gm)].map(m=>m[1].replace(/\s+/g,' ').trim());
 for(const q of blocks)assert.ok(quotes.some(original=>original.includes(q)),'direct quote differs from selected quotation text');
 return {...stats,direct_quote_blocks:blocks.length};
}
module.exports={fixture,nativeFixture,probe,assertDraft,assertKnownRegressions};

const reference='fixture-only: not reusable execution permission';
if(process.argv[2]==='--probe')console.log(probe(process.argv[3]));
else if(process.argv[2]==='--native-payload')console.log(JSON.stringify(nativeFixture(process.argv[3],process.argv[4]),null,2));
else if(process.argv[2]==='--payload')console.log(JSON.stringify(fixture(process.argv[3],process.argv[4]),null,2));
else if(process.argv[2]==='--regressions')console.log(JSON.stringify(assertKnownRegressions(fs.readFileSync(process.argv[3],'utf8'),fixture(reference)),null,2));
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
 assert.equal(JSON.stringify(native),JSON.stringify(nativeFixture(reference)),'native probe differs from saved fixture');
 assert.equal(JSON.stringify(runNode('writer-context-builder.js',native).writer_brief),JSON.stringify(y.writer_brief),'test envelope changed Writer material');
 for(const [negative,error]of [['missing-decision',/explicit invocation decision missing/],['wrong-language',/target language mismatch/],['missing-source',/missing\/ineligible material source/]])
  assert.throws(()=>runNode('writer-invocation-gate.js',runNode('writer-context-builder.js',fixture(reference,negative))),error);
 assert.throws(()=>fixture(reference,'unfinished-research'),/unfinished current research/);
 assert.throws(()=>assertDraft('',x),/complete article/);
});
