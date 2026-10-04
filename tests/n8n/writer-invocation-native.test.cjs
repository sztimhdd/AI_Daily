// Archived inputs for native executions 587/588; not a production authorization source.
// Replay only with fresh user approval and verified disconnected Writer/service paths.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {fixture: mappedOrderFixture} = require('./fixtures/writer-input-native.cjs');

function fixture(name = 'positive') {
  assert.ok(['positive', 'wrong-language', 'missing-decision'].includes(name), 'unknown test case');
  const x = mappedOrderFixture();
  x.writer_invocation_decision = {
    schema: 'writer_invocation_decision.v1', status: 'authorized',
    authorization_kind: 'controlled_test', scope: 'writer_draft',
    content_id: x.content_id, story_id: x.story_id, story_mode: x.story_mode,
    title: x.writing_input.title,
    reader_promise: x.writing_input.approved_story.proposal.reader_promise,
    target_language: 'zh-CN',
    decision_source: {
      type: 'user_chat_authorization',
      reference: 'chat:2026-10-04-current-user-continue; isolated T03 validation only; not formal HITL or publication authorization'
    },
    side_effects_isolated: true
  };
  x.test_context = {
    kind: 'isolated_gate_contract_test', formal_hitl: false,
    model_calls_allowed: false, publication_allowed: false,
    fixture_source: 'tests/n8n/fixtures/writer-input-native.cjs'
  };
  if (name === 'wrong-language') x.writer_invocation_decision.target_language = 'en-US';
  if (name === 'missing-decision') delete x.writer_invocation_decision;
  return x;
}

function runNode(file, json) {
  const code = fs.readFileSync(path.join(__dirname, '../../src/n8n', file), 'utf8');
  return vm.runInNewContext(`(function(){${code}\n})()`, {
    $input: {all: () => [{json}], first: () => ({json})}
  }, {filename: file, timeout: 1000})[0].json;
}
const plain = value => JSON.parse(JSON.stringify(value));
const map = x => runNode('writer-context-builder.js', x);
const gate = x => runNode('writer-invocation-gate.js', x);

if (process.argv[2] === '--payload') {
  console.log(JSON.stringify(fixture(process.argv[3]), null, 2));
} else {
  require('node:test').test('native controlled-test fixture passes the real mapper/gate without losing evidence', () => {
    const input = fixture(), before = plain(input);
    const output = gate(map(input)), receipt = output.writer_invocation_receipt;
    assert.deepEqual(plain(input), before, 'input must not be mutated');
    assert.deepEqual(plain(output.writing_work_order), before, 'audit order must remain intact');
    assert.equal(receipt.authorization_kind, 'controlled_test');
    assert.equal(receipt.target_language, 'zh-CN');
    assert.equal(receipt.service_invoked, false);
    assert.equal(receipt.historical_writing_authorized, false);
    assert.equal(output.writing_work_order.research_loop_authorized, false);
    assert.equal(output.writer_brief.article_intent.thesis, null);
    assert.deepEqual(plain(output.writer_context.evidence.quotations), input.writing_input.selected_quotations);
    assert.equal(output.writer_context.evidence.sources.length, 2);
    assert.equal(output.writer_context.evidence.claims.length, 2);
    assert.ok(!JSON.stringify(output.writer_brief).includes('writer_invocation_decision'));
    assert.throws(() => gate(map(fixture('wrong-language'))), /target language mismatch/);
    assert.throws(() => gate(map(fixture('missing-decision'))), /explicit invocation decision missing/);
  });
}
