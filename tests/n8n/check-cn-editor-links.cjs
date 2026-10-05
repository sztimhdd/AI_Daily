// One saved-sample regression check, not a production gate or semantic fact checker.
// Usage: node tests/n8n/check-cn-editor-links.cjs article.md
const assert = require('node:assert/strict');
const fs = require('node:fs');
const required = [
 'https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter',
 'https://openrouter.ai/blog/announcements/openrouter-is-joining-stripe',
 'https://techcrunch.com/2026/08/19/stripe-didnt-really-buy-openrouter-because-of-the-singularity/',
 'https://www.bloomberg.com/news/articles/2026-08-16/stripe-nears-deal-to-buy-ai-firm-openrouter-for-over-7-billion'
];
function check(article) {
 // ponytail: ordinary inline links used by this saved sample, not a full Markdown parser.
 const urls = [...article.matchAll(/(?<!!)\[[^\]\n]+\]\(<?(https?:\/\/[^\s<>]+?)>?\)/g)].map(m => m[1]);
 const missing = required.filter(url => !urls.includes(url));
 assert.deepEqual(missing, [], 'Retained factual passages lost their source links');
 assert.equal((article.match(/^#\s+\S.*$/gm) || []).length, 1, 'Expected one article title');
 return { required: required.length, retained: required.length, source_links: urls.length };
}
module.exports = { check };
if (require.main === module) {
 if (!process.argv[2]) throw new Error('Pass the saved article Markdown path');
 console.log(JSON.stringify(check(fs.readFileSync(process.argv[2], 'utf8'))));
}
