// Local interface tests only. Counts are fixtures, not editorial quotas.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {preview,plan}=require('./visual-planning.test.cjs');
const root=path.join(__dirname,'../..');
function runFile(file,x){const code=fs.readFileSync(path.join(root,'src/n8n',file),'utf8');return vm.runInNewContext(`(function(){${code}\n})()`,{$input:{all:()=>[{json:x}],first:()=>({json:x})}},{timeout:1000})[0].json;}
function fixture(n){const p=preview(), tasks=plan(n).images_to_generate;return {...p,visual_planning_status:'completed',visual_plan:{schema:'visual_plan_validated.v1',status:'PASS',source_plan_schema:'visual_plan.v2',final_article:p.article_markdown,cover_image:tasks[0],body_images:tasks.slice(1),images_to_generate:tasks,counts:{total:tasks.length,cover:1,body:n,archetypes:1},archetypes_used:['SATIRIST_PEN_INK']}};}
const compile=x=>runFile('visual-prompt-compiler.js',x);
const requests=x=>runFile('image-request-builder.js',x);
const clean=x=>JSON.parse(JSON.stringify(x));
for(const n of [0,1,3])test(`cover plus ${n} body images reach requests unchanged`,()=>{
 const input=fixture(n),before=JSON.stringify(input),c=compile(input),out=requests(c);
 assert.equal(c.visual_compilation_status,'completed');assert.equal(out.image_request_status,'prepared');
 assert.equal(out.image_requests.length,n+1);assert.equal(out.article_markdown,input.article_markdown);
 assert.equal(out.draft_markdown,input.draft_markdown);assert.equal(out.publication.state,'NOT_PUBLISHED');
 assert.equal(out.content_id,input.content_id);assert.equal(JSON.stringify(input),before);
 for(const [i,r] of out.image_requests.entries()){
  const original=input.visual_plan.images_to_generate[i];
  for(const k of ['id','role','scene','caption','alt_text','archetype_id','format_preset'])assert.equal(r[k],original[k]);
  assert.deepEqual(clean(r.placement),original.placement);assert.ok(r.prompt.includes(original.scene));
  assert.equal(r.schema,'image_request.v1');assert.equal(r.generation.n,1);
  assert.equal(r.generation.requested_size,i?'1024x1024':'1536x1024');
 }
});
test('failed planning has zero requests and preserves the preview',()=>{
 const p={...fixture(1),visual_planning_status:'failed',visual_plan:null,warnings:['invalid_body_anchor']};
 const x=requests(compile(p));assert.equal(x.image_request_status,'skipped');assert.equal(x.image_requests.length,0);
 assert.equal(x.article_markdown,p.article_markdown);assert.deepEqual(clean(x.warnings),p.warnings);
});
test('unknown recipe or mismatched article fails safely without leaking error text',()=>{
 for(const mutate of [p=>p.visual_plan.images_to_generate[0].archetype_id='not-an-installed-style',p=>p.visual_plan.final_article+='changed',p=>p.visual_plan.images_to_generate[1].id='IMG_8']){
  const p=fixture(1);mutate(p);const c=compile(p);assert.equal(c.visual_compilation_status,'failed');
  const x=requests(c);assert.equal(x.image_requests.length,0);assert.equal(x.article_markdown,p.article_markdown);
 }
});
test('request failure does not return a partial batch or lose either article',()=>{
 const p=fixture(1),c=compile(p);c.compiled_visual_plan.images_to_generate[1].format_preset='unimplemented';
 const x=requests(c);assert.equal(x.image_request_status,'failed');assert.equal(x.image_requests.length,0);
 assert.equal(x.article_markdown,p.article_markdown);assert.equal(x.draft_markdown,p.draft_markdown);
});
test('empty or unfinished preview is not accepted as a generation job',()=>{
 for(const c of [{article_markdown:''},{status:'review_required'},{publication:{state:'PUBLISHED'}}])assert.throws(()=>compile({...fixture(0),...c}),/Visual compiler:/);
});
module.exports={fixture,compile,requests};
