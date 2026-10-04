// Prompt-binding checks and reproducible editorial input. Not a readership metric.
// --payload requires the locally saved draft and fresh permission; no network calls.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const file=path.join(__dirname,'../../src/n8n/cn-line-editor.prompts.json');
function payload(article,permission){
 assert.ok(typeof article==='string'&&article.trim(),'draft required');
 assert.ok(typeof permission==='string'&&permission.trim(),'fresh permission required');
 return {schema:'polish_input.v1',article_to_polish:article,review_status:'REVISE',source_branch:'READER_FIRST_EDIT',
  config:{language:'zh-CN',content_type:'zhihu_longform',audience:'对 AI 好奇、没有相关专业背景的普通读者',
   reader_job:'看懂支付公司为何关注模型路由，以及现有用户在意的变化。',
   timeframe:'历史材料按2026年8月19日公告语境写作，不是今日跟进。',
   headline_policy:'保留报道主体和核心问题，可以缩短原标题。'},
  review_issues:[
   {location:'省钱接口段',required_fix:'删掉“省钱的必要接口”与“还没有被任何一方测量过”的无依据绝对表述。这里要讲清使用者怎样看到花费和缓存状态，不必另写一段测评免责声明。'},
   {location:'结尾与功能归属',required_fix:'Cline自身账户的账单、额度和交易记录是Cline功能，不是OpenRouter承诺保留的产品。结尾不要把两者混写；可以删去重复功能清单。将“启用价格的计算”改为自然的“价格计算功能”。'},
   {location:'来源链接',required_fix:'保留仍采用事实所需的已有链接。原研究包还提供了卖方说明 https://openrouter.ai/blog/announcements/openrouter-is-joining-stripe 与媒体分析 https://techcrunch.com/2026/08/19/stripe-didnt-really-buy-openrouter-because-of-the-singularity/ ，相应转述可使用这两个链接。'}],
  test_context:{kind:'isolated_reader_edit',source_execution:'593',permission,model_calls_allowed:true,publication_allowed:false}};
}
function render(template,input){
 return template.replace(/^=/,'').replace(/{{([\s\S]*?)}}/g,(_,expression)=>
  String(vm.runInNewContext(expression,{$json:input},{timeout:1000})));
}
module.exports={payload,render};
if(process.argv[2]==='--payload'){
 console.log(JSON.stringify(payload(fs.readFileSync(process.argv[3],'utf8'),process.argv[4]),null,2));
}else test('Chinese reader editor consumes the supplied draft, uses Chinese assignment and rejects empty input',()=>{
 const p=JSON.parse(fs.readFileSync(file,'utf8'));
 const article='# 测试标题\n\n同一份初稿，不是重新研究。';
 const input=payload(article,'fixture-only: not execution permission');
 const before=JSON.stringify(input), output=render(p.text,input);
 assert.ok(output.includes(article),'draft text must arrive unchanged');
 assert.ok(output.includes('普通读者')&&output.includes('省钱接口段'));
 assert.match(p.options.systemMessage,/中文/);
 assert.doesNotMatch(p.text,/English line-editing|V2 EN Lead Writer/);
 assert.throws(()=>render(p.text,{article_to_polish:'   '}),/article_to_polish is empty/);
 assert.equal(JSON.stringify(input),before);
});
