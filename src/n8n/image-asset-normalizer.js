// One result per split request, including native generation/binary/upload errors.
const r = $('Split Out1').item.json.request;
if (r?.schema !== 'image_request.v1' || !r.id) throw new Error('Image asset: paired request missing');
const u=$json, d=u.data;
const url=d?.image?.url || d?.url || d?.display_url;
const base={...r,schema:'image_asset.v1',source_prompt:r.prompt};
if (u.error || u.success!==true || u.status!==200 || typeof url!=='string' || !/^https:\/\/[^\s]+$/.test(url)) {
  return {json:{...base,status:'FAILED',asset:null,error:'image_io_failed'}};
}
const width=Number(d.width)>0?Number(d.width):null, height=Number(d.height)>0?Number(d.height):null;
const ratio=width&&height?width/height:null;
const target=r.publication?.aspect_ratio==='16:9'?16/9:r.publication?.aspect_ratio==='1:1'?1:null;
const geometry=ratio&&target?(Math.abs(ratio-target)<=0.03?'PASS':'MISMATCH'):'UNKNOWN';
return {json:{...base,status:geometry==='MISMATCH'?'GEOMETRY_WARNING':'READY',asset:{
  url,display_url:d.display_url||url,width,height,mime:d.image?.mime||null,
  bytes:Number(d.size)>0?Number(d.size):null,geometry_status:geometry
}}};
