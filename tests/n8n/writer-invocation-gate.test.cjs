const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const codePath = path.join(__dirname, '../../src/n8n/writer-invocation-gate.js');
const gateCode = fs.existsSync(codePath) ? fs.readFileSync(codePath, 'utf8') : '';

function baseMapped() {
  const content_id = 'test:t03-writer-auth-20261003';
  return {
    schema: 'writer_context.v1', content_id, story_id: 'story_1', story_mode: 'news',
    status: 'READY', ready_for_writer: true,
    writing_work_order: {
      schema: 'writing_work_order.v1', content_id, story_id: 'story_1', story_mode: 'news',
      status: 'prepared', next_action: 'prepare_writing', service_invoked: false,
      task_config: {language:'zh-CN', content_type:'zhihu_longform'},
      writing_authorized: false, research_loop_authorized: false,
      preparation_source: {
        schema:'selected_story_reassessment_result.v1', content_id, story_id:'story_1', story_mode:'news',
        writing_authorized:false, research_loop_authorized:false,
        test_context:{kind:'controlled_writer_test', formal_hitl:false}
      },
      writing_input: {
        schema:'writing_handoff.v1', content_id, story_id:'story_1', story_mode:'news',
        title:'Stripe 拟收购 OpenRouter：模型路由进入支付公司的版图',
        approved_story:{story_id:'story_1',story_mode:'news',proposal:{reader_promise:'解释交易状态、模型路由作用与用户承诺。'}},
        human_instructions:'保留归属，不把签约写成交割完成。', editor_note:'', materials:{sources:[],claims:[],quotations:[]}, selected_quotations:[]
      }
    },
    writer_context:{schema:'writer_context.v1',config:{language:'zh-CN'}},
    writer_brief:{schema:'writer_brief.v3',language:'zh-CN',title:'Stripe 拟收购 OpenRouter：模型路由进入支付公司的版图',article_intent:{reader_change:'解释交易状态、模型路由作用与用户承诺。'}}
  };
}

function decisionFor(mapped, overrides={}) {
  return {
    schema:'writer_invocation_decision.v1', status:'authorized', authorization_kind:'controlled_test',
    scope:'writer_draft', content_id:mapped.content_id, story_id:mapped.story_id, story_mode:mapped.story_mode,
    title:mapped.writing_work_order.writing_input.title,
    reader_promise:mapped.writing_work_order.writing_input.approved_story.proposal.reader_promise,
    target_language:mapped.writer_brief.language,
    decision_source:{type:'user_chat_authorization',reference:'chat:2026-10-03T14:01-03:00'},
    side_effects_isolated:true,
    ...overrides
  };
}

function run(input) {
  if (!gateCode.trim()) throw new Error('gate implementation missing');
  const sandbox = {$input:{all:()=>[{json:input}],first:()=>({json:input})},console};
  const wrapped = `(async()=>{${gateCode}})()`;
  return vm.runInNewContext(wrapped, sandbox);
}

test('rejects mapped writer input without an explicit invocation decision', async()=>{
  await assert.rejects(()=>run(baseMapped()), /invocation decision/i);
});
test('authorizes a controlled test only when scope and source are explicit', async()=>{
  const x=baseMapped(); x.writing_work_order.writer_invocation_decision=decisionFor(x);
  const out=await run(x); const y=out[0].json;
  assert.equal(y.writer_invocation_receipt.status,'authorized');
  assert.equal(y.writer_invocation_receipt.authorization_kind,'controlled_test');
  assert.equal(y.writer_invocation_receipt.decision_source.type,'user_chat_authorization');
  assert.equal(y.writer_invocation_receipt.historical_writing_authorized,false);
  assert.equal(y.writer_brief.language,'zh-CN');
});
test('rejects title or reader-promise drift', async()=>{
  for (const change of [{title:'Different title'},{reader_promise:'Different promise'}]) {
    const x=baseMapped(); x.writing_work_order.writer_invocation_decision=decisionFor(x,change);
    await assert.rejects(()=>run(x), /approved story mismatch/i);
  }
});
test('rejects wrong story identity or target language', async()=>{
  for (const change of [{content_id:'other'},{story_id:'story_2'},{target_language:'en-US'}]) {
    const x=baseMapped(); x.writing_work_order.writer_invocation_decision=decisionFor(x,change);
    await assert.rejects(()=>run(x), /(identity|language)/i);
  }
});
test('controlled test requires isolated side effects and user-chat source', async()=>{
  const cases=[
    {side_effects_isolated:false},
    {decision_source:{type:'story_decision_execution',reference:'550'}},
    {decision_source:{type:'user_chat_authorization',reference:''}}
  ];
  for (const change of cases) {
    const x=baseMapped(); x.writing_work_order.writer_invocation_decision=decisionFor(x,change);
    await assert.rejects(()=>run(x), /(controlled test|source|side effects)/i);
  }
});
test('formal HITL cannot be inferred from a reassessment receipt that lacks approval provenance', async()=>{
  const x=baseMapped();
  x.writing_work_order.writer_invocation_decision=decisionFor(x,{authorization_kind:'formal_hitl',decision_source:{type:'story_decision_execution',reference:'550'}});
  await assert.rejects(()=>run(x), /formal HITL provenance/i);
});
test('rejects any attempt to rewrite historical false authorization', async()=>{
  const x=baseMapped(); x.writing_work_order.writing_authorized=true;
  x.writing_work_order.writer_invocation_decision=decisionFor(x);
  await assert.rejects(()=>run(x), /historical authorization/i);
});

test('formal HITL accepts approval provenance preserved inside reassessment research parent_context', async()=>{
  const x=baseMapped();
  const content_id=x.content_id;
  const candidate={schema:'story_candidate.v1',content_id,story_id:'story_1',story_mode:'news',status:'ready',proposal:{working_title:x.writing_work_order.writing_input.title,reader_promise:x.writing_work_order.writing_input.approved_story.proposal.reader_promise},research_requests:[]};
  const approval_bundle={schema:'story_approval.v1',content_id,choices:[{selection_value:1,story_mode:'news',candidate,selected_quotations:[]}]};
  const decision={schema:'story_decision.v1',content_id,status:'selected',selected_story:1,story_id:'story_1',story_mode:'news',selected_candidate:candidate,title:x.writing_work_order.writing_input.title,title_override:'',editor_note:'',additional_research_instructions:'',needs_targeted_research:true,next_action:'targeted_research',research_requests:[],optional_research_requests:[],research_task_budget:3,selected_quotations:[]};
  x.writing_work_order.preparation_source={
    schema:'selected_story_reassessment_result.v1',content_id,story_id:'story_1',story_mode:'news',writing_authorized:false,research_loop_authorized:false,
    research_increment_receipt:{schema:'research_increment_receipt.v1',research_work_order:{schema:'research_work_order.v1',parent_context:{content_id,approval_bundle,decision}}}
  };
  x.writing_work_order.writer_invocation_decision=decisionFor(x,{authorization_kind:'formal_hitl',decision_source:{type:'story_decision_execution',reference:'native-test'}});
  const out=await run(x);
  assert.equal(out[0].json.writer_invocation_receipt.authorization_kind,'formal_hitl');
});