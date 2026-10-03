// Reduced, public-material regression fixture derived from mother execution 557.
// Not a raw export, independent news verification, or formal HITL approval.
// Keep exact identities, title/promise, selected quote text and important edge cases.
// Source notes/support arrays and unrelated workflow fields are intentionally omitted.
const clone = x => JSON.parse(JSON.stringify(x));
const content_id = 'test:full-source-dossier-20261002-r2';
const title = 'Stripe 拟收购 OpenRouter：模型路由为何进入支付公司的版图，现有用户会怎样？';
const promise = '读者能弄清这笔交易到了哪一步、OpenRouter 的模型路由具体有什么用、双方各自如何解释结合，以及现有用户的使用方式与公司承诺之间有哪些直接联系。';
const human = '按公告当日材料研究，保留各方原话与归属；不要把签约写成交割完成。';
const source = (ref,url,title,source_kind='primary',retrieval_status='body_fetched') => ({ref,url,title,source_kind,retrieval_status,claim_eligible:retrieval_status!=='title_only'});
const sources = [
 source('initial:S01','https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter','Stripe agrees to acquire OpenRouter to help businesses optimize token routing and usage'),
 source('initial:S02','https://openrouter.ai/blog/announcements/openrouter-is-joining-stripe','OpenRouter is Joining Stripe'),
 source('initial:S03','https://techcrunch.com/2026/08/19/stripe-didnt-really-buy-openrouter-because-of-the-singularity/','TechCrunch 关于 Stripe 拟收购 OpenRouter 的报道','reporting'),
 source('initial:S04','https://www.bloomberg.com/news/articles/2026-08-16/stripe-nears-deal-to-buy-ai-firm-openrouter-for-over-7-billion','Stripe Clinches Over $7 Billion Deal to Buy AI Firm OpenRouter','reporting','partial_body'),
 source('initial:S05','https://quasa.io/insights/stripe-buys-openrouter-model-choice-stays-for-now','Stripe Agrees to Buy OpenRouter; Model Choice Stays','reporting','title_only'),
 source('initial:S06','https://aitoolsreview.co.uk/insights/stripe-openrouter-acquisition','Stripe Buys OpenRouter: The Real Numbers (September 2026) - AIToolsReview','reporting','title_only'),
 source('supplementary:S01','https://cline.bot/blog/cline-3-8-0-workflow-integration-account-management-and-provider-optimization','Cline 3.8.0: Workflow Integration, Account Management, and Provider Optimization'),
 source('supplementary:S02','https://cline.bot/blog/cline-v3-14-improved-gemini-caching-newrule-command-enhanced-checkpoints-key-updates','Cline v3.14: Improved Gemini Caching, /newrule Command, Enhanced Checkpoints & Key Updates')
];
const claim = (ref,statement,source_refs,status='attributed') => ({ref,statement,source_refs,status});
const claims = [
 claim('initial:C01','Stripe 在 2026 年 8 月 19 日公告中宣布已同意收购 OpenRouter；应写为达成收购协议，而不是交割完成。',['initial:S01'],'confirmed'),
 claim('initial:C02','Stripe 将交易解释为同时改善 AI 企业收入、效能与成本：它称 OpenRouter 按任务复杂度、价格、速度和可靠性动态路由请求，并列举 NVIDIA、Zoom、Lovable 为用户。',['initial:S01']),
 claim('initial:C03','OpenRouter 表示交易仍须满足惯常交割条件，预计未来数周完成；这只是公告时的预期，并非已经交割的证据。',['initial:S02']),
 claim('initial:C04','OpenRouter 向现有用户承诺使命、名称、产品、路线图和现有集成不变，并称模型平等与中立承诺不会因模型、供应商或母公司而改变。',['initial:S02']),
 claim('initial:C05','OpenRouter 解释选择 Stripe 是为了在不牺牲使命、中立性和市场领先地位的前提下更快推进业务，并特别强调 Stripe 的客户网络、互联网企业增长数据及反欺诈与滥用经验。',['initial:S02']),
 claim('initial:C06','独立报道强调经济位置变化：Bloomberg 将交易联系到企业寻找低成本 AI 方案的需求；TechCrunch 则分析 Stripe 从收入管理延伸到 AI 支出管理，并引用分析师对 AI 资本流动的判断。',['initial:S03','initial:S04']),
 claim('supplementary:C01','2025 年 3 月 23 日的 Cline 3.8.0 发布记录说明，应用内新增底层提供商路由排序：可按吞吐量、价格或延迟选择优先级，默认方式兼顾价格与可用性。这是跨提供商路由的具体集成记录，而非仅列出支持的模型。',['supplementary:S01']),
 claim('supplementary:C02','Cline 3.8.0 记录了两项不同的成本可见性更新：Cline 账户可在扩展内查看账单、额度消耗和交易历史，减少离开 VS Code 查询的需要；团队另称 OpenRouter 的 usage_details 功能使成本追踪更可靠。后者不是独立验证结果。',['supplementary:S01']),
 claim('supplementary:C03','2025 年 5 月 3 日的 Cline v3.14 发布记录称，为 OpenRouter 和内置 Cline 提供商增加 Cache UI，让使用者更清楚缓存何时处于启用状态。这里直接解决的是缓存状态可见性，而非提供节省金额或命中率统计。',['supplementary:S02']),
 claim('supplementary:C04','同一份 v3.14 记录把缓存逻辑改进和启用价格计算明确归于 Gemini、Vertex 提供商；不能将这些更新写成 OpenRouter 的缓存优化或价格计算改进。OpenRouter/Cline 在该段对应的是缓存界面。',['supplementary:S02'])
];
const quote = (ref,text_original,speaker,source_ref,attribution) => ({ref,text_original,speaker,source_ref,attribution,language:'en'});
const quotations = [
 quote('initial:QT01','Stripe is building the economic infrastructure for AI, and together with OpenRouter we’ll help businesses maximize profitability by routing their requests intelligently and spending their tokens efficiently.','Patrick Collison','initial:S01','Stripe 官方公告引用其联合创始人兼 CEO Patrick Collison 的讲话，并非本研究采访。'),
 quote('initial:QT02','There are few companies on earth we would have considered selling to; our mission, our neutrality, and our lead in the market make the story for independence strong. We would only join a company if we thought we could do more together, faster, without compromising any of them.','Alex, Chris, Louis, and the OpenRouter team','initial:S02','OpenRouter 博文中团队自己的书面说明，全文署名为 Alex, Chris, Louis, and the OpenRouter team；不将集体声明单独归给某一人。'),
 quote('initial:QT03','is Stripe’s deliberate attempt to embed itself into the middle of capital flows in the AI era,','Franco Granda','initial:S03','TechCrunch 报道引用 PitchBook 研究分析师 Franco Granda 的判断，并非本研究采访。'),
 quote('supplementary:QT01',"One of the most powerful additions in 3.8.0 is the new 'Sort underlying provider routing' setting. This feature gives you more control over how Cline and OpenRouter route your requests across different AI providers.",'Nick Baumann','supplementary:S01','Nick Baumann 署名发表于 Cline 官方博客的书面发布说明；不是本刊采访。'),
 quote('supplementary:QT02',"We know accurate cost tracking and efficient model usage are crucial. While Gemini's context caching offers potential savings, ensuring its effectiveness and providing clear visibility has been an ongoing effort.",'Nick Baumann','supplementary:S02','Nick Baumann 署名发表于 Cline 官方博客的书面说明，谈的是 Gemini 缓存背景；不是对 OpenRouter 节省效果的证言。')
];
const initial={sources:sources.slice(0,6),claims:claims.slice(0,6),quotations:quotations.slice(0,3),open_questions:[],conflicts:[]};
const extra={sources:sources.slice(6),claims:claims.slice(6),quotations:quotations.slice(3)};
const qv=n=>({collection_present:true,quotation_count:n,checked_count:n,valid:true,matching:'whitespace_only',errors:[]});
// Jobs are shortened fixture labels; reference bindings are taken from 557.
const originalProposal={working_title:title,reader_promise:promise,opening:{description:'公告时承诺与待交割状态。',material_refs:['initial:C01','initial:C03','initial:C04']},story_path:[{job:'双方说法和报道背景。',material_refs:['initial:C02','initial:C05','initial:C06','initial:QT01','initial:QT02','initial:QT03']}],quotation_refs:['initial:QT01','initial:QT02','initial:QT03']};
const currentProposal={...clone(originalProposal),opening:{description:'以原承诺对照应用中的路由设置。',material_refs:['initial:C01','initial:C03','initial:C04','supplementary:C01']},story_path:[
 {job:'协议与用户承诺。',material_refs:['initial:C01','initial:C03','initial:C04']},
 {job:'路由设置。',material_refs:['supplementary:C01','supplementary:QT01','initial:C02']},
 {job:'成本追踪和缓存状态；不夸大效果。',material_refs:['supplementary:C02','supplementary:C03','supplementary:C04']},
 {job:'双方解释。',material_refs:['initial:QT01','initial:QT02','initial:C05']},
 {job:'媒体分析。',material_refs:['initial:C06']},
 {job:'回到用户承诺。',material_refs:['supplementary:C01','supplementary:C02','supplementary:C03','initial:C04','initial:C03']}
],quotation_refs:['supplementary:QT01','initial:QT01','initial:QT02']};
const request={question:'能否找到至少一份在 2026 年 8 月 19 日或此前公开、由实际开发者或使用团队发布的 OpenRouter 使用记录，具体说明模型选择或路由在其应用中解决的问题？',required_for_story:true};
const ctx={content_id,stage:'propose',title,topic_brief:'公告日材料的受控交接测试；不独立验证新闻。',human_instructions:human,materials:initial,research_task_budget:3,approved_story:null};
const approved={story_id:'story_1',story_mode:'news',title,proposal:originalProposal,editor_note:'',research_requests:[request],additional_research_instructions:''};
function reassessed(){
 const parent={content_id,title,human_instructions:human,brief_content:'',editor_input:clone(ctx),quotation_validation:qv(3)};
 const work={schema:'research_work_order.v1',content_id,story_id:'story_1',story_mode:'news',service_invoked:false,editor_input:clone(ctx),parent_context:parent,research_input:{content_id,story_id:'story_1',story_mode:'news',human_instructions:'',final_narrative:{...clone(approved),initial_human_instructions:human}}};
 return clone({schema:'selected_story_reassessment_result.v1',content_id,story_id:'story_1',story_mode:'news',status:'ready_for_writer_handoff',next_action:'prepare_writing_handoff',writing_authorized:false,research_loop_authorized:false,approved_story:approved,editor_input:{...ctx,stage:'reassess',title,approved_story:approved,materials:{sources,claims,quotations,open_questions:[],conflicts:[]}},candidate:{schema:'story_candidate.v1',content_id,story_id:'story_1',story_mode:'news',status:'ready',proposal:currentProposal,research_requests:[]},selected_quotations:currentProposal.quotation_refs.map(ref=>{const q=quotations.find(q=>q.ref===ref);return {...q,source_url:sources.find(s=>s.ref===q.source_ref).url};}),research_increment_receipt:{schema:'research_increment_receipt.v1',content_id,story_id:'story_1',story_mode:'news',status:'usable_materials',worker_research_status:'research_ready',service_invoked:true,requires_reassessment:true,accepted_materials:extra,quotation_validation:qv(2),research_work_order:work},test_context:{kind:'reduced_historical_fixture',source_execution:'557',formal_hitl:false}});
}
function direct(){
 // Synthetic ready input: NOT a historical direct-ready execution.
 const x=reassessed(),c=clone(x.candidate);
 c.proposal=clone(originalProposal);
 return {schema:'story_dispatch.v1',content_id,story_id:'story_1',story_mode:'news',next_action:'prepare_writing',selection_status:'selected',title,title_override:'',editor_note:'',additional_research_instructions:'',research_requests:[],approved_candidate:c,editor_input:clone(ctx),parent_context:clone(x.research_increment_receipt.research_work_order.parent_context),test_context:{kind:'synthetic_direct_ready',formal_hitl:false}};
}
module.exports={reassessed,direct,clone};
