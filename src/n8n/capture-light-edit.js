// Keep the original draft and bind the edit to the current language, including native errors.
const c=$('Draft Ready for Edit').item.json,r=$input.first().json,d=c.draft;
if(!d||d.status!=='completed'||typeof d.markdown!=='string'||!d.markdown.trim()
 ||d.language!==c.language||d.story_mode!==c.story_mode)throw new Error('Light edit: original draft identity missing');
const candidate=typeof r.output==='string'?r.output:'';
const heads=[...candidate.matchAll(/^#\s+(.+)$/gm)],title=heads[0]?.[1]?.trim()||'';
const script=c.language==='zh-CN'?/\p{Script=Han}/u.test(title):/[A-Za-z]/.test(title)&&!/\p{Script=Han}/u.test(title);
// ponytail: simple inline HTTP links only; this does not validate factual support or every Markdown dialect.
const links=s=>[...new Set([...s.matchAll(/(?<!!)\[[^\]\n]+\]\(<?(https?:\/\/[^\s>)]+)>?(?:\s+"[^"]*")?\)/g)].map(m=>m[1]))];
const before=links(d.markdown),after=links(candidate);
const shape=candidate.trim().startsWith('# ')&&heads.length===1&&candidate.trim().split('\n').slice(1).join('\n').trim().length>0&&script;
const valid=!r.error&&shape&&(!before.length||after.length>0);
const warnings=valid?[]:[r.error?'editor_failed_original_retained':!shape?'invalid_edit_original_retained':'source_links_lost_original_retained'];
return [{json:{...c,preview:{schema:'writing_preview.v1',content_id:c.content_id,story_mode:c.story_mode,
 language:c.language,config:{language:c.language,content_type:c.content_type},status:valid?'draft':'review_required',
 article_title:valid?title:d.title,article_markdown:valid?candidate:d.markdown,draft_markdown:d.markdown,
 editing_status:valid?'completed':'failed',validation:'structure_title_script_and_nonzero_links_only',
 link_changes:{before,after,removed:before.filter(u=>!after.includes(u))},warnings,
 publication:{state:'NOT_PUBLISHED',url:null}}},pairedItem:{item:0}}];
