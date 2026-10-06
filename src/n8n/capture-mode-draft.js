// Bind this response to the current batch-of-one, not the first language of the run.
const c=$('Draft Language Loop').item.json, r=$input.first().json;
const markdown=typeof r.output==='string'?r.output:'';
const heads=[...markdown.matchAll(/^#\s+(.+)$/gm)],title=heads[0]?.[1]?.trim()||'';
const body=markdown.trim().split('\n').slice(1).join('\n').trim();
const script=c.language==='zh-CN'?/\p{Script=Han}/u.test(title):/[A-Za-z]/.test(title)&&!/\p{Script=Han}/u.test(title);
const valid=!r.error&&markdown.trim().startsWith('# ')&&heads.length===1&&body.length>0&&script;
const error=r.error?(typeof r.error==='string'?r.error:r.error.message||JSON.stringify(r.error)):
 valid?null:'Writer returned empty, malformed or wrong-language title';
return [{json:{...c,draft:{language:c.language,content_type:c.content_type,story_mode:c.story_mode,
 status:valid?'completed':'failed',title,markdown,error,validation:'structure_and_title_script_only'}},pairedItem:{item:0}}];
