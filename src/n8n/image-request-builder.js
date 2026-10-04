// Prepare all requests in one preview. Splitting belongs at the I/O boundary.
// No network call, creative change, or generated-asset claim.
const rows = $input.all();
if (rows.length !== 1) throw new Error('Image requests: expected one preview');
const preview = rows[0].json;
if (preview.schema !== 'writing_preview.v1' || !preview.content_id
    || typeof preview.article_markdown !== 'string' || !preview.article_markdown.trim()
    || preview.publication?.state !== 'NOT_PUBLISHED') throw new Error('Image requests: preview missing');
const emit = fields => [{json:{...preview,...fields},pairedItem:{item:0}}];
if (preview.visual_compilation_status !== 'completed') {
  return emit({image_request_status:'skipped',image_requests:[]});
}
const presets = {
  linkedin_article_cover:{
    generation:{n:1,requested_size:'1536x1024'},
    publication:{width:1920,height:1080,aspect_ratio:'16:9'},
    note:['EXECUTION REQUIREMENTS:','Target generation canvas: 1536x1024.',
      'The publication crop is 16:9.','Preserve all essential visual meaning inside the central safe region.',
      'Keep outer edges comparatively quiet.','Do not add readable text, labels, logos, signatures, or watermarks.'].join('\n')
  },
  inline_square:{
    generation:{n:1,requested_size:'1024x1024'},
    publication:{width:1200,height:1200,aspect_ratio:'1:1'},
    note:['EXECUTION REQUIREMENTS:','Target generation canvas: 1024x1024.',
      'The publication format is square 1:1.','Keep the central relationship immediately legible at mobile size.',
      'Preserve intentional negative space and avoid edge crowding.',
      'Do not add readable text, labels, logos, signatures, or watermarks.'].join('\n')
  }
};
try {
  const plan=preview.compiled_visual_plan;
  if (plan?.schema!=='visual_prompt_compiled.v1'||plan.status!=='PASS'
      ||plan.final_article!==preview.article_markdown||!Array.isArray(plan.images_to_generate)
      ||!plan.images_to_generate.length) throw new Error('invalid_compiled_plan');
  const requests=plan.images_to_generate.map((img,i)=>{
    const fields=['id','role','visual_mode','archetype_id','format_preset','purpose','scene','prompt','alt_text'];
    if(!img||fields.some(k=>typeof img[k]!=='string'||!img[k].trim())||typeof img.caption!=='string'
       ||!img.placement||typeof img.placement.anchor!=='string'||img.visual_mode!=='editorial_image'
       ||img.id!==(i?'IMG_'+i:'COVER_IMG')||img.role!==(i?'body_illustration':'article_cover')
       ||img.format_preset!==(i?'inline_square':'linkedin_article_cover')) throw new Error('invalid_image_task');
    const cfg=presets[img.format_preset];
    return {schema:'image_request.v1',...img,prompt:img.prompt.trim()+'\n\n'+cfg.note,
      generation:{...cfg.generation},publication:{...cfg.publication}};
  });
  return emit({image_request_status:'prepared',image_requests:requests});
} catch(error) {
  return emit({image_request_status:'failed',image_requests:[],
    warnings:[...(preview.warnings||[]),'image_request_preparation_failed']});
}
