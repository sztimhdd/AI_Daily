// Prepared V3 order -> existing Writer contracts. No model, research or authorization.
// This replaces the unpublished V2 planner-output input contract; old nodes are retained.
const fail = message => { throw new Error('Writer input: ' + message); };
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const text = v => typeof v === 'string' && v.trim().length > 0;
const equal = (a,b) => JSON.stringify(a,sort) === JSON.stringify(b,sort);
function sort(k,v) { return object(v) ? Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])) : v; }
const rows = $input.all();
if (rows.length !== 1) fail('expected one prepared order');
const x = rows[0].json, h = x.writing_input, config = x.task_config;
if (x.schema !== 'writing_work_order.v1' || x.status !== 'prepared'
    || x.next_action !== 'prepare_writing' || x.service_invoked !== false) fail('order is not prepared');
if (!object(h) || h.schema !== 'writing_handoff.v1' || !text(x.content_id)
    || !['news','deep_analysis'].includes(x.story_mode)
    || x.story_id !== (x.story_mode === 'news' ? 'story_1' : 'story_2')) fail('order identity mismatch');
for (const value of [h,h.approved_story]) {
  if (!object(value) || value.story_id !== x.story_id || value.story_mode !== x.story_mode) fail('story identity mismatch');
}
if (h.content_id !== x.content_id) fail('handoff identity mismatch');
if (!object(x.preparation_source)) fail('preparation provenance missing');
for (const key of ['writing_authorized','research_loop_authorized']) {
  if ((Object.hasOwn(x,key) && x[key] !== false)
      || (Object.hasOwn(x.preparation_source,key) && x.preparation_source[key] !== false)) fail('historical authorization must remain false');
}
if (!object(config) || !['en-US','zh-CN'].includes(config.language)) fail('explicit supported task_config.language required');
for (const language of [x.language,x.creative_blueprint?.language,h.language,h.task_config?.language,h.creative_blueprint?.language]) {
  if (language !== undefined && language !== config.language) fail('conflicting language');
}
if (!text(config.content_type)) fail('explicit task_config.content_type required');
if (typeof h.human_instructions !== 'string' || typeof h.editor_note !== 'string') fail('human instructions missing');
const p = h.approved_story.proposal, m = h.materials;
if (!text(h.title) || !object(p) || !text(p.working_title) || !text(p.reader_promise)
    || !object(p.opening) || !Array.isArray(p.opening.material_refs)
    || !Array.isArray(p.story_path) || !p.story_path.length
    || p.story_path.some(s=>!object(s)||!text(s.job)||!Array.isArray(s.material_refs))
    || !Array.isArray(p.quotation_refs) || !object(m)) fail('proposal/material bindings missing');
const judgment = x.story_mode === 'deep_analysis' ? p.analysis_judgment : null;
if (x.story_mode === 'deep_analysis' && (!text(judgment) || judgment.trim().toLowerCase() === 'none')) fail('Deep judgment missing');
function registry(key) {
  if (!Array.isArray(m[key])) fail('material collection missing: ' + key);
  const out = new Map();
  for (const v of m[key]) {
    if (!object(v) || !text(v.ref)) fail('material reference missing');
    if (out.has(v.ref)) fail('duplicate material reference');
    out.set(v.ref,v);
  }
  return out;
}
const sources = registry('sources'), claims = registry('claims'), quotes = registry('quotations');
function source(ref) {
  const s = sources.get(ref);
  if (!s || s.claim_eligible !== true || !['body_fetched','partial_body'].includes(s.retrieval_status)
      || !text(s.url) || !/^https?:\/\/[^\s]+$/.test(s.url)) fail('missing/ineligible material source');
  return s;
}
function publicSource(ref) {
  const s = source(ref);
  return {title:s.title ?? null,kind:s.source_kind ?? null,url:s.url,
    retrieval_status:s.retrieval_status,note:s.source_note ?? null};
}
for (const c of claims.values()) {
  if (!text(c.statement) || !text(c.status) || !Array.isArray(c.source_refs) || !c.source_refs.length) fail('claim/source binding missing');
  c.source_refs.forEach(source);
}
for (const q of quotes.values()) {
  if (!text(q.text_original) || !text(q.speaker) || !text(q.attribution)) fail('quotation attribution missing');
  source(q.source_ref);
}
const refs = [...new Set([...p.opening.material_refs,...p.story_path.flatMap(s=>s.material_refs),...p.quotation_refs])];
if (!refs.length || refs.some(ref=>!claims.has(ref)&&!quotes.has(ref))) fail('unknown selected material');
if (p.quotation_refs.some(ref=>!quotes.has(ref))) fail('invalid quotation reference');
const selectedRefs = refs.filter(ref=>quotes.has(ref));
if (!Array.isArray(h.selected_quotations) || h.selected_quotations.length !== selectedRefs.length) fail('selected quotation set mismatch');
const selected = new Map(h.selected_quotations.map(q=>[q.ref,q]));
if (selected.size !== selectedRefs.length || selectedRefs.some(ref=>!equal(selected.get(ref),
    {...quotes.get(ref),source_url:source(quotes.get(ref).source_ref).url}))) fail('selected quotation drift');
function proposition(ref) {
  if (claims.has(ref)) {
    const c = claims.get(ref);
    return {kind:'claim',text:c.statement,status:c.status,attribution:c.attribution ?? null,
      sources:c.source_refs.map(publicSource)};
  }
  const q = quotes.get(ref);
  return {kind:'quotation',text:q.text_original,speaker:q.speaker,language:q.language ?? null,
    attribution:q.attribution,source_context:q.source_context ?? null,editorial_use:q.editorial_use ?? null,
    sources:[publicSource(q.source_ref)]};
}
const movements = p.story_path.map((s,i)=>({id:'s'+(i+1),job:s.job,
  reader_change:s.reader_change ?? null,propositions:s.material_refs.map(proposition)}));
const narrative = {story_mode:x.story_mode,title:h.title,reader_change:p.reader_promise,
  thesis:judgment,central_tension:p.central_tension ?? null};
const sections = p.story_path.map((s,i)=>({id:'s'+(i+1),job:s.job,reader_change:s.reader_change ?? null,
  claim_ids:s.material_refs.filter(ref=>claims.has(ref)),quotation_refs:s.material_refs.filter(ref=>quotes.has(ref))}));
const storyContract = {schema:'story_contract.v1',status:'READY',...narrative,sections,
  forbidden_claims:p.forbidden_claims ?? p.must_not_claim ?? []};
const usedSources = new Set([...claims.values()].flatMap(c=>c.source_refs)
  .concat([...quotes.values()].map(q=>q.source_ref)));
const reviewerClaims = [...claims.values()].map(c=>({id:c.ref,status:c.status,claim:c.statement,
  attribution:c.attribution ?? null,source_ids:c.source_refs,support:(c.support ?? []).map(s=>{
    const ref = String(s.source_id).includes(':') ? s.source_id : c.ref.split(':')[0]+':'+s.source_id;
    if (!c.source_refs.includes(ref) || typeof (s.evidence ?? s.text) !== 'string') fail('support/source binding missing');
    return {source_id:ref,locator:s.locator ?? null,text:s.evidence ?? s.text};
  })}));
const writerContext = {schema:'writer_context.v1',config:{...config},narrative,
  story_contract:storyContract,evidence:{claims:reviewerClaims,
    sources:[...usedSources].map(ref=>({id:ref,...publicSource(ref)})),
    quotations:h.selected_quotations,gaps:m.open_questions ?? [],conflicts:m.conflicts ?? []},selection:{}};
const writerBrief = {schema:'writer_brief.v3',language:config.language,content_type:config.content_type,
  title:h.title,story_mode:x.story_mode,target_length:config.word_count_target ?? null,
  platform_profile:config.platform_profile ?? null,
  article_intent:{reader_change:p.reader_promise,thesis:judgment,central_tension:p.central_tension ?? null,
    news_anchor:p.news_anchor ?? null,story_pitch:p.story_pitch ?? null},
  editorial_instructions:{human_instructions:h.human_instructions,editor_note:h.editor_note},
  voice:{persona_and_vantage_point:config.persona_and_vantage_point ?? null,rhetorical_rules:config.rhetorical_rules ?? {}},
  opening:{description:p.opening.description ?? null,propositions:p.opening.material_refs.map(proposition)},
  movements,quotations:h.selected_quotations.map(q=>proposition(q.ref)),coverage_wins:p.coverage_wins ?? [],
  evidence_boundaries:{open_questions:m.open_questions ?? [],conflicts:m.conflicts ?? []},
  hard_red_lines:storyContract.forbidden_claims};
return [{json:{schema:'writer_context.v1',content_id:x.content_id,story_id:x.story_id,story_mode:x.story_mode,
  status:'READY',ready_for_writer:true,writing_work_order:x,
  story_contract:storyContract,writer_context:writerContext,writer_brief:writerBrief},pairedItem:{item:0}}];
