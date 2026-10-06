// Keep source context once and collect two drafts. A failed language never erases its sibling.
const first=$('Draft Languages').first().json, {language,content_type,...c}=first;
const drafts={},issues=[];
for(const {json:r} of $input.all()){
 const d=r?.draft,lang=d?.language;
 if(!['zh-CN','en-US'].includes(lang)||r.content_id!==c.content_id||r.story_mode!==c.story_mode
  ||r.language!==lang||d.story_mode!==c.story_mode){issues.push('draft_identity_mismatch');continue;}
 if(drafts[lang]){issues.push('duplicate_language:'+lang);continue;}
 drafts[lang]=d;
}
for(const lang of ['zh-CN','en-US'])if(!drafts[lang])drafts[lang]={language:lang,status:'failed',title:'',markdown:'',error:'Missing language result'};
const completed=Object.values(drafts).filter(d=>d.status==='completed').length;
return [{json:{...c,drafts,stage:completed===2&&!issues.length?'drafts_ready':completed?'drafts_partial':'drafts_failed',
 draft_issues:issues,publication:{state:'NOT_PUBLISHED',url:null}},pairedItem:$input.all().map((_,item)=>({item}))}];
