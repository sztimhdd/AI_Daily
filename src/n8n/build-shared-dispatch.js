// Phase3 decision -> bounded next step. No model, research or writing execution.
const rows=$input.all();
const fail=m=>{throw new Error('Shared dispatch: '+m);};
const obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const equal=(a,b)=>JSON.stringify(a,sort)===JSON.stringify(b,sort);
function sort(k,v){return obj(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v;}
if(rows.length!==1)fail('expected one approval context');
const x=rows[0].json.body??rows[0].json;
const ctx=x.editor_input,d=x.decision,b=x.approval_bundle;
if(x.schema!=='story_approval_context.v1'||!obj(ctx)||!obj(d)||!obj(b))fail('approval envelope missing');
if(d.schema!=='story_decision.v1'||b.schema!=='story_approval.v1'||!x.content_id||[ctx,d,b].some(v=>v.content_id!==x.content_id))fail('identity mismatch');
const parent=x.parent_context;
if(!obj(parent)||!equal(parent.editor_input??parent,ctx))fail('parent material snapshot mismatch');
const budget=ctx.research_task_budget;
if(!Number.isInteger(budget)||budget<1||budget>3||d.research_task_budget!==budget)fail('budget mismatch');
for(const k of ['title_override','editor_note','additional_research_instructions'])if(typeof d[k]!=='string')fail('invalid human field '+k);
if(!obj(ctx.materials)||!['sources','claims','quotations'].every(k=>Array.isArray(ctx.materials[k])))fail('material snapshot missing');
const out={schema:'story_dispatch.v1',content_id:x.content_id,next_action:'hold',selection_status:d.status,
 story_id:null,story_mode:null,title:'',title_override:d.title_override,editor_note:d.editor_note,
 additional_research_instructions:d.additional_research_instructions,research_task_budget:budget,
 approved_candidate:null,research_requests:[],optional_research_requests:[],
 editor_input:ctx,parent_context:{...parent,approval_bundle:b,decision:d}};
if(d.status==='returned'||d.status==='awaiting_selection'){
 if(d.next_action!=='hold'||d.needs_targeted_research!==false||d.selected_candidate!==null)fail('hold decision carries execution intent');
 return [{json:out,pairedItem:{item:0}}];
}
if(d.status!=='selected'||![1,2].includes(d.selected_story))fail('invalid selection status');
const chosen=b.choices?.find(c=>c.selection_value===d.selected_story);
const c=chosen?.candidate;
if(!c||!equal(c,d.selected_candidate))fail('selected candidate differs from approved bundle');
if(c.content_id!==x.content_id||c.story_id!==d.story_id||c.story_mode!==d.story_mode||c.story_id!==(d.selected_story===1?'story_1':'story_2')||c.story_mode!==(d.selected_story===1?'news':'deep_analysis'))fail('selected identity mismatch');
if(!['ready','needs_research'].includes(c.status)||!obj(c.proposal)||!Array.isArray(c.research_requests))fail('candidate is not selectable');
const required=c.research_requests.filter(r=>r.required_for_story===true);
const optional=c.research_requests.filter(r=>r.required_for_story===false);
if(required.length+optional.length!==c.research_requests.length||c.research_requests.length>budget)fail('invalid research requests');
if((c.status==='ready'&&required.length)||(c.status==='needs_research'&&!required.length))fail('candidate readiness conflict');
const need=c.status==='needs_research'||d.additional_research_instructions.trim().length>0;
const action=need?'targeted_research':'prepare_writing';
if(d.next_action!==action||d.needs_targeted_research!==need)fail('decision action conflicts with selected story');
const title=d.title_override.trim()||c.proposal.working_title;
if(d.title!==title)fail('title override mismatch');
return [{json:{...out,next_action:action,story_id:c.story_id,story_mode:c.story_mode,title,
 approved_candidate:c,research_requests:required,optional_research_requests:optional},pairedItem:{item:0}}];