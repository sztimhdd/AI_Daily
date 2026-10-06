const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const src=fs.readFileSync(process.env.CAPTURE_CODE||path.join(__dirname,'../../src/n8n/capture-light-edit.js'),'utf8');
// Minimal transport regression. Exact saved 757 text was separately replayed in native execution 759.
const fixture={before:'# 原稿\n\n[发布](https://example.org/a)；[帮助](https://example.org/b)；[人物原话](https://example.org/c)。',after:'# 编辑稿\n\n[发布](https://example.org/a)；[帮助](https://example.org/b)；人物原话仍在。',urls:['https://example.org/a','https://example.org/b','https://example.org/c']};
function run(markdown,response){
 const c={content_id:'test:link-rule',story_mode:'news',language:'zh-CN',content_type:'zhihu_longform',materials:[{url:'https://example.org/context',raw_content:'unchanged'}],draft:{status:'completed',language:'zh-CN',story_mode:'news',title:markdown.split('\n')[0].slice(2),markdown}};
 const snapshot=JSON.stringify(c);
 const row=new Function('$','$input',src)(name=>{assert.equal(name,'Draft Ready for Edit');return {item:{json:c}};},{first:()=>({json:response})})[0].json;
 assert.equal(JSON.stringify(c),snapshot,'must not mutate input');
 assert.equal(row.draft.markdown,markdown);
 assert.equal(row.preview.draft_markdown,markdown);
 assert.deepEqual(row.materials,c.materials);
 assert.equal(row.preview.publication.state,'NOT_PUBLISHED');
 return row.preview;
}
const short='# 原稿\n\n正文[一](https://example.org/a)，[二](https://example.org/b)。';
test('one URL lost must reject and preserve original and rejected candidate',()=>{
 const p=run(fixture.before,{output:fixture.after});
 assert.equal(p.editing_status,'failed'); assert.equal(p.status,'review_required');
 assert.equal(p.article_markdown,fixture.before);assert.equal(p.editor_candidate_markdown,fixture.after);
 assert.deepEqual(p.link_changes.removed,[fixture.urls[2]]);
 assert.equal(p.editing_error.reason,'source_urls_missing');
 assert.deepEqual(p.editing_error.missing_source_urls,[fixture.urls[2]]);
 assert.ok(p.warnings.includes('source_urls_missing_original_retained'));
});
test('same URLs moved into a footer pass; location is irrelevant',()=>{
 const out=fixture.after.replace(/\[([^\]]+)\]\(https?:[^)]+\)/g,'$1')+'\n\n## 来源\n\n'+fixture.urls.map((u,i)=>`[来源${i+1}](${u})`).join(' · ');
 const p=run(fixture.before,{output:out}); assert.equal(p.editing_status,'completed');assert.equal(p.article_markdown,out);assert.deepEqual(p.warnings,[]);assert.deepEqual(p.link_changes.removed,[]);
});
test('original without URLs does not fail solely for lacking links',()=>{const p=run('# 无来源样本\n\n纯合成文字。',{output:'# 已编辑样本\n\n新的合成文字。'});assert.equal(p.editing_status,'completed');assert.deepEqual(p.link_changes.before,[]);});
test('empty edit retains original',()=>{const p=run(short,{output:''});assert.equal(p.editing_status,'failed');assert.equal(p.article_markdown,short);assert.equal(p.editor_candidate_markdown,'');assert.equal(p.editing_error.reason,'invalid_output');});
test('model error retains original and partial output',()=>{const out='# 未完成编辑\n\n部分输出。';const p=run(short,{output:out,error:{message:'Injected model failure'}});assert.equal(p.editing_status,'failed');assert.equal(p.article_markdown,short);assert.equal(p.editor_candidate_markdown,out);assert.equal(p.editing_error.reason,'model_error');assert.equal(p.editing_error.message,'Injected model failure');});
test('a new URL cannot substitute for a missing original even when counts match',()=>{const p=run(short,{output:'# 编辑稿\n\n[一](https://example.org/a)，[三](https://example.org/c)。'});assert.equal(p.editing_status,'failed');assert.deepEqual(p.link_changes.removed,['https://example.org/b']);});
test('unchanged original passes',()=>{const p=run(short,{output:short});assert.equal(p.editing_status,'completed');assert.deepEqual(p.link_changes.removed,[]);});
test('wrong title language still rejected despite preserved URLs',()=>{const p=run(short,{output:'# English title\n\n[一](https://example.org/a)，[二](https://example.org/b)。'});assert.equal(p.editing_status,'failed');assert.equal(p.article_markdown,short);});
