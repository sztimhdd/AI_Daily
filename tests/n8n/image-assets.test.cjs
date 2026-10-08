// Transport and return-contract checks. Fake URLs/bytes are never generation evidence.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'../..');
const plain=x=>JSON.parse(JSON.stringify(x));
async function run(file, items, refs={}) {
 const code=fs.readFileSync(path.join(root,'src/n8n',file),'utf8');
 return await vm.runInNewContext(`(async function(){${code}\n})()`,{
  Buffer,$json:items[0],$input:{all:()=>items.map(json=>({json})),first:()=>({json:items[0]})},
  $:name=>({item:{json:refs[name]},first:()=>({json:refs[name]})})
 },{timeout:1000});
}
function req(id){return {schema:'image_request.v1',id,role:id==='COVER_IMG'?'article_cover':'body_illustration',
 visual_mode:'editorial_image',archetype_id:'EDITORIAL_DIORAMA',format_preset:id==='COVER_IMG'?'linkedin_article_cover':'inline_square',
 placement:{mode:id==='COVER_IMG'?'cover_field':'after_paragraph',anchor:id==='COVER_IMG'?'':id+'段落'},
 purpose:'A distinct visual idea',scene:id+' scene',prompt:id+' compiled prompt',alt_text:id+'画面',caption:id==='COVER_IMG'?'':id+'图注',
 generation:{n:1,requested_size:id==='COVER_IMG'?'1536x1024':'1024x1024'},publication:{aspect_ratio:id==='COVER_IMG'?'16:9':'1:1'}};}
function source(count=4){return {schema:'writing_preview.v1',status:'draft',editing_status:'completed',content_id:'test:assets',story_id:'story_1',language:'zh-CN',
 article_markdown:'# 保留文章\n\n正文不因图片失败改变。',draft_markdown:'# 原稿\n\n也保留。',warnings:[],publication:{state:'NOT_PUBLISHED',url:null},
 image_request_status:count?'prepared':'skipped',image_requests:Array.from({length:count},(_,i)=>req(i?'IMG_'+i:'COVER_IMG'))};}
function upload(id){return {content:{download_url:'https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/test/'+id+'.png',path:'test/'+id+'.png',sha:'test-'+id,size:100}};}
async function normalize(r,res,actualSize){return (await run('image-asset-normalizer.js',[res],{'Split Out1':{request:r},'Generate an image':{size:actualSize??(r.role==='article_cover'?'1672x941':'1254x1254')}})).json;}
async function collect(p,assets){return (await run('image-asset-collector.js',assets,{'V2 Image Request Builder':p}))[0].json;}
test('normalizer binds each upload to the paired split request, not batch item zero',async()=>{
 const r=req('IMG_3'),a=await normalize(r,upload(r.id));
 assert.equal(a.id,'IMG_3');assert.equal(a.status,'READY');assert.equal(a.asset.url,'https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/test/IMG_3.png');
 assert.equal(a.scene,r.scene);assert.deepEqual(plain(a.placement),r.placement);assert.equal(a.caption,r.caption);
});
test('generation, upload and missing-url failures become one failed asset, with no raw secret',async()=>{
 for(const bad of [{error:{message:'private-token'}},{success:false,status:400},{success:true,status:200,data:{}}]){
  const a=await normalize(req('IMG_1'),bad);assert.equal(a.status,'FAILED');assert.equal(a.asset,null);
  assert.ok(!JSON.stringify(a).includes('private-token'));
 }
});
test('response-reported dimensions override requested sizes (cover and body)',async()=>{
 const cover=await normalize(req('COVER_IMG'),upload('COVER_IMG'),'1672x941');
 const body=await normalize(req('IMG_1'),upload('IMG_1'),'1254x1254');
 assert.equal(cover.status,'READY');assert.equal(cover.asset.width,1672);assert.equal(cover.asset.height,941);
 assert.equal(cover.asset.geometry_status,'PASS');assert.equal(body.status,'READY');assert.equal(body.asset.width,1254);assert.equal(body.asset.geometry_status,'PASS');
});
test('geometry mismatch is reported, not claimed cropped',async()=>{
 const a=await normalize(req('COVER_IMG'),upload('COVER_IMG'),'1536x1024');
 assert.equal(a.status,'GEOMETRY_WARNING');assert.equal(a.asset.width,1536);assert.equal(a.asset.geometry_status,'MISMATCH');
});
test('collector retains any count and reorders by ID, not transport order',async()=>{
 for(const n of [1,2,4]){
  const p=source(n),before=JSON.stringify(p),a=await Promise.all(p.image_requests.map(r=>normalize(r,upload(r.id))));
  const x=await collect(p,a.reverse());assert.equal(x.image_generation_status,'completed');assert.equal(x.image_assets.length,n);
  assert.deepEqual(plain(x.image_assets.map(a=>a.id)),p.image_requests.map(r=>r.id));
  assert.equal(x.article_markdown,p.article_markdown);assert.equal(x.draft_markdown,p.draft_markdown);assert.equal(JSON.stringify(p),before);
 }
});
test('partial and all-failed batches return text and exact failed IDs',async()=>{
 const p=source(2),success=await normalize(req('IMG_1'),upload('IMG_1')),failed=await normalize(req('COVER_IMG'),{error:'test'});
 const partial=await collect(p,[failed,success]);assert.equal(partial.image_generation_status,'partial');
 assert.deepEqual(plain(partial.image_failures),['COVER_IMG']);assert.equal(partial.article_markdown,p.article_markdown);
 const all=await collect(p,[failed,await normalize(req('IMG_1'),{error:'test'})]);
 assert.equal(all.image_generation_status,'failed');assert.equal(all.draft_markdown,p.draft_markdown);
});
test('zero requests return the preview without inventing an asset or making it disappear',async()=>{
 const p=source(0),x=await collect(p,[p]);assert.equal(x.image_generation_status,'skipped');assert.deepEqual(plain(x.image_assets),[]);
 assert.equal(x.article_markdown,p.article_markdown);assert.equal(x.publication.state,'NOT_PUBLISHED');
});
test('missing, duplicate or mismatched assets cannot silently cross-bind',async()=>{
 const p=source(2),a=await normalize(req('COVER_IMG'),upload('COVER_IMG'));
 const x=await collect(p,[a]);assert.equal(x.image_generation_status,'partial');assert.deepEqual(plain(x.image_failures),['IMG_1']);
 const bad={...a,scene:'different'};const y=await collect(p,[bad,a]);assert.equal(y.image_generation_status,'failed');assert.equal(y.article_markdown,p.article_markdown);
});
test('binary conversion rejects missing payload; valid PNG stays identical',async()=>{
 await assert.rejects(run('image-binary.js',[{data:[]}],{'Split Out1':{request:req('IMG_2')}}),/image payload/i);
 const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1ioAAAAASUVORK5CYII=';
 const x=await run('image-binary.js',[{data:[{b64_json:png}]}],{'Split Out1':{request:req('IMG_2')}});
 assert.equal(x.binary.image.data,png);assert.equal(x.binary.image.mimeType,'image/png');assert.equal(x.binary.image.fileName,'IMG_2.png');
});
module.exports={req,source,upload,normalize,collect};
