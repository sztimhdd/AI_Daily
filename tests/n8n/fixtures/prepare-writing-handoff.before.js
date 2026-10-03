// Direct-ready handoff only; no outline rewriting and no authoring call.
const x=$input.first().json;
const fail=m=>{throw new Error('Writing handoff: '+m);};
if(x.schema!=='story_dispatch.v1'||x.next_action!=='prepare_writing'||x.approved_candidate?.status!=='ready'||x.research_requests.length||x.additional_research_instructions.trim())fail('writing is not ready');
const ctx=x.editor_input,p=x.approved_candidate.proposal;
if(ctx.content_id!==x.content_id||x.approved_candidate.content_id!==x.content_id)fail('identity mismatch');
const quotes=new Map(ctx.materials.quotations.map(q=>[q.ref,q]));
const sources=new Map(ctx.materials.sources.map(s=>[s.ref,s]));
const claims=new Map(ctx.materials.claims.map(c=>[c.ref,c]));
const refs=[...new Set([...p.opening.material_refs,...p.story_path.flatMap(s=>s.material_refs),...p.quotation_refs])];
for(const id of refs)if(!quotes.has(id)&&!claims.has(id))fail('unknown selected material '+id);
const selected=refs.filter(id=>quotes.has(id)).map(id=>{
 const q=quotes.get(id),s=sources.get(q.source_ref);
 if(x.parent_context.quotation_validation?.valid===false||!s||s.claim_eligible!==true||!['body_fetched','partial_body'].includes(s.retrieval_status))fail('quotation source is not eligible');
 return {...q,source_url:s.url};
});
const approved={story_id:x.story_id,story_mode:x.story_mode,proposal:p};
const writing={schema:'writing_handoff.v1',content_id:x.content_id,title:x.title,story_id:x.story_id,story_mode:x.story_mode,
 topic_brief:ctx.topic_brief,human_instructions:ctx.human_instructions,editor_note:x.editor_note,title_override:x.title_override,
 approved_story:approved,materials:ctx.materials,selected_quotations:selected,
 brief_content:x.parent_context.brief_content??x.parent_context.report_content??'',
 editorial_dossier:x.parent_context.editorial_dossier??null,
 quotation_validation:x.parent_context.quotation_validation??null,
 supplementary_dossier:null,supplementary_research_status:'not_requested'};
return [{json:{schema:'writing_work_order.v1',content_id:x.content_id,story_id:x.story_id,story_mode:x.story_mode,
 status:'prepared',next_action:'prepare_writing',service_invoked:false,writing_input:writing},pairedItem:{item:0}}];