// Direct-ready or completed News research -> the same V2 Writer call contract.
const rows=$input.all();
const fail=m=>{throw new Error('Writer invocation prep: '+m);};
const obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const text=v=>typeof v==='string'&&v.trim().length>0;
if(rows.length!==1)fail('expected one work order');
const w=rows[0].json;

// False output of Research Needed? also carries hold states. Preserve the old behavior: stop quietly.
if(w?.next_action!=='prepare_writing') return [];

if(w.schema!=='writing_work_order.v1'||w.status!=='prepared'||w.service_invoked!==false
   ||!text(w.content_id)||!['news','deep_analysis'].includes(w.story_mode)
   ||w.story_id!==(w.story_mode==='news'?'story_1':'story_2')) fail('prepared writing work order invalid');

const h=w.writing_input;
if(!obj(h)||h.schema!=='writing_handoff.v1'||h.content_id!==w.content_id
   ||h.story_id!==w.story_id||h.story_mode!==w.story_mode
   ||!text(h.title)||!text(h.approved_story?.proposal?.reader_promise)) fail('writing handoff identity/promise missing');

const p=w.preparation_source;
const reassessment=p?.schema==='selected_story_reassessment_result.v1';
if(reassessment && (w.story_mode!=='news'||p.status!=='ready_for_writer_handoff'
   ||p.next_action!=='prepare_writing_handoff')) fail('News reassessment is not ready');
const provenance=reassessment
 ? p.research_increment_receipt?.research_work_order?.parent_context
 : p?.parent_context;
const bundle=provenance?.approval_bundle;
const d=provenance?.decision;
if(!obj(bundle)||bundle.schema!=='story_approval.v1'||bundle.content_id!==w.content_id
   ||!obj(d)||d.schema!=='story_decision.v1'||d.status!=='selected'
   ||d.content_id!==w.content_id||d.story_id!==w.story_id||d.story_mode!==w.story_mode
   ||d.next_action!==(reassessment?'targeted_research':'prepare_writing')) fail('selected approval provenance missing');
if(d.title!==h.title||d.selected_candidate?.proposal?.reader_promise!==h.approved_story.proposal.reader_promise) fail('approved title/promise drift');

const task_config={language:'zh-CN',content_type:'zhihu_longform'};
const writer_invocation_decision={
  schema:'writer_invocation_decision.v1',
  status:'authorized',
  authorization_kind:'formal_hitl',
  scope:'writer_draft',
  content_id:w.content_id,
  story_id:w.story_id,
  story_mode:w.story_mode,
  title:h.title,
  reader_promise:h.approved_story.proposal.reader_promise,
  target_language:task_config.language,
  decision_source:{
    type:'story_decision_execution',
    reference:'mother_execution:'+$execution.id+':Parse Editor Feedback'
  },
  side_effects_isolated:false
};

return [{json:{...w,task_config,writer_invocation_decision},pairedItem:{item:0}}];
