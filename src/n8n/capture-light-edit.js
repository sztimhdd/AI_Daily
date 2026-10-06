// Keep the original draft and bind the edit to the current language, including native errors.
const c=$('Draft Ready for Edit').item.json,r=$input.first().json,d=c.draft;
if(!d||d.status!=='completed'||typeof d.markdown!=='string'||!d.markdown.trim()
 ||d.language!==c.language||d.story_mode!==c.story_mode)throw new Error('Light edit: original draft identity missing');
const candidate=typeof r.output==='string'?r.output:'';
const heads=[...candidate.matchAll(/^#\s+(.+)$/gm)],title=heads[0]?.[1]?.trim()||'';
const script=c.language==='zh-CN'?/\p{Script=Han}/u.test(title):/[A-Za-z]/.test(title)&&!/\p{Script=Han}/u.test(title);
// Reuse the existing inline HTTP-link parser. Exact URL-set preservation, not a source-support audit.
const links=s=>[...new Set([...s.matchAll(/(?<!!)\[[^\]\n]+\]\(<?(https?:\/\/[^\s>)]+)>?(?:\s+"[^"]*")?\)/g)].map(m=>m[1]))];
const before=links(d.markdown),after=links(candidate),removed=before.filter(u=>!after.includes(u));
const shape=candidate.trim().startsWith('# ')&&heads.length===1&&candidate.trim().split('\n').slice(1).join('\n').trim().length>0&&script;
const valid=!r.error&&shape&&removed.length===0;
const warnings=[];
if(r.error)warnings.push('editor_failed_original_retained');
else if(!shape)warnings.push('invalid_edit_original_retained');
if(removed.length)warnings.push('source_urls_missing_original_retained');
const reason=r.error?'model_error':!shape?'invalid_output':removed.length?'source_urls_missing':null;
const message=r.error?(typeof r.error==='string'?r.error:r.error.message||JSON.stringify(r.error)):
 !shape?'Editor returned empty, malformed or wrong-language title':removed.length?'Editor removed original source URLs':null;
return [{json:{...c,preview:{schema:'writing_preview.v1',content_id:c.content_id,story_mode:c.story_mode,
 language:c.language,config:{language:c.language,content_type:c.content_type},status:valid?'draft':'review_required',
 article_title:valid?title:d.title,article_markdown:valid?candidate:d.markdown,draft_markdown:d.markdown,
 editor_candidate_markdown:candidate,editing_error:valid?null:{reason,message,missing_source_urls:removed},
 editing_status:valid?'completed':'failed',validation:'structure_title_script_and_all_inline_source_urls_only',
 link_changes:{before,after,removed},warnings,
 publication:{state:'NOT_PUBLISHED',url:null}}},pairedItem:{item:0}}];
