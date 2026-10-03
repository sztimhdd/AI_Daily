const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../../src/n8n/build-shared-dispatch.js'),'utf8');

function run(input){
  return vm.runInNewContext(`(async()=>{${code}})()`,{$input:{all:()=>[{json:input}]}});
}

function fixture(){
  const content_id='test:approval-provenance';
  const candidate={
    schema:'story_candidate.v1',content_id,story_id:'story_1',story_mode:'news',
    status:'needs_research',
    proposal:{working_title:'Approved title',reader_promise:'Reader promise'},
    research_requests:[{question:'Need one source',required_for_story:true}]
  };
  const editor_input={content_id,research_task_budget:3,materials:{sources:[],claims:[],quotations:[]}};
  const approval_bundle={schema:'story_approval.v1',content_id,choices:[{selection_value:1,story_mode:'news',candidate,selected_quotations:[]}]};
  const decision={
    schema:'story_decision.v1',content_id,status:'selected',selected_story:1,
    story_id:'story_1',story_mode:'news',selected_candidate:candidate,
    title:'Approved title',title_override:'',editor_note:'',
    additional_research_instructions:'',needs_targeted_research:true,
    next_action:'targeted_research',research_requests:candidate.research_requests,
    optional_research_requests:[],research_task_budget:3,selected_quotations:[]
  };
  return {schema:'story_approval_context.v1',content_id,editor_input,approval_bundle,decision,parent_context:{content_id,editor_input}};
}

test('selected dispatch preserves validated approval provenance in parent_context',async()=>{
  const x=fixture();
  const out=(await run(x))[0].json;
  assert.deepEqual(JSON.parse(JSON.stringify(out.parent_context.approval_bundle)),x.approval_bundle);
  assert.deepEqual(JSON.parse(JSON.stringify(out.parent_context.decision)),x.decision);
});
