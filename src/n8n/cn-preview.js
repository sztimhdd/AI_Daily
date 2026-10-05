// Return readable text; an editor error must not discard a successful draft.
const input = $('V2 CN Edit Input').first().json;
const result = $input.first().json;
const draft = input.article_to_polish;
if (typeof draft !== 'string' || !draft.trim()) throw new Error('CN preview: original draft missing');
const candidate = typeof result.output === 'string' ? result.output : '';
const valid = !result.error && candidate.trim().startsWith('# ')
 && (candidate.match(/^#\s+\S.*$/gm) || []).length === 1
 && candidate.trim().split('\n').slice(1).join('\n').trim().length > 0;
const article = valid ? candidate : draft;
return [{json:{
 schema:'writing_preview.v1', status:valid ? 'draft' : 'review_required',
 content_id:input.content_id, story_id:input.story_id, story_mode:input.story_mode,
 language:input.config.language, config:input.config,
 writer_invocation_receipt:input.writer_invocation_receipt,
 article_title:(article.match(/^#\s+(.+)$/m) || [,''])[1],
 article_markdown:article, draft_markdown:draft,
 editing_status:valid ? 'completed' : 'failed',
 warnings:valid ? [] : [result.error ? 'editor_failed_original_retained' : 'invalid_edit_original_retained'],
 publication:{state:'NOT_PUBLISHED',url:null}
},pairedItem:{item:0}}];
