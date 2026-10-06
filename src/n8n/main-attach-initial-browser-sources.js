// Append returned source text to the same context, with no research dossier or authorization receipt.
const c=$('Brief Data Extraction').first().json, plan=c.initial_research, urls=plan.browser_urls;
if(!urls.length)return [{json:c,pairedItem:{item:0}}];
const rows=$input.all(), text=v=>typeof v==='string'&&v.trim().length>0;
const key=u=>typeof u==='string'?u.replace(/^http:/i,'https:').replace('://twitter.com/','://x.com/').replace(/#.*$/,'').replace(/\/$/,''):'';
const materials=c.materials.map(s=>({...s})),images=[...(c.image_candidates||[])],links=[...(c.source_links||[])],errors=[];
let count=0;
for(let i=0;i<urls.length;i++){
 const url=urls[i],row=rows.find(r=>(Array.isArray(r.pairedItem)?r.pairedItem[0]:r.pairedItem)?.item===i);
 let r=null, error=row?.json?.error?String(row.json.error.message||row.json.error):null;
 try{const value=row?.json?.output??row?.json?.result??row?.json;r=typeof value==='string'?JSON.parse(value.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim()):value;}catch{error=error||'Browser returned invalid JSON';}
 const ok=!error&&['completed','partial'].includes(r?.status)&&text(r.text)&&key(r.source_url)===key(url);
 if(!ok)error=error||r?.error||'Missing, empty or mismatched browser result';
 else if(r.status==='partial')error=r.error||'Only partial source text was visible';
 if(error)errors.push({url,error:String(error)});
 let n=materials.findIndex(s=>key(s.origin_url||s.url)===key(url));
 if(n<0){n=materials.length;materials.push({source:'browser',url,title:ok?r.title||'':'',snippet:''});}
 if(ok||!text(materials[n].retrieval?.raw_content))materials[n].retrieval={phase:'initial',method:'browser',requested_url:url,url:ok?r.source_url:url,
  status:ok?(r.status==='completed'?'body_returned':'partial_body'):'failed',raw_content:ok?r.text:'',
  author:ok?r.author||'':'',published_at:ok?r.published_at||'':'',error:error||null,retrieved_at:new Date().toISOString()};
 if(!ok)continue;
 count++;
 for(const u of Array.isArray(r.reference_links)?r.reference_links:[])if(typeof u==='string'&&/^https?:\/\/[^\s]+$/i.test(u)&&!links.some(x=>x.url===u&&x.source_url===r.source_url))links.push({url:u,source_url:r.source_url,label:''});
 for(const u of Array.isArray(r.image_urls)?r.image_urls:[])if(typeof u==='string'&&/^https?:\/\/[^\s]+$/i.test(u)&&!images.some(x=>x.url===u&&x.source_url===r.source_url))images.push({url:u,source_url:r.source_url,source_title:r.title||'',alt_text:'',kind:'source_image',status:'unreviewed'});
}
const total=plan.body_count+count,status=total?((plan.errors||[]).length||errors.length||plan.search_error?'partial':'completed'):'failed';
return [{json:{...c,materials,image_candidates:images,source_links:links,
 initial_research:{...plan,body_count:total,browser_body_count:count,browser_errors:errors,status},
 stage:total?'initial_research_ready':'initial_research_failed'},pairedItem:rows.map((_,item)=>({item}))}];

