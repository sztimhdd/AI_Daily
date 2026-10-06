const ctx=$('Attach Initial Browser Sources').first().json;
const row=$input.first().json;
const text=v=>typeof v==='string'&&v.trim().length>0;
const failContext=(kind,detail)=>[{json:{...ctx,story_mode:null,story_direction:null,
  stage:'story_mode_review_required',story_mode_error:{kind,detail:String(detail||'')},
  publication:{state:'NOT_PUBLISHED',url:null}},pairedItem:{item:0}}];

if(ctx?.stage!=='initial_research_ready'||!text(ctx.content_id)||!text(ctx.title)
 ||!Array.isArray(ctx.materials)||!ctx.selected_topic||typeof ctx.human_instructions!=='string'
 ||!(Number(ctx.initial_research?.body_count)>0)||ctx.publication?.state!=='NOT_PUBLISHED'){
 throw new Error('Story mode decision: initial research context invalid');
}
if(row?.error)return failContext('model_error',row.error?.message||row.error);
let value=row?.text??row?.output??row?.message?.content??row;
try{
 if(typeof value==='string') value=JSON.parse(value.replace(/^\`\`\`(?:json)?\s*/i,'').replace(/\s*\`\`\`$/,'').trim());
}catch(e){return failContext('invalid_json',e.message);}
if(!value||typeof value!=='object'||Array.isArray(value))return failContext('invalid_output','object required');
const allowed=['mode','why_this_mode','working_title','reader_promise','core_judgment','story_path'];
if(Object.keys(value).some(k=>!allowed.includes(k))||allowed.some(k=>!(k in value)))return failContext('invalid_contract','exact story direction fields required');
if(!['news','deep_analysis'].includes(value.mode)||!text(value.why_this_mode)||!text(value.working_title)||!text(value.reader_promise)
 ||!Array.isArray(value.story_path)||value.story_path.length<2||value.story_path.length>6||value.story_path.some(x=>!text(x)))
 return failContext('invalid_contract','mode/title/promise/story_path invalid');
if(value.mode==='news'&&value.core_judgment!==null)return failContext('invalid_contract','News must not invent a thesis');
if(value.mode==='deep_analysis'&&!text(value.core_judgment))return failContext('invalid_contract','Deep requires a core judgment');
const direction={working_title:value.working_title.trim(),reader_promise:value.reader_promise.trim(),
 core_judgment:value.mode==='deep_analysis'?value.core_judgment.trim():null,
 story_path:value.story_path.map(x=>x.trim()),why_this_mode:value.why_this_mode.trim()};
return [{json:{...ctx,story_mode:value.mode,story_direction:direction,
 stage:value.mode==='deep_analysis'?'awaiting_narrative_approval':'story_direction_ready',
 publication:{state:'NOT_PUBLISHED',url:null}},pairedItem:{item:0}}];
