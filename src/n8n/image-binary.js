// Decode one response. Native error output bypasses upload and rejoins the loop.
const r = $('Split Out1').item.json.request;
const b64 = $json.data?.[0]?.b64_json;
if (!r?.id || typeof b64 !== 'string' || !b64.length || !/^[A-Za-z0-9+/\r\n]+={0,2}$/.test(b64)) {
  throw new Error('Image binary: missing image payload');
}
const format = String($json.output_format || 'png').toLowerCase().replace('jpg','jpeg');
const mime = {png:'image/png',jpeg:'image/jpeg',webp:'image/webp'}[format];
if (!mime || !Buffer.from(b64,'base64').length) throw new Error('Image binary: invalid image payload');
return {json:{id:r.id},binary:{image:{data:b64,mimeType:mime,fileName:r.id+'.'+format}}};
