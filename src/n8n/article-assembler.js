// Insert uploaded illustrations; retain the original preview and keep the cover separate.
const rows = $input.all();
const p = rows[0]?.json;
if (rows.length !== 1 || p?.schema !== 'writing_preview.v1' || !p.content_id
    || typeof p.article_markdown !== 'string' || !p.article_markdown.trim()
    || p.publication?.state !== 'NOT_PUBLISHED' || !Array.isArray(p.image_assets)) {
  throw new Error('Assembly: expected an unpublished preview with image assets');
}
const text = p.article_markdown, images = p.image_assets;
const warnings = [...(p.warnings || [])], skipped = [], inserts = [];
const seenAnchors = new Set(), seenUrls = new Set();
const newline = text.includes('\r\n') ? '\r\n' : '\n';
const escapeText = s => s.replace(/[\r\n]+/g, ' ').replace(/[\\`*_[\]<>]/g, '\\$&').trim();
let cover = null;
// Same ordinary-paragraph rules as Visual Plan Validator; no new Markdown dependency.
const paragraphs = [];
let block = [], fence = null;
const flush = () => {
  if (block.length && block.every(l => !/^(?: {4}| {0,3}(?:#{1,6}\s|>|[-*+]\s|\d+[.)]\s|\||<|(?:[-*_]\s*){3,}$))/.test(l))) paragraphs.push(block.join('\n').replace(/\r$/, ''));
  block = [];
};
for (const line of text.split('\n')) {
  const f = line.match(/^ {0,3}(`{3,}|~{3,})/);
  if (f) {
    flush();
    if (!fence) fence = {char:f[1][0], length:f[1].length};
    else if (f[1][0] === fence.char && f[1].length >= fence.length && new RegExp('^ {0,3}'+fence.char+'{'+fence.length+',}\\s*$').test(line)) fence = null;
    continue;
  }
  if (fence) continue;
  if (!line.trim()) flush(); else block.push(line);
}
flush();
for (const img of images) {
  const id = /^(COVER_IMG|IMG_[1-9][0-9]*)$/.test(img?.id) ? img.id : 'unknown';
  const skip = () => { skipped.push(id); warnings.push('assembly_image_skipped:'+id); };
  const url = img?.asset?.url;
  // ponytail: small per-article array; index IDs only if large batches warrant it.
  if (id === 'unknown' || images.filter(x => x?.id === id).length !== 1
      || img.schema !== 'image_asset.v1' || !['READY','GEOMETRY_WARNING'].includes(img.status)
      || typeof url !== 'string' || !/^https:\/\/[^\s<>\\]+$/.test(url)
      || typeof img.alt_text !== 'string' || !img.alt_text.trim()
      || typeof img.caption !== 'string') { skip(); continue; }
  if (img.status === 'GEOMETRY_WARNING') warnings.push('image_geometry_warning:'+id);
  const metadata = {id, url, alt_text:img.alt_text, caption:img.caption,
    width:img.asset.width ?? null, height:img.asset.height ?? null,
    mime:img.asset.mime ?? null, geometry_status:img.asset.geometry_status ?? 'UNKNOWN'};
  if (id === 'COVER_IMG') {
    if (img.role !== 'article_cover' || img.placement?.mode !== 'cover_field') { skip(); continue; }
    cover = metadata;
    continue;
  }
  const anchor = img.placement?.anchor;
  const at = typeof anchor === 'string' && anchor ? text.indexOf(anchor) : -1;
  const coverUrl = images.find(x => x?.id === 'COVER_IMG')?.asset?.url;
  if (img.role !== 'body_illustration' || img.placement?.mode !== 'after_paragraph'
      || at < 0 || paragraphs.filter(v => v === anchor).length !== 1
      || text.indexOf(anchor, at + anchor.length) !== -1 || seenAnchors.has(anchor)
      || seenUrls.has(url) || url === coverUrl) { skip(); continue; }
  seenAnchors.add(anchor); seenUrls.add(url);
  const imageMarkdown = '!['+escapeText(img.alt_text)+'](<'+url+'>)';
  const caption = escapeText(img.caption);
  const insertion = newline+newline+imageMarkdown+(caption ? newline+newline+'*'+caption+'*' : '');
  inserts.push({...metadata, placement_mode:'after_paragraph', anchor,
    offset:at+anchor.length, markdown_insertion:insertion});
}
// Original offsets avoid replacement-string expansion ($&, $') and anchor re-matching.
inserts.sort((a,b) => a.offset-b.offset);
let markdown = text;
for (const img of [...inserts].reverse()) markdown = markdown.slice(0,img.offset)+img.markdown_insertion+markdown.slice(img.offset);
const finalWarnings = [...new Set(warnings)];
return [{json:{...p, assembly_status:skipped.length ? 'partial' : 'completed',
  assembly_skipped_images:[...new Set(skipped)], warnings:finalWarnings,
  assembled_article:{schema:'assembled_article.v1', status:finalWarnings.length ? 'READY_WITH_WARNINGS' : 'READY',
    article_title:p.article_title || (text.match(/^#\s+(.+)$/m)||[,''])[1],
    article_markdown:markdown, cover_image:cover,
    body_images:inserts.map(({offset,...img}) => img), counts:{body_images_inserted:inserts.length}, warnings:finalWarnings}
},pairedItem:{item:0}}];
