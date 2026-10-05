// Existing Prepare Writing Handoff node: direct ready OR News reassessment.
// Preparation only. No model, network, publication, or authorization decision.
const rows = $input.all();
const fail = message => { throw new Error('Writing handoff: ' + message); };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = value => typeof value === 'string' && value.trim().length > 0;
const canonical = value => JSON.stringify(value, (_, v) => object(v)
  ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
const equal = (a, b) => canonical(a) === canonical(b);
if (rows.length !== 1) fail('expected one input');
const raw = rows[0].json;
const x = raw.body ?? raw;
const reassessment = x.schema === 'selected_story_reassessment_result.v1';
if (!reassessment && x.schema !== 'story_dispatch.v1') fail('unsupported input schema');
if (!text(x.content_id) || !['news', 'deep_analysis'].includes(x.story_mode)
    || x.story_id !== (x.story_mode === 'news' ? 'story_1' : 'story_2')) fail('identity mismatch');
if (reassessment && x.story_mode !== 'news') fail('Deep reassessment remains held');
const c = reassessment ? x.candidate : x.approved_candidate;
const ctx = x.editor_input;
if (!object(c) || !object(ctx) || c.content_id !== x.content_id || ctx.content_id !== x.content_id
    || c.story_id !== x.story_id || c.story_mode !== x.story_mode) fail('candidate/context identity mismatch');
if (c.schema !== 'story_candidate.v1' || c.status !== 'ready') fail('candidate is not ready');
if (!Array.isArray(c.research_requests)
    || c.research_requests.some(r => !object(r) || typeof r.required_for_story !== 'boolean' || r.required_for_story)) fail('unfinished current research');
const p = c.proposal;
if (!object(p) || !text(p.working_title) || !text(p.reader_promise)
    || !object(p.opening) || !Array.isArray(p.opening.material_refs)
    || !Array.isArray(p.story_path) || !p.story_path.length
    || p.story_path.some(s => !object(s) || !Array.isArray(s.material_refs))
    || !Array.isArray(p.quotation_refs)) fail('proposal/material bindings missing');
if (x.story_mode === 'deep_analysis' && (!text(p.analysis_judgment)
    || p.analysis_judgment.trim().toLowerCase() === 'none')) fail('Deep judgment missing');
if (!text(ctx.topic_brief) || typeof ctx.human_instructions !== 'string') fail('assignment/instructions missing');

let parent, title, editorNote, titleOverride, increment = null;
if (reassessment) {
  if (x.status !== 'ready_for_writer_handoff' || x.next_action !== 'prepare_writing_handoff') fail('reassessment is not ready');
  if (x.writing_authorized !== false || x.research_loop_authorized !== false) fail('historical authorization must remain false');
  const a = x.approved_story;
  increment = x.research_increment_receipt;
  const w = increment?.research_work_order;
  const prior = w?.research_input?.final_narrative;
  parent = w?.parent_context;
  if (!object(a) || !object(increment) || !object(w) || !object(prior) || !object(parent)
      || increment.schema !== 'research_increment_receipt.v1' || w.schema !== 'research_work_order.v1') fail('reassessment provenance missing');
  for (const item of [a, increment, w, prior]) {
    if (item.story_id !== x.story_id || item.story_mode !== x.story_mode) fail('historical story identity mismatch');
  }
  for (const item of [increment, w, w.research_input, w.editor_input, parent]) {
    if (item?.content_id !== x.content_id) fail('historical content identity mismatch');
  }
  if (increment.status !== 'usable_materials' || increment.service_invoked !== true
      || increment.requires_reassessment !== true || w.service_invoked !== false) fail('research receipt is not ready');
  if (!equal(parent.editor_input ?? parent, w.editor_input)) fail('original parent snapshot changed');
  if (!equal(ctx.approved_story, a) || !equal(prior.proposal, a.proposal) || prior.title !== a.title) fail('approved snapshot mismatch');
  if (p.working_title !== a.title || p.reader_promise !== a.proposal.reader_promise) fail('approved title/promise changed');
  if (ctx.human_instructions !== w.editor_input.human_instructions
      || (typeof prior.initial_human_instructions === 'string' && ctx.human_instructions !== prior.initial_human_instructions)
      || ctx.topic_brief !== w.editor_input.topic_brief) fail('original instructions changed');
  if (typeof a.editor_note !== 'string' || a.editor_note !== prior.editor_note
      || typeof a.additional_research_instructions !== 'string'
      || a.additional_research_instructions !== w.research_input.human_instructions) fail('editor instructions changed');
  title = a.title;
  editorNote = a.editor_note;
  // Absence is not a fabricated title-override decision. Original is in preparation_source.
  titleOverride = Object.hasOwn(a, 'title_override') ? a.title_override : null;
  // Use the CURRENT candidate for readiness. Historical research requests stay in provenance.
  const old = w.editor_input.materials, added = increment.accepted_materials;
  if (!object(old) || !object(added)) fail('research material snapshots missing');
  for (const key of ['sources', 'claims', 'quotations']) {
    if (!Array.isArray(old[key]) || !Array.isArray(added[key]) || !Array.isArray(ctx.materials?.[key])) fail('material collections missing');
    const expected = [...old[key], ...added[key]];
    const actual = ctx.materials[key];
    if (expected.length !== actual.length) fail('merged material count changed');
    const byRef = new Map(actual.map(v => [v.ref, v]));
    if (byRef.size !== actual.length || new Set(expected.map(v => v.ref)).size !== expected.length
        || expected.some(v => !equal(byRef.get(v.ref), v))) fail('merged material snapshot changed');
  }
} else {
  if (x.next_action !== 'prepare_writing' || x.selection_status !== 'selected'
      || !Array.isArray(x.research_requests) || x.research_requests.length
      || typeof x.additional_research_instructions !== 'string' || x.additional_research_instructions.trim()) fail('writing is not ready');
  parent = x.parent_context;
  if (!object(parent) || !equal(parent.editor_input ?? parent, ctx)) fail('parent material snapshot mismatch');
  if (typeof x.title_override !== 'string' || typeof x.editor_note !== 'string') fail('editor instructions missing');
  title = x.title;
  titleOverride = x.title_override;
  editorNote = x.editor_note;
  if (title !== (titleOverride.trim() || p.working_title)) fail('approved title mismatch');
}

const materials = ctx.materials;
if (!object(materials)) fail('materials missing');
const allRefs = new Set();
function registry(key, kind) {
  if (!Array.isArray(materials[key])) fail(key + ' missing');
  const map = new Map();
  for (const item of materials[key]) {
    if (!object(item) || typeof item.ref !== 'string'
        || !new RegExp('^(initial|supplementary):' + kind + '[0-9]+$').test(item.ref)) fail('invalid ' + key + ' reference');
    if (allRefs.has(item.ref)) fail('duplicate material reference');
    allRefs.add(item.ref); map.set(item.ref, item);
  }
  return map;
}
const sources = registry('sources', 'S');
const claims = registry('claims', 'C');
const quotes = registry('quotations', 'QT');
function eligible(ref) {
  const s = sources.get(ref);
  if (!s || s.claim_eligible !== true || !['body_fetched', 'partial_body'].includes(s.retrieval_status)
      || typeof s.url !== 'string' || !/^https?:\/\/[^\s]+$/.test(s.url)) fail('missing/ineligible material source');
  return s;
}
for (const claim of claims.values()) {
  if (!text(claim.statement) || !Array.isArray(claim.source_refs) || !claim.source_refs.length) fail('claim/source binding missing');
  claim.source_refs.forEach(eligible);
}
for (const q of quotes.values()) {
  eligible(q.source_ref);
  if (!text(q.text_original) || !text(q.speaker) || !text(q.attribution)) fail('quotation text/attribution missing');
}
const refs = [...new Set([...p.opening.material_refs, ...p.story_path.flatMap(s => s.material_refs), ...p.quotation_refs])];
if (!refs.length || refs.some(ref => !claims.has(ref) && !quotes.has(ref))) fail('unknown selected material');
if (p.quotation_refs.some(ref => !quotes.has(ref))) fail('quotation reference is not a quotation');
const selected = refs.filter(ref => quotes.has(ref)).map(ref => {
  const q = quotes.get(ref);
  const validation = ref.startsWith('supplementary:') && reassessment
    ? increment.quotation_validation : parent.quotation_validation;
  if (validation?.valid !== true || !Array.isArray(validation.errors) || validation.errors.length
      || !Number.isInteger(validation.checked_count) || validation.checked_count < [...quotes.keys()].filter(id => id.split(':')[0] === ref.split(':')[0]).length
      || validation.checked_count !== validation.quotation_count) fail('quotation verification missing');
  return {...q, source_url: eligible(q.source_ref).url};
});
if (reassessment) {
  if (!Array.isArray(x.selected_quotations) || x.selected_quotations.length !== selected.length) fail('selected quotation set changed');
  const supplied = new Map(x.selected_quotations.map(q => [q.ref, q]));
  if (supplied.size !== selected.length || selected.some(q => !equal(supplied.get(q.ref), q))) fail('selected quotation drift');
}
const writing = {
  schema: 'writing_handoff.v1', content_id: x.content_id, title,
  story_id: x.story_id, story_mode: x.story_mode,
  topic_brief: ctx.topic_brief, human_instructions: ctx.human_instructions,
  editor_note: editorNote, title_override: titleOverride,
  approved_story: {story_id: x.story_id, story_mode: x.story_mode, proposal: p},
  materials, selected_quotations: selected,
  brief_content: parent.brief_content ?? parent.report_content ?? '',
  editorial_dossier: parent.editorial_dossier ?? null,
  quotation_validation: parent.quotation_validation ?? null,
  supplementary_dossier: null,
  supplementary_research_status: reassessment ? increment.worker_research_status : 'not_requested'
};
const output = {
  schema: 'writing_work_order.v1', content_id: x.content_id,
  story_id: x.story_id, story_mode: x.story_mode, status: 'prepared',
  next_action: 'prepare_writing', service_invoked: false, writing_input: writing,
  // Audit-only snapshot. Do not send this object to a Writer model.
  preparation_source: x
};
if (reassessment) {
  output.writing_authorized = x.writing_authorized;
  output.research_loop_authorized = x.research_loop_authorized;
}
return [{json: output, pairedItem: {item: 0}}];
