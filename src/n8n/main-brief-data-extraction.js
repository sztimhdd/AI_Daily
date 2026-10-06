// Keep the returned source text, not a new LLM summary or per-claim dossier.
const c=$('Select Initial Sources').first().json, raw=$input.first().json;
const plan=c.initial_research;
const text=v=>typeof v==='string'&&v.trim().length>0;
const key=u=>typeof u==='string'?u.replace(/#.*$/,'').replace(/\/$/,''):'';
const error=v=>typeof v==='string'?v:JSON.stringify(v);
const usefulImage=u=>{
 if(typeof u!=='string'||!/^https?:\/\/[^\s]+$/i.test(u))return false;
 const path=u.toLowerCase().split(/[?#]/)[0];
 if(/\.(?:svg|ico)$/.test(path))return false;
 return !/(?:^|[\/_.-])(?:favicon|logo|icon|icons|avatar|sprite|emoji|badge|spacer|pixel|tracking|analytics)(?:[\/_.-]|$)/.test(path);
};
const results=Array.isArray(raw.results)?raw.results:[],failed=Array.isArray(raw.failed_results)?raw.failed_results:[];
const materials=c.materials.map(s=>({...s})), images=(c.image_candidates||[]).map(s=>({...s})), errors=[];
const links=(c.source_links||[]).map(s=>({...s}));
const fetched_at=new Date().toISOString();
let body_count=0;
for(const url of plan.urls){
 const r=results.find(x=>key(x.url)===key(url)&&text(x.raw_content));
 const f=failed.find(x=>key(x.url)===key(url));
 const search=plan.search_results.find(x=>key(x.url)===key(url));
 let i=materials.findIndex(s=>key(s.origin_url||s.url)===key(url));
 if(i<0){i=materials.length;materials.push({source:'web_search',url,title:search?.title||r?.title||'',snippet:search?.description||'',published_at:search?.page_age||null});}
 const msg=r?null:error(f?.error||raw.error||'No non-empty source text returned');
 materials[i].retrieval={phase:'initial',method:'tavily_extract',url,status:r?'body_returned':'failed',raw_content:r?r.raw_content:'',error:msg,retrieved_at:fetched_at};
 if(!r){errors.push({url,error:msg});continue;}
 body_count++;
 if(c.target_urls.some(u=>key(u)===key(url))){
  for(const m of r.raw_content.matchAll(/(?<!!)\[([^\]\n]+)\]\(<?(https?:\/\/[^\s>)]+)>?(?:\s+"[^"]*")?\)/g)){
   if(m[1].startsWith('![')||links.some(x=>key(x.url)===key(m[2])&&x.source_url===url))continue;
   links.push({url:m[2],source_url:url,label:m[1]});
  }
 }
 const candidates=Array.isArray(r.images)?[...r.images]:[];
 for(const m of r.raw_content.matchAll(/!\[([^\]]*)\]\(<?(https?:\/\/[^\s>)]+)>?(?:\s+"[^"]*")?\)/g))candidates.push({url:m[2],alt_text:m[1]});
 for(const x of candidates){
  const image_url=typeof x==='string'?x:x?.url;
  if(!usefulImage(image_url))continue;
  const existing=images.find(v=>v.url===image_url&&v.source_url===url);
  if(existing){if(!existing.alt_text&&typeof x==='object'&&text(x.alt_text))existing.alt_text=x.alt_text;continue;}
  images.push({url:image_url,source_url:url,source_title:materials[i].title||'',alt_text:typeof x==='object'?x.alt_text||'':'',status:'unreviewed',kind:'source_image'});
 }
}
const status=body_count?(errors.length||plan.search_error||plan.browser_urls.length?'partial':'completed'):(plan.browser_urls.length?'browser_pending':'failed');
return [{json:{...c,materials,image_candidates:images,source_links:links,
 initial_research:{...plan,body_count,errors,status,completed_at:fetched_at},
 stage:body_count?'initial_research_ready':plan.browser_urls.length?'initial_research_browser_pending':'initial_research_failed',
 publication:{state:'NOT_PUBLISHED',url:null}
},pairedItem:{item:0}}];
