const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
function run(file,rows,context){
 const src=fs.readFileSync(__dirname+'/../../src/n8n/'+file,'utf8');
 return new Function('$input','$',src)({all:()=>rows.map(json=>({json})),first:()=>({json:rows[0]})},name=>{
  assert.ok(name in context,'unexpected dependency '+name);return {first:()=>({json:context[name]})};
 })[0].json;
}
function context(mode='deep_analysis'){
 return {content_id:'test:cn-context',story_id:mode==='news'?'story_1':'story_2',story_mode:mode,
  writer_context:{config:{language:'zh-CN',content_type:'wechat_article',audience:'test-reader'}},
  writer_brief:{schema:'writer_brief.v3',language:'zh-CN',story_mode:mode,
   article_intent:{reader_change:'test promise',thesis:mode==='news'?null:'supplied judgment'},
   editorial_instructions:{human_instructions:'keep attribution',editor_note:''},movements:[{propositions:[{text:'source material',status:'attributed'}]}]},
  writer_invocation_receipt:{schema:'writer_invocation_receipt.v1',authorization_kind:'controlled_test',target_language:'zh-CN'}};
}
const draft='\n# 原稿\n\n已存在的正文。\n';
function editInput(ctx=context()){return run('cn-edit-input.js',[{output:draft}],{'Writer Invocation Gate':ctx});}
for(const mode of ['deep_analysis','news'])test(mode+' carries existing complete brief without mutation',()=>{
 const ctx=context(mode),before=JSON.stringify(ctx),p=editInput(ctx);
 assert.deepEqual(p.writer_brief,ctx.writer_brief);
 assert.equal(p.article_to_polish,draft);assert.equal(JSON.stringify(ctx),before);
});
test('wrong brief language is rejected',()=>{const ctx=context();ctx.writer_brief.language='en-US';assert.throws(()=>editInput(ctx),/Chinese writer context/);});
test('empty draft remains rejected',()=>assert.throws(()=>run('cn-edit-input.js',[{output:''}],{'Writer Invocation Gate':context()}),/draft is empty/));
for(const result of [{output:'# 编辑稿\n\n编辑后的正文。'},{error:'controlled error'},{output:'invalid response'}])test('preview retains original and metadata: '+Object.keys(result)[0]+':'+String(result.output||result.error).slice(0,10),()=>{
 const input=editInput();const p=run('cn-preview.js',[result],{'V2 CN Edit Input':input});
 assert.deepEqual(p.config,input.config);assert.deepEqual(p.writer_invocation_receipt,input.writer_invocation_receipt);
 assert.equal(p.draft_markdown,draft);assert.equal(p.story_mode,'deep_analysis');
 assert.deepEqual(p.publication,{state:'NOT_PUBLISHED',url:null});
 const valid=result.output?.startsWith('# ');
 assert.equal(p.status,valid?'draft':'review_required');assert.equal(p.article_markdown,valid?result.output:draft);
});
