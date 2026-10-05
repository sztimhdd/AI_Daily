// Isolated contract fixtures; no real approval, news, services or credentials.
const {test}=require('node:test'),a=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const src=path.join(__dirname,'../../src/n8n');
function run(name,rows,context={}){return new Function('$input','$','$execution',fs.readFileSync(path.join(src,name),'utf8'))({all:()=>rows,first:()=>rows[0]},n=>({all:()=>context[n],first:()=>context[n]?.[0]}),{id:'fixture'});}
function order(mode='news',reassessed=false){
 const id={content_id:'test:bilingual',story_id:mode==='news'?'story_1':'story_2',story_mode:mode};
 const proposal={reader_promise:'supplied promise',analysis_judgment:mode==='news'?null:'supplied judgment'};
 const provenance={approval_bundle:{schema:'story_approval.v1',content_id:id.content_id},decision:{schema:'story_decision.v1',status:'selected',...id,title:'approved selection title',next_action:reassessed?'targeted_research':'prepare_writing',selected_candidate:{proposal}}};
 return {schema:'writing_work_order.v1',...id,status:'prepared',next_action:'prepare_writing',service_invoked:false,writing_authorized:false,writing_input:{schema:'writing_handoff.v1',...id,title:'approved selection title',approved_story:{proposal},materials:{claims:[{ref:'initial:C1',text:'unchanged'}]}},preparation_source:reassessed?{schema:'selected_story_reassessment_result.v1',status:'ready_for_writer_handoff',next_action:'prepare_writing_handoff',research_increment_receipt:{research_work_order:{parent_context:provenance}}}:{parent_context:provenance}};
}
const prep=w=>run('prepare-writer-invocation.js',[{json:w}]);
for(const [mode,re] of [['news',false],['news',true],['deep_analysis',false]])test('default two languages '+mode+' reassessed='+re,()=>{
 const w=order(mode,re),original=JSON.stringify(w),rows=prep(w);
 a.deepEqual(rows.map(x=>x.json.task_config.language),['zh-CN','en-US']);
 for(const {json:x} of rows){a.deepEqual(x.writing_input,w.writing_input);a.equal(x.writing_authorized,false);a.equal(x.writer_invocation_decision.target_language,x.task_config.language);a.equal(x.writer_invocation_decision.title,w.writing_input.title);}
 a.equal(JSON.stringify(w),original);rows[0].json.task_config.language='modified';a.equal(rows[1].json.task_config.language,'en-US');
});
test('hold stays hold',()=>a.deepEqual(prep({next_action:'hold'}),[]));
test('missing approval rejected',()=>{let w=order();w.preparation_source={};a.throws(()=>prep(w),/provenance/);});
test('Deep supplementary stays blocked',()=>a.throws(()=>prep(order('deep_analysis',true)),/News reassessment/));
function preview(lang='zh-CN',count=1){
 const zh=lang==='zh-CN',title=zh?'模型选择与支出':'Model choice and spending',md='# '+title+'\n\n'+(zh?'已有正文。':'Existing article.');
 const img=i=>({id:i?'IMG_'+i:'COVER_IMG',url:'https://example.test/'+lang+'/'+i+'.png',alt_text:zh?'分流装置':'A routing switch',caption:i?(zh?'选择也影响支出。':'Choices also affect spending.'):'',geometry_status:'PASS'});
 return {schema:'writing_preview.v1',content_id:'test:bilingual',story_id:'story_1',story_mode:'news',language:lang,config:{language:lang,content_type:zh?'zhihu_longform':'linkedin_article'},article_title:title,article_markdown:md,draft_markdown:md+'\n',editing_status:'completed',status:'draft',assembly_status:'completed',image_generation_status:'completed',warnings:[],publication:{state:'NOT_PUBLISHED',url:null},assembled_article:{schema:'assembled_article.v1',article_title:title,article_markdown:md,cover_image:img(0),body_images:Array.from({length:count},(_,i)=>img(i+1)),status:'READY'}};
}
function kit(lang){const zh=lang==='zh-CN';return {schema:'social_kit.v1',language:lang,seo_title:zh?'模型与支出':'Models and spending',seo_description:zh?'模型选择如何影响支出。':'How model choices affect spending.',linkedin_post:zh?'一次选择也影响费用。':'A choice also affects costs.',hashtags:zh?['#人工智能','#模型路由','#技术','#成本']:['#AI','#Routing','#Technology','#Costs']};}
const pack=(p,k)=>run('publication-package-builder.js',[{json:k}],{'V2 Article Assembler':[{json:p}]})[0].json;
for(const lang of ['zh-CN','en-US'])for(const n of [0,1,3])test('localized package '+lang+' body='+n,()=>{
 const p=preview(lang,n),before=JSON.stringify(p),out=pack(p,{output:kit(lang)}),k=out.publication_package;
 a.equal(out.schema,'writing_preview.v1');a.equal(k.language,lang);a.equal(k.article.title,p.article_title);a.equal(k.article.markdown,p.assembled_article.article_markdown);a.equal(k.body_images.length,n);a.equal(k.social_kit.language,lang);a.equal(out.draft_markdown,p.draft_markdown);a.equal(k.status,'DRAFT');a.ok(k.article.filename.endsWith(lang+'.md'));a.equal(JSON.stringify(p),before);
});
test('kit error preserves article',()=>{const p=preview();const out=pack(p,{error:'test failure'});a.equal(out.article_markdown,p.article_markdown);a.equal(out.social_kit_status,'failed');a.equal(out.publication_package.social_kit,null);});
test('wrong kit language not silently relabeled',()=>a.equal(pack(preview(),{output:kit('en-US')}).social_kit_status,'failed'));
test('wrong-language title flagged without losing text',()=>{const p=preview('en-US');p.article_title=p.assembled_article.article_title='中文标题';const r=pack(p,{output:kit('en-US')});a.equal(r.publication_package.status,'REVIEW_REQUIRED');a.equal(r.article_markdown,p.article_markdown);});
test('wrong-language caption flagged without losing image',()=>{const p=preview('en-US');p.assembled_article.body_images[0].caption='中文图注';const r=pack(p,{output:kit('en-US')});a.equal(r.publication_package.status,'REVIEW_REQUIRED');a.equal(r.publication_package.body_images[0].url,p.assembled_article.body_images[0].url);});
function aggregate(rows){return run('aggregate-drafts.js',rows,{'Prepare Writer Invocation':prep(order())})[0].json;}
const good=lang=>pack(preview(lang),{output:kit(lang)});
test('two versions aggregated by native paired item not array order',()=>{const r=aggregate([{json:good('en-US'),pairedItem:{item:1}},{json:good('zh-CN'),pairedItem:{item:0}}]);a.equal(r.delivery_status,'completed');a.equal(r.versions['en-US'].article.title,'Model choice and spending');});
test('one child failure keeps sibling',()=>{const r=aggregate([{json:{error:'controlled'},pairedItem:{item:0}},{json:good('en-US'),pairedItem:{item:1}}]);a.equal(r.delivery_status,'partial');a.equal(r.versions['en-US'].status,'DRAFT');a.equal(r.versions['zh-CN'].status,'FAILED');});
test('missing second never called complete',()=>a.equal(aggregate([{json:good('zh-CN'),pairedItem:{item:0}}]).delivery_status,'partial'));
test('duplicate language and identity mismatch rejected without overwriting sibling',()=>{const en=good('en-US');en.content_id='other';const r=aggregate([{json:good('zh-CN'),pairedItem:{item:0}},{json:en,pairedItem:{item:1}},{json:good('zh-CN'),pairedItem:{item:0}}]);a.equal(r.delivery_status,'partial');a.ok(r.rejected_results.length);a.equal(r.versions['zh-CN'].article.title,'模型选择与支出');});
