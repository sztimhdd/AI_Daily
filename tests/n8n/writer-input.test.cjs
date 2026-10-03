const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {direct,reassessed,clone} = require('./fixtures/handoff.cjs');
const prepareCode = fs.readFileSync(path.join(__dirname,'../../src/n8n/prepare-writing-handoff.js'),'utf8');
const source = fs.readFileSync(process.env.WRITER_INPUT_CODE || path.join(__dirname,'../../src/n8n/writer-context-builder.js'),'utf8');
const invoke = (code,x) => new Function('$input',code)({all:()=>[{json:x}],first:()=>({json:x})})[0].json;
const input = (kind='reassessed',language='zh-CN') => {
 const x=invoke(prepareCode,kind==='direct'?direct():reassessed());
 x.task_config={language,content_type:language==='zh-CN'?'zhihu_longform':'linkedin_longform'};
 return x;
};
const run=x=>invoke(source,x);
const reject=(change,re)=>{const x=input();change(x);assert.throws(()=>run(x),re);};
const allProps=b=>[...b.opening.propositions,...b.movements.flatMap(m=>m.propositions)];

test('prepared News with empty text compiles without a planner or a fabricated thesis',()=>{
 const x=input(),o=run(x);assert.equal(x.writing_input.brief_content,'');
 assert.equal(o.status,'READY');assert.equal(o.ready_for_writer,true);assert.equal(o.schema,'writer_context.v1');
 assert.equal(o.writer_brief.schema,'writer_brief.v3');assert.equal(o.writer_brief.story_mode,'news');
 assert.equal(o.writer_brief.article_intent.thesis,null);assert.equal(o.writer_context.narrative.thesis,null);
});
test('entire received work order and audit history survive byte-for-byte without input mutation',()=>{
 const x=input(),before=JSON.stringify(x),o=run(x);assert.equal(JSON.stringify(x),before);
 assert.equal(JSON.stringify(o.writing_work_order),before);assert.equal(o.writing_work_order.writing_authorized,false);
 assert.equal(o.writing_work_order.research_loop_authorized,false);assert.equal(o.writing_work_order.service_invoked,false);
 const h=o.writing_work_order.writing_input;assert.deepEqual([h.materials.sources.length,h.materials.claims.length,h.materials.quotations.length],[8,10,5]);
 assert.equal(o.writing_work_order.preparation_source.approved_story.research_requests[0].required_for_story,true);
 assert.equal(h.title_override,null);
});
test('title, reader promise and actual human instructions are copied, not inferred',()=>{
 const x=input();x.writing_input.editor_note='  保留这段原话。\n不要自动改口吻。  ';const b=run(x).writer_brief;
 assert.equal(b.title,x.writing_input.title);assert.equal(b.article_intent.reader_change,x.writing_input.approved_story.proposal.reader_promise);
 assert.equal(b.editorial_instructions.human_instructions,x.writing_input.human_instructions);
 assert.equal(b.editorial_instructions.editor_note,x.writing_input.editor_note);
});
test('all story movements and each referenced proposition retain their exact meaning and status',()=>{
 const x=input(),p=x.writing_input.approved_story.proposal,b=run(x).writer_brief;
 assert.deepEqual(b.movements.map(m=>m.job),p.story_path.map(m=>m.job));
 const texts=new Set(allProps(b).map(t=>t.text));for(const c of x.writing_input.materials.claims)assert.ok(texts.has(c.statement));
 const entry=allProps(b).find(t=>t.text===x.writing_input.materials.claims[1].statement);assert.equal(entry.status,'attributed');
});
test('two QT01 namespaces retain different quote texts speakers and source URLs',()=>{
 const x=input(),b=run(x).writer_brief,q=b.quotations;
 assert.equal(q.length,3);for(const original of x.writing_input.selected_quotations){
  const output=q.find(q=>q.text===original.text_original);assert.ok(output);assert.equal(output.speaker,original.speaker);
  assert.equal(output.attribution,original.attribution);assert.equal(output.sources[0].url,original.source_url);
 }
 assert.equal(q.filter(q=>['Patrick Collison','Nick Baumann'].includes(q.speaker)).length,2);
});
test('partial source and quote context limitations are visible to the writer',()=>{
 const x=input(),s=x.writing_input.materials.sources[3];s.source_note='Only two paragraphs fetched.';
 const q=x.writing_input.materials.quotations.find(q=>q.ref==='supplementary:QT01');q.source_context='Release notes, not independent measurement.';q.editorial_use='Do not infer savings.';
 Object.assign(x.writing_input.selected_quotations.find(q=>q.ref==='supplementary:QT01'),q);
 const b=run(x).writer_brief,ss=allProps(b).flatMap(p=>p.sources).find(s=>s.url===x.writing_input.materials.sources[3].url);
 assert.equal(ss.retrieval_status,'partial_body');assert.equal(ss.note,'Only two paragraphs fetched.');
 const qq=b.quotations.find(v=>v.text===q.text_original);assert.equal(qq.source_context,q.source_context);assert.equal(qq.editorial_use,q.editorial_use);
});
test('source evidence excerpts are preserved in the compiled reviewer context',()=>{
 const x=input();x.writing_input.materials.claims[0].support=[{source_id:'S01',locator:'First paragraph',evidence:'agreed to acquire'}];
 const c=run(x).writer_context.evidence.claims[0];assert.equal(c.id,'initial:C01');assert.equal(c.support[0].text,'agreed to acquire');
 assert.equal(c.support[0].source_id,'initial:S01');assert.equal(c.support[0].locator,'First paragraph');
});
test('reader brief does not include provenance test flags or internal evidence IDs',()=>{
 const b=JSON.stringify(run(input()).writer_brief);assert.doesNotMatch(b,/initial:|supplementary:|preparation_source|formal_hitl|writing_authorized|quotation_validation/);
});
test('ineligible discovery sources stay in audit but never become article evidence',()=>{
 const x=input(),o=run(x),bad=x.writing_input.materials.sources.filter(s=>!s.claim_eligible);
 for(const s of bad){assert.ok(o.writing_work_order.writing_input.materials.sources.some(a=>a.ref===s.ref));assert.ok(!JSON.stringify(o.writer_brief).includes(s.url));}
});
for(const kind of ['direct','reassessed'])for(const language of ['zh-CN','en-US'])test(`${kind} preserves explicit ${language} in both consumer contracts`,()=>{
 const x=input(kind,language),o=run(x);assert.equal(o.writer_context.config.language,language);assert.equal(o.writer_brief.language,language);
 assert.equal(o.writer_brief.content_type,x.task_config.content_type);
 if(kind==='direct')assert.equal(Object.hasOwn(o.writing_work_order,'writing_authorized'),false);
});
test('Deep judgment maps exactly and does not become a new editorial opinion',()=>{
 const d=direct();d.story_id=d.approved_candidate.story_id='story_2';d.story_mode=d.approved_candidate.story_mode='deep_analysis';
 d.approved_candidate.proposal.analysis_judgment='Fixture judgment; not verified analysis.';
 const x=invoke(prepareCode,d);x.task_config={language:'zh-CN',content_type:'zhihu_longform'};
 const o=run(x);assert.equal(o.writer_brief.article_intent.thesis,d.approved_candidate.proposal.analysis_judgment);
});
test('configuration can change language without changing platform',()=>{
 const x=input();x.task_config.language='en-US';const b=run(x).writer_brief;assert.equal(b.language,'en-US');assert.equal(b.content_type,'zhihu_longform');
});
const cases=[
 ['unprepared status',x=>x.status='held',/prepared/],
 ['already invoked order',x=>x.service_invoked=true,/prepared/],
 ['wrong handoff identity',x=>x.writing_input.content_id='other',/identity/],
 ['missing language',x=>delete x.task_config.language,/language/],
 ['substring language',x=>x.task_config.language='not-en-US',/language/],
 ['conflicting legacy language',x=>x.creative_blueprint={language:'en-US'},/language/],
 ['conflicting nested language',x=>x.writing_input.language='en-US',/language/],
 ['missing human instructions',x=>delete x.writing_input.human_instructions,/instruction/],
 ['missing source',x=>x.writing_input.materials.sources.shift(),/source/],
 ['ineligible source',x=>x.writing_input.materials.sources[0].claim_eligible=false,/source/],
 ['unknown selected material',x=>x.writing_input.approved_story.proposal.opening.material_refs.push('initial:C999'),/material/],
 ['quote text drift',x=>x.writing_input.selected_quotations[0].text_original='invented',/quotation/],
 ['duplicate namespaced claim',x=>x.writing_input.materials.claims.push(clone(x.writing_input.materials.claims[0])),/duplicate/],
 ['missing reader promise',x=>delete x.writing_input.approved_story.proposal.reader_promise,/proposal/],
 ['Deep without judgment',x=>{x.story_mode=x.writing_input.story_mode=x.writing_input.approved_story.story_mode='deep_analysis';x.story_id=x.writing_input.story_id=x.writing_input.approved_story.story_id='story_2';x.writing_input.approved_story.proposal.analysis_judgment='none';},/judgment/],
 ['escalated historical flag',x=>x.writing_authorized=true,/authorization/],
 ['missing audit provenance',x=>delete x.preparation_source,/provenance/]
];
for(const [name,mutate,pattern] of cases)test(name+' rejects before Writer',()=>reject(mutate,pattern));
test('multiple orders cannot silently lose later stories',()=>{const x=input();assert.throws(()=>new Function('$input',source)({all:()=>[{json:x},{json:clone(x)}]}),/one/);});

test('unresolved questions and conflicts remain visible to the Chinese writer',()=>{
 const x=input();x.writing_input.materials.open_questions=[{question:'Fixture unresolved condition?',why_it_matters:'Do not state it as settled.',blocks:'neither'}];
 x.writing_input.materials.conflicts=[{description:'Fixture sources disagree.'}];
 const b=run(x).writer_brief;assert.deepEqual(b.evidence_boundaries,{open_questions:x.writing_input.materials.open_questions,conflicts:x.writing_input.materials.conflicts});
});
test('a quote-free assignment remains valid without invented quotations',()=>{
 const x=input('direct'),h=x.writing_input,p=h.approved_story.proposal;h.materials.quotations=[];h.selected_quotations=[];p.quotation_refs=[];
 p.opening.material_refs=p.opening.material_refs.filter(r=>!r.includes(':QT'));
 for(const s of p.story_path)s.material_refs=s.material_refs.filter(r=>!r.includes(':QT'));
 assert.deepEqual(run(x).writer_brief.quotations,[]);
});
