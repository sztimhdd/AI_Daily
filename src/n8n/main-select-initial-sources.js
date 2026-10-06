// Add retrieval targets to the selected context. Fixed services do not need an LLM router.
const c=$('Parse Selection1').first().json, search=$input.first().json;
const text=v=>typeof v==='string'&&v.trim().length>0;
const valid=u=>typeof u==='string'&&/^https?:\/\/[^\s]+$/i.test(u);
const key=u=>u.replace(/#.*$/,'').replace(/\/$/,'');
if(c?.stage!=='initial_research'||!text(c.title)||!Array.isArray(c.materials)
 ||!Array.isArray(c.target_urls)||!c.target_urls.length||!c.target_urls.every(valid)
 ||typeof c.human_instructions!=='string')throw new Error('Initial research: selected topic and original URLs required');
const found=Array.isArray(search.web?.results)?search.web.results:[];
const selected=[...c.target_urls,...found.map(x=>x.url)].filter(valid);
const targets=[...new Map(selected.map(u=>[key(u),u])).values()].slice(0,20);
const browser=u=>/^https?:\/\/(?:[^/]+\.)?(?:x\.com|twitter\.com|zhihu\.com|bloomberg\.com|wsj\.com|ft\.com|linkedin\.com)(?:[/:]|$)/i.test(u);
const urls=targets.filter(u=>!browser(u)), browser_urls=targets.filter(browser);
return [{json:{...c,initial_research:{
 search_query:c.title,search_results:found,search_error:search.error?(typeof search.error==='string'?search.error:JSON.stringify(search.error)):null,
 urls,browser_urls,requested_at:new Date().toISOString()
}},pairedItem:{item:0}}];

