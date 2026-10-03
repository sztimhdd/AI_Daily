// AI Daily V3 — Writer Invocation Gate v1
// Validates authorization for THIS writer-draft invocation only.
// Does not mutate historical authorization receipts and does not call a model.
const fail = message => { throw new Error('Writer invocation gate: ' + message); };
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const text = v => typeof v === 'string' && v.trim().length > 0;

const rows = $input.all();
if (rows.length !== 1) fail('expected one mapped writer input');
const x = rows[0].json;
const order = x.writing_work_order;
const brief = x.writer_brief;
const decision = order?.writer_invocation_decision;

if (x.schema !== 'writer_context.v1' || x.status !== 'READY' || x.ready_for_writer !== true
    || !object(x.writer_context) || x.writer_context.schema !== 'writer_context.v1'
    || !object(brief) || brief.schema !== 'writer_brief.v3') fail('writer input is not ready');
if (!object(order) || order.schema !== 'writing_work_order.v1' || order.status !== 'prepared'
    || order.next_action !== 'prepare_writing' || order.service_invoked !== false) fail('prepared work order missing');
if (!object(order.writing_input) || order.writing_input.schema !== 'writing_handoff.v1') fail('writing handoff missing');

for (const holder of [order, order.preparation_source]) {
  if (!object(holder)) continue;
  if (Object.hasOwn(holder, 'writing_authorized') && holder.writing_authorized !== false) fail('historical authorization must remain false');
  if (Object.hasOwn(holder, 'research_loop_authorized') && holder.research_loop_authorized !== false) fail('historical authorization must remain false');
}

if (!object(decision) || decision.schema !== 'writer_invocation_decision.v1') fail('explicit invocation decision missing');
if (decision.status !== 'authorized' || decision.scope !== 'writer_draft') fail('invocation decision is not authorized for writer_draft');
if (!['controlled_test','formal_hitl'].includes(decision.authorization_kind)) fail('unsupported authorization kind');

const handoff = order.writing_input;
const promise = handoff.approved_story?.proposal?.reader_promise;
if (!text(handoff.title) || !text(promise)) fail('approved title/reader promise missing');
if (decision.content_id !== x.content_id || decision.content_id !== order.content_id
    || decision.story_id !== x.story_id || decision.story_id !== order.story_id
    || decision.story_mode !== x.story_mode || decision.story_mode !== order.story_mode) fail('invocation identity mismatch');
if (decision.title !== handoff.title || decision.reader_promise !== promise) fail('approved story mismatch');
if (!text(decision.target_language) || decision.target_language !== brief.language
    || decision.target_language !== x.writer_context?.config?.language) fail('target language mismatch');
if (!object(decision.decision_source) || !text(decision.decision_source.type)
    || !text(decision.decision_source.reference)) fail('decision source missing');

if (decision.authorization_kind === 'controlled_test') {
  if (decision.decision_source.type !== 'user_chat_authorization') fail('controlled test source must be user_chat_authorization');
  if (decision.side_effects_isolated !== true) fail('controlled test requires isolated side effects');
} else {
  if (decision.decision_source.type !== 'story_decision_execution') fail('formal HITL source must be story_decision_execution');
  const p = order.preparation_source;
  const bundle = p?.approval_bundle;
  const priorDecision = p?.decision;
  if (!object(bundle) || bundle.schema !== 'story_approval.v1'
      || !object(priorDecision) || priorDecision.schema !== 'story_decision.v1'
      || priorDecision.status !== 'selected') fail('formal HITL provenance missing');
  if (bundle.content_id !== x.content_id || priorDecision.content_id !== x.content_id
      || priorDecision.story_id !== x.story_id || priorDecision.story_mode !== x.story_mode) fail('formal HITL identity mismatch');
}

const receipt = {
  schema: 'writer_invocation_receipt.v1',
  status: 'authorized',
  authorization_kind: decision.authorization_kind,
  scope: decision.scope,
  content_id: x.content_id,
  story_id: x.story_id,
  story_mode: x.story_mode,
  title: handoff.title,
  reader_promise: promise,
  target_language: brief.language,
  decision_source: decision.decision_source,
  side_effects_isolated: decision.side_effects_isolated === true,
  historical_writing_authorized: Object.hasOwn(order, 'writing_authorized') ? order.writing_authorized : null,
  service_invoked: false
};

return [{json:{...x, writer_invocation_receipt:receipt}, pairedItem:{item:0}}];