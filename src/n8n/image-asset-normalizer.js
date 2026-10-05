// One GitHub upload result per split request; failed uploads return FAILED without losing the article.
const r = $('Split Out1').item.json.request;
if (r?.schema !== 'image_request.v1' || !r.id) throw new Error('Image asset: paired request missing');

const u = $json;
const url = u.content?.download_url;
const base = {...r, schema:'image_asset.v1', source_prompt:r.prompt};

if (u.error || typeof url !== 'string'
    || !/^https:\/\/raw\.githubusercontent\.com\/sztimhdd\/AI_Daily\/[^\s]+$/.test(url)) {
  return {json:{...base,status:'FAILED',asset:null,error:'image_io_failed'}};
}

const m = String(r.generation?.requested_size || '').match(/^(\d+)x(\d+)$/);
const width = m ? Number(m[1]) : null;
const height = m ? Number(m[2]) : null;
const ratio = width && height ? width / height : null;
const target = r.publication?.aspect_ratio === '16:9' ? 16/9
  : r.publication?.aspect_ratio === '1:1' ? 1 : null;
const geometry = ratio && target
  ? (Math.abs(ratio-target) <= 0.03 ? 'PASS' : 'MISMATCH')
  : 'UNKNOWN';

return {json:{...base,
  status: geometry === 'MISMATCH' ? 'GEOMETRY_WARNING' : 'READY',
  asset:{
    url,
    display_url:url,
    github_path:u.content?.path || null,
    github_sha:u.content?.sha || null,
    width,
    height,
    mime:'image/png',
    bytes:Number(u.content?.size)>0 ? Number(u.content.size) : null,
    geometry_status:geometry
  }
}};