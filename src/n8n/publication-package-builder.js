// Add a localized delivery package without discarding the original writing preview.
const p=$('V2 Article Assembler').first().json;
const raw=$input.first().json;
const kit=raw?.output && typeof raw.output==='object' ? raw.output : raw;
const a=p?.assembled_article, lang=p?.language;
const text=v=>typeof v==='string'&&v.trim().length>0;
if(p?.schema!=='writing_preview.v1'||a?.schema!=='assembled_article.v1'
   ||!['zh-CN','en-US'].includes(lang)||p.config?.language!==lang
   ||p.publication?.state!=='NOT_PUBLISHED'||!text(a.article_markdown)
   ||!Array.isArray(a.body_images)) throw new Error('Package: unpublished assembled preview required');
// Coarse script checks flag obvious cross-language accidents, not semantic language detection.
const localized=s=>text(s)&&(lang==='zh-CN'?/\p{Script=Han}/u.test(s):!/[\p{Script=Han}]/u.test(s)&&/[A-Za-z]/.test(s));
const issues=[];
const h1=(a.article_markdown.match(/^#\s+(.+)$/m)||[])[1];
if(!localized(a.article_title)||a.article_title!==p.article_title||h1!==a.article_title)issues.push('article_title_language_or_identity');
for(const img of [a.cover_image,...a.body_images].filter(Boolean)){
 if(!localized(img.alt_text))issues.push('image_alt_language:'+img.id);
 // A standalone cover has no displayed caption; any supplied cover caption must be localized.
 if((img.id!=='COVER_IMG'||text(img.caption))&&!localized(img.caption))issues.push('image_caption_language:'+img.id);
}
const validKit=!raw.error&&kit?.schema==='social_kit.v1'&&kit.language===lang
 &&['seo_title','seo_description','linkedin_post'].every(k=>localized(kit[k]))
 &&kit.seo_title.length<=58&&kit.seo_description.length<=158
 &&Array.isArray(kit.hashtags)&&kit.hashtags.length===4&&new Set(kit.hashtags).size===4
 &&kit.hashtags.every(t=>typeof t==='string'&&/^#[\p{L}\p{N}_]+$/u.test(t)&&!(lang==='en-US'&&/\p{Script=Han}/u.test(t)));
if(!validKit)issues.push('social_kit_failed_or_wrong_language');
const social=validKit?{...kit,linkedin_post_with_hashtags:kit.linkedin_post+'\n\n'+kit.hashtags.join(' ')}:null;
const warnings=[...new Set([...(p.warnings||[]),...issues])];
const stem=(p.content_id+'-'+p.story_id).replace(/[^A-Za-z0-9_-]/g,'_');
return [{json:{...p,social_kit_status:validKit?'completed':'failed',social_kit:social,
 publication_package:{schema:'publication_package.v1',status:issues.length?'REVIEW_REQUIRED':'DRAFT',
  content_id:p.content_id,story_id:p.story_id,story_mode:p.story_mode,language:lang,platform:p.config.content_type,
  article:{title:a.article_title,filename:stem+'-'+lang+'.md',markdown:a.article_markdown},
  cover_image:a.cover_image,body_images:a.body_images,social_kit:social,
  localization_check:'script_only',delivery_issues:issues,publication:{state:'NOT_PUBLISHED',url:null},warnings},
 warnings},pairedItem:{item:0}}];
