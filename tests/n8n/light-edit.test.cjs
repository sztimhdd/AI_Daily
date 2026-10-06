const {test}=require('node:test');
const a=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../src/n8n');
const run=(name,values,context)=>new Function('$input','$',fs.readFileSync(path.join(root,name),'utf8'))(
 {all:()=>values.map(json=>({json})),first:()=>({json:values[0]})},()=>({first:()=>({json:context}),item:{json:context}}))[0].json;
const context={content_id:'test:E',story_mode:'news',stage:'writing_materials_ready',human_instructions:'Keep this exact.',
 story_direction:{working_title:'Test',core_judgment:null},materials:[{url:'https://example.org/evidence',retrieval:{raw_content:'Test source.'}}],
 narrative_feedback:{test:true},publication:{state:'NOT_PUBLISHED',url:null}};
const row=language=>({...structuredClone(context),language,content_type:language==='zh-CN'?'zhihu_longform':'linkedin_article',
 draft:{language,story_mode:'news',status:'completed',title:language==='zh-CN'?'原稿':'Original',markdown:language==='zh-CN'?'# 原稿\n\n原始[来源](https://example.org/evidence)。':'# Original\n\nOriginal [source](https://example.org/evidence).'}});
const preview=(c,ok=true)=>({schema:'writing_preview.v1',content_id:c.content_id,story_mode:c.story_mode,language:c.language,
 status:ok?'draft':'review_required',editing_status:ok?'completed':'failed',draft_markdown:c.draft.markdown,
 article_markdown:ok?(c.language==='zh-CN'?'# 编辑稿\n\n保留[来源](https://example.org/evidence)。':'# Edited\n\nRetained [source](https://example.org/evidence).'):c.draft.markdown,
 warnings:ok?[]:['editor_failed_original_retained'],publication:{state:'NOT_PUBLISHED',url:null}});
for(const [name,changed] of [['both_edits_survive',false],['failed_first_keeps_original_and_sibling',true]])test(name,()=>{
 const zh=row('zh-CN'),en=row('en-US');zh.preview=preview(zh,!changed);en.preview=preview(en);
 const out=run('collect-mode-drafts.js',[en,zh],zh);
 a.equal(out.previews?.['zh-CN']?.article_markdown,zh.preview.article_markdown);
 a.equal(out.previews?.['en-US']?.article_markdown,en.preview.article_markdown);
 a.deepEqual(out.drafts['zh-CN'],zh.draft);a.deepEqual(out.materials,context.materials);
 a.deepEqual(out.narrative_feedback,context.narrative_feedback);
 a.equal(out.editing_stage,changed?'edits_partial':'edits_ready');
});
test('missing_edit_keeps_original_and_is_not_success',()=>{
 const zh=row('zh-CN'),en=row('en-US');en.preview=preview(en);
 const out=run('collect-mode-drafts.js',[zh,en],zh);
 a.equal(out.previews?.['zh-CN']?.article_markdown,zh.draft.markdown);
 a.equal(out.previews?.['zh-CN']?.editing_status,'not_started');
 a.equal(out.editing_stage,'edits_partial');
});
for(const lang of ['zh-CN','en-US'])test('capture_success_'+lang,()=>{
 const c=row(lang),before=structuredClone(c),candidate=preview(c).article_markdown;
 const out=run('capture-light-edit.js',[{output:candidate}],c);
 a.deepEqual(c,before);a.deepEqual(out.draft,c.draft);a.deepEqual(out.materials,c.materials);
 a.equal(out.preview.article_markdown,candidate);a.equal(out.preview.draft_markdown,c.draft.markdown);
 a.equal(out.preview.editing_status,'completed');a.equal(out.preview.language,lang);
});
for(const [name,response] of Object.entries({error:{error:{message:'controlled'}},empty:{output:''},heading_only:{output:'# Title'},wrong_language:{output:'# 中文\n\nBody.'},all_links_lost:{output:'# Edited\n\nBody without sources.'}}))test('retain_original_'+name,()=>{
 const c=row('en-US'),out=run('capture-light-edit.js',[response],c);
 a.deepEqual(out.draft,c.draft);a.equal(out.preview.article_markdown,c.draft.markdown);
 a.equal(out.preview.editing_status,'failed');a.equal(out.preview.status,'review_required');
 a.equal(out.preview.publication.state,'NOT_PUBLISHED');
});
test('mispaired_preview_is_not_adopted',()=>{
 const zh=row('zh-CN'),en=row('en-US');zh.preview=preview(en);en.preview=preview(en);
 const out=run('collect-mode-drafts.js',[zh,en],zh);
 a.equal(out.previews['zh-CN'].article_markdown,zh.draft.markdown);
 a.ok(out.edit_issues.includes('edit_identity_mismatch:zh-CN'));
});
