// One topic choice enriches the same material context. No internal authorization envelope.
const rows=$input.all(),contexts=$('Topic Discovery').all();
const fail=m=>{throw new Error('Parse Selection1: '+m);};
if(rows.length!==1||contexts.length!==1)fail('需要一份选题上下文和一份表单答复。');
const c=contexts[0].json,form=rows[0].json.data;
if(!form||typeof form!=='object'||Array.isArray(form))fail('未找到表单数据。');
if(c.stage!=='awaiting_topic_selection'||!Array.isArray(c.topics)||!c.topics.length
 ||c.topics.length>5||c.topic_count!==c.topics.length||!Array.isArray(c.materials))fail('本轮没有有效的待选题目。');
const label=`请选择要推进的选题（输入 1 至 ${c.topics.length}）`;
const raw=form.selected_topic??form[label];
if(form.selected_topic!==undefined&&form[label]!==undefined&&String(form.selected_topic).trim()!==String(form[label]).trim())fail('选题字段冲突。');
const number=typeof raw==='number'?raw:typeof raw==='string'&&/^\d+$/.test(raw.trim())?Number(raw.trim()):NaN;
if(!Number.isSafeInteger(number)||number<1||number>c.topics.length)fail('选题编号无效。');
const t=c.topics[number-1];
if(t?.selection_value!==number||t.status!=='pending'||typeof t.title!=='string'||!t.title.trim()
 ||!Array.isArray(t.source_urls)||!t.source_urls.length)fail('所选条目不是可研究选题。');
const noteLabel='这篇你最想了解什么？还有哪些方向要补充？（可选）';
const human=form.additional_research_instructions??form[noteLabel]??'';
if(typeof human!=='string')fail('补充方向必须是文字。');
if(form.additional_research_instructions!==undefined&&form[noteLabel]!==undefined&&form.additional_research_instructions!==form[noteLabel])fail('补充方向字段冲突。');
const bound=t.source_urls.map(url=>{
 const source=c.materials.find(s=>s.url===url);
 if(!source)fail('所选来源不在本轮材料中。');
 const target=source.origin_url||source.url;
 if(typeof target!=='string'||!/^https?:\/\/[^\s]+$/i.test(target))fail('原始来源网址无效。');
 return target;
});
return [{json:{...c,selected_topic:t,title:t.title,human_instructions:human,
 content_id:'url:'+encodeURIComponent(t.source_urls[0]),target_urls:[...new Set(bound)],
 stage:'initial_research',publication:{state:'NOT_PUBLISHED',url:null}},pairedItem:{item:0}}];
