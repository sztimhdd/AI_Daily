// One existing research context, two publication languages. No work order or authorization wrapper.
const rows=$input.all(), c=rows[0]?.json;
const text=v=>typeof v==='string'&&v.trim().length>0;
if(rows.length!==1||c?.stage!=='writing_materials_ready'||!text(c.content_id)
 ||!['news','deep_analysis'].includes(c.story_mode)||!text(c.story_direction?.working_title)
 ||!Array.isArray(c.materials)||c.publication?.state!=='NOT_PUBLISHED')throw new Error('Draft languages: research context missing');
if(c.story_mode==='deep_analysis'&&!text(c.story_direction.core_judgment))throw new Error('Draft languages: Deep judgment missing');
if(!c.materials.some(s=>text(s.retrieval?.raw_content)))throw new Error('Draft languages: no source text');
return [['zh-CN','zhihu_longform'],['en-US','linkedin_article']].map(([language,content_type])=>({
 json:{...JSON.parse(JSON.stringify(c)),language,content_type},pairedItem:{item:0}
}));
