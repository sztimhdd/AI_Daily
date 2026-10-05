// Counts are test cases, not editorial quotas. No network or model calls.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const target=path.join(__dirname,'../../src/n8n/article-assembler.js');
function run(p){
  const code=fs.existsSync(target)?fs.readFileSync(target,'utf8'):"throw new Error('assembler implementation missing');";
  return JSON.parse(JSON.stringify(vm.runInNewContext(`(function(){${code}})()`,{$input:{all:()=>[{json:p}],first:()=>({json:p})}})[0].json));
}
function fixture(n=0){
 const paragraphs=['**先读文字。** 没有图片也能交付。','链接 [原文](https://example.org/source) 和 $& 保留。','保留这个结尾。'];
 const article='# 组装测试\n\n'+paragraphs.join('\n\n');
 const p={schema:'writing_preview.v1',status:'draft',editing_status:'completed',content_id:'test:assembly',story_id:'story_1',story_mode:'news',language:'zh-CN',article_title:'组装测试',article_markdown:article,draft_markdown:'# 原稿\n\n这份原稿也要保留。',image_generation_status:n?'completed':'skipped',image_assets:[],warnings:[],publication:{state:'NOT_PUBLISHED',url:null}};
 if(n) for(let i=0;i<=n;i++) p.image_assets.push({schema:'image_asset.v1',id:i?'IMG_'+i:'COVER_IMG',role:i?'body_illustration':'article_cover',status:i?'READY':'GEOMETRY_WARNING',alt_text:'画面 '+i,caption:i?'图注 '+i:'',placement:{mode:i?'after_paragraph':'cover_field',anchor:i?paragraphs[i-1]:''},asset:{url:'https://example.invalid/'+(i?'IMG_'+i:'COVER_IMG')+'.png',width:i?1024:1536,height:1024,mime:'image/png',geometry_status:i?'PASS':'MISMATCH'}});
 return p;
}
function unchanged(p,o){assert.equal(o.article_markdown,p.article_markdown);assert.equal(o.draft_markdown,p.draft_markdown);assert.equal(o.content_id,p.content_id);assert.equal(o.language,p.language);assert.deepEqual(o.publication,p.publication);}
test('zero images returns unchanged readable article, without requiring cover',()=>{
 const p=fixture(),o=run(p);unchanged(p,o);assert.equal(o.assembly_status,'completed');assert.equal(o.assembled_article.article_markdown,p.article_markdown);assert.equal(o.assembled_article.cover_image,null);
});
test('one or three body images follow paragraph positions, cover remains separate',()=>{
 for(const n of [1,3]){const p=fixture(n);p.image_assets.reverse();const before=JSON.stringify(p),o=run(p),a=o.assembled_article;unchanged(p,o);assert.equal(JSON.stringify(p),before);assert.equal(a.body_images.length,n);assert.equal(a.cover_image.width,1536);assert.equal(a.cover_image.geometry_status,'MISMATCH');assert.ok(!a.article_markdown.includes(a.cover_image.url));
 let stripped=a.article_markdown;for(const image of [...a.body_images].reverse())stripped=stripped.replace(image.markdown_insertion,'');assert.equal(stripped,p.article_markdown);assert.deepEqual(a.body_images.map(x=>x.id),Array.from({length:n},(_,i)=>'IMG_'+(i+1)));}
});
test('failed cover and failed/bad body leave remaining image and both texts',()=>{
 const p=fixture(3);p.image_assets[0].status='FAILED';p.image_assets[0].asset=null;p.image_assets[1].status='FAILED';p.image_assets[1].asset=null;p.image_assets[2].placement.anchor='段落片段';const o=run(p);unchanged(p,o);assert.equal(o.assembly_status,'partial');assert.equal(o.assembled_article.cover_image,null);assert.deepEqual(o.assembled_article.body_images.map(x=>x.id),['IMG_3']);assert.deepEqual(o.assembly_skipped_images,['COVER_IMG','IMG_1','IMG_2']);
});
test('missing/duplicate/non-prose anchors never edit article or discard text',()=>{
 for(const kind of ['fragment','missing','repeated','heading','fenced']){const p=fixture(1),img=p.image_assets[1],anchor=img.placement.anchor;if(kind==='fragment')img.placement.anchor='先读文字';if(kind==='missing')img.placement.anchor='没有这段。';if(kind==='repeated')p.article_markdown+='\n\n'+anchor;if(kind==='heading')img.placement.anchor='# 组装测试';if(kind==='fenced'){p.article_markdown+='\n\n```text\n\n代码段。\n\n```';img.placement.anchor='代码段。';}const o=run(p);unchanged(p,o);assert.equal(o.assembled_article.body_images.length,0);assert.equal(o.assembled_article.article_markdown,p.article_markdown);}
});
test('literal dollar syntax, Markdown escaping, CRLF, and replay do not change source',()=>{
 const p=fixture(1);p.article_markdown=p.article_markdown.replaceAll('\n','\r\n');p.image_assets[1].caption='费用 $& *保留* [字面]';p.image_assets[1].alt_text='[图片] <非HTML> \\ 路径';p.image_assets[1].asset.url='https://example.invalid/image(1).png';const o=run(p);unchanged(p,o);assert.ok(o.assembled_article.article_markdown.includes('$& \\*保留\\*'));assert.ok(o.assembled_article.article_markdown.includes('(<https://example.invalid/image(1).png>)'));assert.deepEqual(run(o),o);
});
test('duplicate image IDs and unsafe URLs are omitted, not substituted',()=>{
 const p=fixture(3);p.image_assets.push({...p.image_assets[1]});p.image_assets[2].asset.url='javascript:alert(1)';const o=run(p);unchanged(p,o);assert.deepEqual(o.assembled_article.body_images.map(x=>x.id),['IMG_3']);assert.ok(!o.assembled_article.article_markdown.includes('javascript:'));
});
test('unpublished preview and nonempty text are required at the boundary',()=>{
 for(const patch of [{publication:{state:'PUBLISHED',url:'https://example.invalid/post'}},{article_markdown:''},{schema:'other'}])assert.throws(()=>run({...fixture(),...patch}),/Assembly: expected/);
});
module.exports={fixture,run};
