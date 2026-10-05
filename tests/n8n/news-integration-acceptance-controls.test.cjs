const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const run=new Function('$input','$',fs.readFileSync(__dirname+'/native-news-integration-assert.js','utf8'));
const clone=x=>JSON.parse(JSON.stringify(x));
// Synthetic controls test the acceptance assertions, not models or the full product suite.
function fixture(count=1){
 const source={content_id:'synthetic',schema:'selected_story_reassessment_result.v1',test_context:{scenario:'ready'},editor_input:{materials:{sources:[{ref:'initial:S01'},{ref:'supplementary:S01'}],claims:[{ref:'initial:C01'},{ref:'supplementary:C01'}],quotations:[]}},selected_quotations:[],research_increment_receipt:{research_work_order:{parent_context:{decision:{next_action:'targeted_research'}}}}};
 const w={schema:'writing_work_order.v1',status:'prepared',service_invoked:false,preparation_source:clone(source),writing_input:{materials:clone(source.editor_input.materials),selected_quotations:[]},writing_authorized:false,research_loop_authorized:false,writer_invocation_decision:{status:'authorized',target_language:'zh-CN'}};
 const url=id=>'https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/n8n/images/test/'+id+'.png';
 const body=Array.from({length:count},(_,i)=>({id:'IMG_'+(i+1),url:url('IMG_'+(i+1)),markdown_insertion:'\n\n![image](<'+url('IMG_'+(i+1))+'>)',alt_text:'fixture',caption:''}));
 const requests=[{id:'COVER_IMG',role:'article_cover'},...body.map(x=>({id:x.id,role:'body_illustration'}))];
 const p={schema:'writing_preview.v1',status:'draft',editing_status:'completed',content_id:'synthetic',story_id:'story_1',story_mode:'news',language:'zh-CN',draft_markdown:'# Title\n\nDraft fixture.',article_markdown:'# Title\n\nEdited fixture.',publication:{state:'NOT_PUBLISHED',url:null},assembly_status:'completed',visual_planning_status:'completed',image_generation_status:'completed',image_requests:requests,image_assets:requests.map(r=>({id:r.id,status:'READY',asset:{url:url(r.id)}})),image_counts:{requested:requests.length,succeeded:requests.length,failed:0},warnings:[],assembled_article:{schema:'assembled_article.v1',article_title:'Title',article_markdown:'# Title\n\nEdited fixture.'+body.map(x=>x.markdown_insertion).join(''),cover_image:{id:'COVER_IMG',url:url('COVER_IMG')},body_images:body,counts:{body_images_inserted:count}}};
 return {source,w,p};
}
function execute(f){return run({all:()=>[{json:f.p}]},name=>({first:()=>({json:name==='TEMP Prepare News Replay'?f.source:f.w})}))[0].json;}
for(const count of [0,1,3])test('dynamic body count '+count+' passes intact',()=>assert.equal(execute(fixture(count)).passed,true));
const mutations=[
 ['material loss',f=>f.w.writing_input.materials.claims.pop(),/materials changed/],
 ['history mutation',f=>f.w.preparation_source.extra='changed',/receipt mutated/],
 ['historical authorization',f=>f.w.writing_authorized=true,/authorization changed/],
 ['identity drift',f=>f.p.content_id='other',/identity/],
 ['lost draft',f=>f.p.draft_markdown='',/draft lost/],
 ['published output',f=>f.p.publication.state='PUBLISHED',/publication boundary/],
 ['incomplete images',f=>f.p.image_generation_status='failed',/visual chain incomplete/],
 ['wrong host',f=>f.p.image_assets[0].asset.url='https://example.invalid/image.png',/image destination/],
 ['assembly rewrite',f=>f.p.assembled_article.article_markdown+='changed',/assembly rewrote/],
 ['lost body image',f=>f.p.assembled_article.body_images=[],/body image count/]
];
for(const [name,mutate,pattern]of mutations)test(name+' rejected',()=>{const f=fixture();mutate(f);assert.throws(()=>execute(f),pattern);});
test('hold returned unchanged without consulting invocation',()=>{const x={schema:'selected_story_reassessment_result.v1',test_context:{scenario:'hold'},next_action:'editor_review'};const result=run({all:()=>[{json:clone(x)}]},name=>{assert.equal(name,'TEMP Prepare News Replay');return {first:()=>({json:x})};});assert.equal(result[0].json.writer_called,false);});
