// Disposable native-test adapter. Sources are pinned to the audited immutable commit.
// Never wire this loader into the product entry. It creates synthetic approval only.
const scenario = $('TEMP News Integration Entry').first().json.body?.scenario;
if (!['ready','hold','missing_approval'].includes(scenario)) throw new Error('Replay: unsupported scenario');
const handoffSource = $('TEMP Read Handoff Fixture').first().json.data;
const writerSource = $('TEMP Read Writing Fixture').first().json.data;
if (typeof handoffSource !== 'string' || !handoffSource.startsWith('// Reduced, public-material regression fixture') || typeof writerSource !== 'string' || !writerSource.startsWith('// Writing-material replay derived')) throw new Error('Replay: expected audited fixture sources');
const hm={exports:{}}, wm={exports:{}};
new Function('module',handoffSource)(hm);
new Function('require','module',writerSource)(name=>{if(name!=='./handoff.cjs') throw new Error('Replay: unexpected module dependency'); return hm.exports;},wm);
const x=wm.exports.fixture(), clone=hm.exports.clone, m=x.editor_input.materials;
if(m.sources.length!==8||m.claims.length!==10||m.quotations.length!==5) throw new Error('Replay: full material fixture missing');
const a=x.approved_story, parent=x.research_increment_receipt.research_work_order.parent_context;
if(parent.approval_bundle||parent.decision) throw new Error('Replay: refuse to overwrite existing approval');
const selected={schema:'story_candidate.v1',content_id:x.content_id,story_id:x.story_id,story_mode:x.story_mode,status:'needs_research',proposal:clone(a.proposal),research_requests:clone(a.research_requests)};
// Test copy only. Never changes the historical fixture or represents real Gmail approval.
parent.approval_bundle={schema:'story_approval.v1',content_id:x.content_id,choices:[{selection_value:1,story_mode:'news',candidate:clone(selected)}]};
parent.decision={schema:'story_decision.v1',content_id:x.content_id,status:'selected',selected_story:1,story_id:x.story_id,story_mode:x.story_mode,title:a.title,selected_candidate:clone(selected),next_action:'targeted_research'};
x.test_context={...x.test_context,scope:'post_research_to_assembled_preview',scenario,synthetic_approval:true,formal_hitl:false,fixture_commit:'2e6ef29abaa18141fffc64d4995ea236980a9c04',current_test_authorization:'User requested News post-research integration acceptance in this conversation.'};
if(scenario==='missing_approval') delete parent.approval_bundle;
if(scenario==='hold'){x.status='needs_editor_decision';x.next_action='editor_review';}
return [{json:x,pairedItem:{item:0}}];
