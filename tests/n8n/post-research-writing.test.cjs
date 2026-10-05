const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {reassessed,direct,clone}=require('./fixtures/handoff.cjs');
const source=name=>fs.readFileSync(path.join(__dirname,'../../src/n8n/',name),'utf8');
const run=(name,x)=>new Function('$input','$execution',source(name))({all:()=>[{json:x}]},{id:'synthetic-test'});
// Synthetic selected receipts exercise shape only: never present these as actual HITL.
function approved(post){
 const x=post?reassessed():direct();
 const parent=post?x.research_increment_receipt.research_work_order.parent_context:x.parent_context;
 const candidate=post?{...clone(x.candidate),status:'needs_research',proposal:clone(x.approved_story.proposal),research_requests:clone(x.approved_story.research_requests)}:clone(x.approved_candidate);
 parent.approval_bundle={schema:'story_approval.v1',content_id:x.content_id,choices:[{selection_value:1,candidate}]};
 parent.decision={schema:'story_decision.v1',content_id:x.content_id,status:'selected',story_id:'story_1',story_mode:'news',title:post?x.approved_story.title:x.title,selected_candidate:candidate,next_action:post?'targeted_research':'prepare_writing'};
 return x;
}
test('direct and post-research share invocation; keep history and selected materials',()=>{
 for(const post of [false,true]){
  const x=approved(post),before=clone(x);
  const w=run('prepare-writing-handoff.js',post?{body:x}:x)[0].json;
  const o=run('prepare-writer-invocation.js',w)[0].json;
  assert.equal(o.writer_invocation_decision.status,'authorized');
  assert.equal(o.writer_invocation_decision.target_language,'zh-CN');
  assert.deepEqual(o.writing_input.materials,x.editor_input.materials);
  assert.deepEqual(o.preparation_source,before);
  assert.deepEqual(x,before);
  if(post){
   assert.equal(o.writing_authorized,false);
   assert.equal(o.research_loop_authorized,false);
   assert.equal(o.preparation_source.research_increment_receipt.research_work_order.parent_context.decision.next_action,'targeted_research');
   assert.deepEqual(o.writing_input.selected_quotations.map(q=>q.ref).sort(),['initial:QT01','initial:QT02','supplementary:QT01']);
  }
 }
});
test('post-research retains stop conditions and cannot borrow direct approval',()=>{
 for(const change of [
  x=>{x.research_increment_receipt.research_work_order.parent_context.decision.next_action='prepare_writing';},
  x=>{delete x.research_increment_receipt.research_work_order.parent_context.approval_bundle;},
  x=>{x.research_increment_receipt.research_work_order.parent_context.decision.title='different';}
 ]){
  const x=approved(true);change(x);
  const w=run('prepare-writing-handoff.js',x)[0].json;
  assert.throws(()=>run('prepare-writer-invocation.js',w),/provenance|drift/);
 }
 for(const change of [x=>{x.story_mode='deep_analysis';x.story_id='story_2';},x=>{x.status='needs_editor_decision';},x=>{x.writing_authorized=true;}]){
  const x=approved(true);change(x);assert.throws(()=>run('prepare-writing-handoff.js',x),/Deep|ready|authorization/);
 }
 assert.deepEqual(run('prepare-writer-invocation.js',{next_action:'hold'}),[]);
});
test('one existing hold terminal returns non-ready News and still holds Deep',()=>{
 for(const status of ['needs_editor_decision','unavailable']){
  const x={...approved(true),status,next_action:'editor_review'},before=clone(x);
  assert.deepEqual(run('finalize-reassessment-hold.js',x)[0].json,before);
 }
 const deep={schema:'selected_story_reassessment.v1',content_id:'fixture',status:'prepared',story_id:'story_2',story_mode:'deep_analysis'};
 assert.equal(run('finalize-reassessment-hold.js',deep)[0].json.next_action,'editor_review');
 assert.throws(()=>run('finalize-reassessment-hold.js',approved(true)),/schema|state/);
});
