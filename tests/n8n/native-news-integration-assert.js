// Disposable acceptance terminal. No edits, network calls, or publication.
const check=(ok,message)=>{if(!ok)throw new Error('News integration acceptance: '+message);};
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);
const source=$('TEMP Prepare News Replay').first().json;
const scenario=source.test_context.scenario, rows=$input.all();
check(rows.length===1,'expected one returned item');
const p=rows[0].json;
if(scenario==='hold'){
 check(canonical(p)===canonical(source),'hold changed the receipt');
 return [{json:{test:'news_post_research_integration',scenario,passed:true,writer_called:false,
  result_schema:p.schema,next_action:p.next_action,synthetic_approval:true,formal_hitl:false},pairedItem:{item:0}}];
}
check(scenario==='ready','invalid approval must not reach acceptance');
const w=$('Prepare Writer Invocation').first().json;
check(w.schema==='writing_work_order.v1'&&w.status==='prepared'&&w.service_invoked===false,'work order state');
check(canonical(w.preparation_source)===canonical(source),'historical receipt mutated');
check(canonical(w.writing_input.materials)===canonical(source.editor_input.materials),'initial or supplementary materials changed');
check(canonical([...w.writing_input.selected_quotations].sort((a,b)=>a.ref.localeCompare(b.ref)))===canonical([...source.selected_quotations].sort((a,b)=>a.ref.localeCompare(b.ref))),'selected quotation drift');
check(w.writing_authorized===false&&w.research_loop_authorized===false,'historical authorization changed');
check(w.preparation_source.research_increment_receipt.research_work_order.parent_context.decision.next_action==='targeted_research','historical research action rewritten');
check(w.writer_invocation_decision.status==='authorized'&&w.writer_invocation_decision.target_language==='zh-CN','invocation decision');
check(p.schema==='writing_preview.v1'&&p.status==='draft'&&p.editing_status==='completed','edited preview missing');
check(p.content_id===source.content_id&&p.story_id==='story_1'&&p.story_mode==='news'&&p.language==='zh-CN','returned identity/language');
check(typeof p.draft_markdown==='string'&&p.draft_markdown.trim().length>0,'original draft lost');
check(typeof p.article_markdown==='string'&&p.article_markdown.startsWith('# '),'edited text missing');
check(p.publication?.state==='NOT_PUBLISHED'&&p.publication.url===null,'publication boundary');
check(p.assembly_status==='completed'&&p.assembled_article?.schema==='assembled_article.v1','assembled preview missing');
check(p.visual_planning_status==='completed'&&p.image_generation_status==='completed','real visual chain incomplete');
const tasks=p.image_requests, assets=p.image_assets, assembled=p.assembled_article;
check(Array.isArray(tasks)&&tasks.length>=1&&Array.isArray(assets)&&assets.length===tasks.length,'dynamic asset count');
check(p.image_counts.requested===tasks.length&&p.image_counts.succeeded===tasks.length&&p.image_counts.failed===0,'image receipt counts');
check(assembled.cover_image?.id==='COVER_IMG','cover field missing');
const body=assembled.body_images;
check(Array.isArray(body)&&body.length===tasks.filter(t=>t.role==='body_illustration').length,'body image count differs from plan');
check(assembled.counts.body_images_inserted===body.length,'insert count');
for(const asset of assets){
 check(['READY','GEOMETRY_WARNING'].includes(asset.status),'failed asset');
 check(/^https:\/\/raw\.githubusercontent\.com\/sztimhdd\/AI_Daily\/n8n-v3-handoff-20261003\/n8n\/images\//.test(asset.asset?.url||''),'wrong image destination');
}
let stripped=assembled.article_markdown;
for(const img of body){
 check(typeof img.markdown_insertion==='string'&&stripped.includes(img.markdown_insertion),'missing image insertion');
 stripped=stripped.replace(img.markdown_insertion,'');
 check(assembled.article_markdown.includes(img.url),'body URL missing');
}
check(stripped===p.article_markdown,'assembly rewrote edited text');
check(!assembled.article_markdown.includes(assembled.cover_image.url),'cover inserted into body');
return [{json:{test:'news_post_research_integration',scenario,passed:true,writer_called:true,
 result_schema:p.schema,assembly_status:p.assembly_status,publication:p.publication,
 synthetic_approval:true,formal_hitl:false,material_counts:{sources:w.writing_input.materials.sources.length,
 claims:w.writing_input.materials.claims.length,quotations:w.writing_input.materials.quotations.length},
 selected_quotation_refs:w.writing_input.selected_quotations.map(q=>q.ref),
 initial_and_supplementary_preserved:true,historical_authorization_preserved:true,
 image_counts:p.image_counts,body_images_inserted:body.length,assembly_text_unchanged:true,
 draft_chars:p.draft_markdown.length,edited_chars:p.article_markdown.length,
 warnings:p.warnings,article_title:assembled.article_title,article_markdown:assembled.article_markdown,
 cover_image:assembled.cover_image,body_images:body.map(({id,url,alt_text,caption})=>({id,url,alt_text,caption}))
},pairedItem:{item:0}}];
