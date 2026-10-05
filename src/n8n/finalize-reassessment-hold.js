const rows=$input.all(),fail=m=>{throw new Error('Reassessment hold: '+m);};
if(rows.length!==1)fail('expected one reassessment state');
const x=rows[0].json;
// The post-research branch already carries a complete held receipt; return it unchanged.
if(x?.schema==='selected_story_reassessment_result.v1'
   && ['needs_editor_decision','unavailable'].includes(x.status) && x.next_action==='editor_review'
   && x.writing_authorized===false && x.research_loop_authorized===false) return [{json:x,pairedItem:{item:0}}];
if(x?.schema!=='selected_story_reassessment.v1')fail('wrong schema');
let reason='';
if(x.status==='review_required'&&x.next_action==='editor_review') reason=x.review_reason||x.research_increment_receipt?.insufficiency_reason||'Supplementary research did not produce usable material.';
else if(x.status==='prepared'&&x.story_mode==='deep_analysis') reason='Deep-analysis reassessment is not adapted in this phase; editor review is required.';
else fail('unexpected state reached hold branch');
return [{json:{schema:'selected_story_reassessment_result.v1',content_id:x.content_id,story_id:x.story_id,story_mode:x.story_mode,status:'needs_editor_decision',next_action:'editor_review',writing_authorized:false,research_loop_authorized:false,candidate:null,selected_quotations:[],preview_markdown:'',review_reason:reason,approved_story:x.approved_story,editor_input:x.editor_input,research_increment_receipt:x.research_increment_receipt},pairedItem:{item:0}}];
