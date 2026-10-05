// Native Execute Sub-workflow(mode=each) pairs each result/error to its input item.
// Never infer language from a title and never overwrite a successful sibling.
const expected=$('Prepare Writer Invocation').all().map(x=>x.json), rows=$input.all();
if(expected.length!==2||expected[0].task_config?.language!=='zh-CN'||expected[1].task_config?.language!=='en-US')throw new Error('Bilingual delivery: expected two language orders');
const base=expected[0],versions={},rejected=[];
for(const w of expected)if(w.content_id!==base.content_id||w.story_id!==base.story_id||w.story_mode!==base.story_mode)throw new Error('Bilingual delivery: mixed orders');
for(const row of rows){
 const pair=Array.isArray(row.pairedItem)?(row.pairedItem.length===1?row.pairedItem[0]:null):row.pairedItem;
 const w=Number.isInteger(pair?.item)?expected[pair.item]:null,p=row.json;
 if(!w){rejected.push({reason:'unpaired_result',result:p});continue;}
 const lang=w.task_config.language;
 if(versions[lang]){rejected.push({reason:'duplicate_language',language:lang,result:p});continue;}
 if(p?.error){versions[lang]={language:lang,status:'FAILED',error:p.error,publication:{state:'NOT_PUBLISHED',url:null}};continue;}
 if(p?.schema!=='writing_preview.v1'||p.content_id!==w.content_id||p.story_id!==w.story_id
    ||p.story_mode!==w.story_mode||p.language!==lang||p.publication?.state!=='NOT_PUBLISHED'
    ||(p.publication_package&&(p.publication_package.language!==lang||p.publication_package.content_id!==w.content_id))){
  rejected.push({reason:'identity_or_language_mismatch',language:lang,result:p});continue;
 }
 const pkg=p.publication_package;
 versions[lang]=pkg?{...pkg,preview:p}:{language:lang,status:'REVIEW_REQUIRED',
  article:{title:p.article_title,markdown:p.article_markdown},social_kit:null,preview:p,
  publication:{state:'NOT_PUBLISHED',url:null}};
}
for(const w of expected){const lang=w.task_config.language;if(!versions[lang])versions[lang]={language:lang,status:'FAILED',error:'missing_or_rejected_result',publication:{state:'NOT_PUBLISHED',url:null}};}
const complete=!rejected.length&&Object.values(versions).every(v=>v.status==='DRAFT'&&v.social_kit);
return [{json:{content_id:base.content_id,story_id:base.story_id,story_mode:base.story_mode,
 expected_languages:['zh-CN','en-US'],delivery_status:complete?'completed':'partial',
 versions,rejected_results:rejected,publication:{state:'NOT_PUBLISHED',url:null}},pairedItem:rows.map((_,item)=>({item}))}];
