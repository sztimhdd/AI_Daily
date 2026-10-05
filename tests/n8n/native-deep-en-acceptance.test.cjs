// Offline checks of the disposable acceptance harness, not the article or production workflow.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const manifest=JSON.parse(fs.readFileSync(__dirname+'/native-deep-en-acceptance.nodes.json','utf8'));
const code=name=>manifest.nodes.find(n=>n.name==='TEMP Deep EN '+name).parameters.jsCode;
for(const n of manifest.nodes.filter(n=>n.type==='n8n-nodes-base.code'))new Function('$input','$','$execution',n.parameters.jsCode);
const source='https://example.test/source';
const materials={sources:[{url:source,claim_eligible:true}],claims:[],quotations:[]};
const proposal={analysis_judgment:'saved judgment'};
const fixture={content_id:'test:deep-en',editor_input:{materials},decision:{selected_candidate:{proposal}}};
const original={schema:'writing_work_order.v1',status:'prepared',content_id:fixture.content_id,story_id:'story_2',story_mode:'deep_analysis',service_invoked:false,writing_input:{title:'Saved title',materials,approved_story:{proposal:{...proposal,reader_promise:'saved promise'}}}};
const invoke=(script,input,refs)=>new Function('$input','$','$execution',script)({first:()=>({json:input})},name=>{assert.ok(name in refs,name);return {first:()=>({json:refs[name]})};},{id:'offline-test'})[0].json;
const before=JSON.stringify(original);
for(const scenario of ['ready','language_mismatch']){
 const w=invoke(code('Authorize'),original,{'TEMP Deep EN Entry':{body:{scenario}}});
 assert.equal(w.task_config.language,'en-US');
 assert.equal(w.writer_invocation_decision.target_language,scenario==='ready'?'en-US':'zh-CN');
 assert.equal(JSON.stringify(original),before);
}
function run(p){return invoke(code('Assert'),p,{'TEMP Deep EN Entry':{body:{scenario:'ready'}},'TEMP Deep EN Fixture':fixture,'TEMP Deep EN Authorize':{writing_input:{materials,approved_story:{proposal}}}});}
function sample(bodyCount){
 const text='# Example\n\n[Source]('+source+')\n\nA conditional explanation.';
 const images=Array.from({length:bodyCount},(_,i)=>({markdown_insertion:'\n\n![Illustration '+i+'](https://example.test/'+i+'.png)'}));
 return {schema:'writing_preview.v1',content_id:fixture.content_id,story_id:'story_2',story_mode:'deep_analysis',language:'en-US',config:{language:'en-US',content_type:'linkedin_article'},writer_invocation_receipt:{authorization_kind:'controlled_test'},publication:{state:'NOT_PUBLISHED',url:null},status:'draft',editing_status:'completed',draft_markdown:text,article_markdown:text,assembly_status:'completed',visual_planning_status:'completed',image_generation_status:'completed',image_counts:{requested:bodyCount+1,succeeded:bodyCount+1,failed:0},image_requests:[{role:'article_cover'},...images.map(()=>({role:'body_illustration'}))],image_assets:[...Array(bodyCount+1)].map(()=>({status:'READY',asset:{url:'https://raw.githubusercontent.com/sztimhdd/AI_Daily/test.png'},alt_text:'A generic illustration',caption:''})),assembled_article:{schema:'assembled_article.v1',cover_image:{id:'COVER_IMG'},body_images:images,article_markdown:text+images.map(x=>x.markdown_insertion).join('')}};
}
for(const n of [0,1,3])assert.equal(run(sample(n)).passed,true);
const changed=sample(1);changed.assembled_article.article_markdown+='Unwanted rewrite';
assert.throws(()=>run(changed),/assembly changed prose/);
const invented=sample(0);invented.article_markdown=invented.article_markdown.replace(source,'https://example.test/invented');invented.assembled_article.article_markdown=invented.article_markdown;
assert.throws(()=>run(invented),/source URL missing or invented/);
console.log('PASS: script syntax; isolated authorization; dynamic 0/1/3 body images; changed prose and invented URL rejected. No network or model calls.');
