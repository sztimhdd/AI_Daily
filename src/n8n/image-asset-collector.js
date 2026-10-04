// Rejoin the batch without discarding text or demanding a successful cover.
const p=$('V2 Image Request Builder').first().json;
if(p?.schema!=='writing_preview.v1'||!Array.isArray(p.image_requests)) throw new Error('Image collector: preview missing');
const requests=p.image_request_status==='prepared'?p.image_requests:[];
const received=$input.all().map(i=>i.json);
const assets=requests.map(r=>{
  const matches=received.filter(a=>a?.schema==='image_asset.v1'&&a.id===r.id);
  const a=matches[0];
  const same=matches.length===1 && ['role','scene','archetype_id','alt_text','caption'].every(k=>a[k]===r[k])
    && JSON.stringify(a.placement)===JSON.stringify(r.placement);
  if(same && ['READY','GEOMETRY_WARNING','FAILED'].includes(a.status)
      && (a.status==='FAILED'||(typeof a.asset?.url==='string'&&/^https:\/\//.test(a.asset.url)))) return a;
  return {...r,schema:'image_asset.v1',source_prompt:r.prompt,status:'FAILED',asset:null,error:'asset_missing_or_mismatched'};
});
const failed=assets.filter(a=>a.status==='FAILED').map(a=>a.id);
const warnings=[...(p.warnings||[]),...assets.filter(a=>a.status==='GEOMETRY_WARNING').map(a=>'image_geometry_warning:'+a.id)];
if(failed.length) warnings.push('image_generation_incomplete');
return [{json:{...p,image_generation_status:!requests.length?'skipped':!failed.length?'completed':failed.length===requests.length?'failed':'partial',
  image_assets:assets,image_failures:failed,image_counts:{requested:requests.length,succeeded:requests.length-failed.length,failed:failed.length},
  warnings:[...new Set(warnings)]},pairedItem:{item:0}}];
