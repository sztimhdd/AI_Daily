// Bind the generated draft to the existing Chinese editor. No review model.
const rows = $input.all();
if (rows.length !== 1) throw new Error('CN edit input: expected one draft');
const draft = rows[0].json.output;
if (typeof draft !== 'string' || !draft.trim()) throw new Error('CN edit input: draft is empty');
const context = $('Writer Invocation Gate').first().json;
if (!context?.content_id || context.writer_context?.config?.language !== 'zh-CN'
 || context.writer_brief?.schema !== 'writer_brief.v3'
 || context.writer_brief.language !== 'zh-CN'
 || context.writer_brief.story_mode !== context.story_mode) {
 throw new Error('CN edit input: Chinese writer context missing');
}
return [{json:{
 schema:'polish_input.v1', content_id:context.content_id,
 story_id:context.story_id, story_mode:context.story_mode,
 article_to_polish:draft, writer_brief:context.writer_brief,
 config:{...context.writer_context.config,
  reader_promise:context.writer_brief.article_intent.reader_change,
  editorial_instructions:context.writer_brief.editorial_instructions},
 review_issues:[], source_branch:'CN_DRAFT',
 writer_invocation_receipt:context.writer_invocation_receipt
},pairedItem:{item:0}}];
