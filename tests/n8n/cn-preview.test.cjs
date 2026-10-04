// Pure interface tests. No model call or readership score.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '../..');
function run(file, json, upstream = {}) {
 const p = path.join(root,'src/n8n',file);
 assert.ok(fs.existsSync(p), `implementation missing: ${file}`);
 return vm.runInNewContext(`(function(){${fs.readFileSync(p,'utf8')}\n})()`, {
  $input:{all:()=>[{json}], first:()=>({json})},
  $:name=>({first:()=>({json:upstream[name]})})
 },{timeout:1000})[0].json;
}
const draft = '# 给普通读者的标题\n\n有头有尾的原稿；编辑失败也不能丢。';
const context = {content_id:'test:cn-preview',story_id:'story_1',story_mode:'news',
 writer_context:{config:{language:'zh-CN',content_type:'zhihu_longform'}},
 writer_brief:{article_intent:{reader_change:'读完能讲清这个变化'},editorial_instructions:{human_instructions:'先让读者想读',editor_note:''}},
 writer_invocation_receipt:{status:'authorized',scope:'writer_draft',target_language:'zh-CN',service_invoked:false}};
function input(){return run('cn-edit-input.js',{output:draft},{'Writer Invocation Gate':context});}
function preview(value){return run('cn-preview.js',value,{'V2 CN Edit Input':input()});}
const plain=x=>JSON.parse(JSON.stringify(x));
test('binds the real CN draft and reader context without creating a review or changing source input',()=>{
 const before=JSON.stringify(context), x=input();
 assert.equal(x.schema,'polish_input.v1'); assert.equal(x.article_to_polish,draft);
 assert.equal(x.content_id,context.content_id);assert.equal(x.config.language,'zh-CN');
 assert.equal(x.config.reader_promise,'读完能讲清这个变化');
 assert.deepEqual(plain(x.review_issues),[]);
 assert.equal(x.writer_invocation_receipt.service_invoked,false);
 assert.equal(JSON.stringify(context),before);
});
test('empty draft is rejected before the editor',()=>{
 assert.throws(()=>run('cn-edit-input.js',{output:'  '},{'Writer Invocation Gate':context}),/draft is empty/);
});
test('successful edit returns an unpublished preview and retains original draft',()=>{
 const edited='# 读者愿意打开的新标题\n\n先从具体变化说起。';
 const x=preview({output:edited});
 assert.equal(x.status,'draft');assert.equal(x.editing_status,'completed');
 assert.equal(x.article_title,'读者愿意打开的新标题');assert.equal(x.article_markdown,edited);
 assert.equal(x.draft_markdown,draft);assert.equal(x.publication.state,'NOT_PUBLISHED');
 assert.equal(x.publication.url,null);assert.equal(x.content_id,context.content_id);
});
test('native editor error preserves original, never claims an edited article or leaks raw error',()=>{
 const x=preview({error:{message:'secret transport trace'}});
 assert.equal(x.status,'review_required');assert.equal(x.editing_status,'failed');
 assert.equal(x.article_markdown,draft);assert.equal(x.draft_markdown,draft);
 assert.ok(!JSON.stringify(x).includes('secret transport'));
});
test('empty or malformed editor output also returns original as review_required',()=>{
 for(const output of ['# 原稿未提供，无法编辑。', '', '   ', '不是完整 Markdown 文章', '# A\n\n# B\n双标题']){
  const x=preview({output});assert.equal(x.status,'review_required');assert.equal(x.article_markdown,draft);
 }
});
