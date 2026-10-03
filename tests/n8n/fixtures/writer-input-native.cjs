// Reproduce mapping fixtures for n8n executions 580/581/582.
// Reuses public texts from handoff.cjs. Title/promise and audit envelope are
// deliberately reduced for this seam. NOT a full T01 receipt or formal approval.
const {reassessed,clone} = require('./handoff.cjs');
function fixture(conflict=false) {
 const original=reassessed(), m=original.editor_input.materials;
 const id='test:writer-input-native-20261003';
 const title='模型路由与提供商路由：公告和应用记录分别说明了什么？';
 const qrefs=['initial:QT01','supplementary:QT01'];
 const srefs=['initial:S01','supplementary:S01'];
 const crefs=['initial:C02','supplementary:C01'];
 const sources=srefs.map((ref,i)=>{
  const s=m.sources.find(s=>s.ref===ref);
  return {ref:s.ref,url:s.url,title:i?'Cline 3.8.0 release notes':'Stripe announcement',
   source_kind:s.source_kind,claim_eligible:s.claim_eligible,retrieval_status:s.retrieval_status};
 });
 const claims=crefs.map(ref=>clone(m.claims.find(c=>c.ref===ref)));
 const quotations=qrefs.map(ref=>clone(m.quotations.find(q=>q.ref===ref)));
 const selected_quotations=quotations.map(q=>({...q,source_url:sources.find(s=>s.ref===q.source_ref).url}));
 const proposal={working_title:title,reader_promise:'区分公告中的模型路由说明与应用内的提供商路由设置。',
  opening:{description:'从两份记录的不同功能归属切入。',material_refs:crefs},
  story_path:[{job:'并置两份说明，不冒充独立实测。',material_refs:[...crefs,...qrefs]}],quotation_refs:qrefs};
 const x={schema:'writing_work_order.v1',content_id:id,story_id:'story_1',story_mode:'news',
  status:'prepared',next_action:'prepare_writing',service_invoked:false,
  task_config:{language:'zh-CN',content_type:'zhihu_longform'},
  writing_authorized:false,research_loop_authorized:false,
  preparation_source:{schema:'selected_story_reassessment_result.v1',content_id:id,story_id:'story_1',story_mode:'news',
   writing_authorized:false,research_loop_authorized:false,
   test_context:{kind:'reduced_mapping_fixture',source_fixture:'tests/n8n/fixtures/handoff.cjs',formal_hitl:false},
   historical_research_requests:[{question:'寻找公开使用记录。',required_for_story:true}]},
  writing_input:{schema:'writing_handoff.v1',content_id:id,story_id:'story_1',story_mode:'news',title,title_override:null,
   topic_brief:'公告与应用记录的裁剪映射样本；不作为完整成稿或正式审批材料。',
   human_instructions:original.editor_input.human_instructions,editor_note:'',brief_content:'',editorial_dossier:null,
   quotation_validation:null,supplementary_dossier:null,supplementary_research_status:'research_ready',
   approved_story:{story_id:'story_1',story_mode:'news',proposal},
   materials:{sources,claims,quotations,open_questions:[],conflicts:[]},selected_quotations}};
 if(conflict)x.creative_blueprint={language:'en-US'};
 return x;
}
module.exports={fixture};
if(require.main===module)console.log(JSON.stringify(fixture(process.argv.includes('--conflict')),null,2));
