# Author Voice Research

Research date: 2026-09-25. Purpose: calibrate the V2 EN Lead Writer against published prose, without turning past first-person statements into authority for future articles. This is a descriptive study with a conservative runtime extraction, not a new editorial policy or an assessment of the author's personality.

The strongest recurring behavior is **problem → mechanism or worked example → practical consequence**. The corpus does not support treating the author as uniformly terse, ironic, anti-question, or opposed to explanatory headings and optimistic endings. Those distinctions matter: a profile that simply repeated the desired anti-AI checklist would misrepresent the publications.

## Corpus

Discovery source: [Hai Hu — recent LinkedIn Articles](https://www.linkedin.com/in/haihu/recent-activity/articles/). The authenticated browser displayed seven article entries. After scrolling the list, it still displayed seven, with no additional article-loading control observed. Six substantial articles were read from their individual published pages; the one-minute prompt checklist was excluded. This meets the five-article minimum for substantial relevant reading, but not the preferred 8–12. It does not establish that the account has only seven articles in total.

All six pages visibly identify Hai Hu as author. Dates below are the displayed publication dates, not dates inferred from order or article narrative. Counts are rounded whitespace-delimited words after the publication-date header, including visible headings, captions, embedded prompts/code and, where present, references. They are approximate page-body lengths, not clean author-prose counts. Image-only text is not counted. Reading times come from the article index.

| ID | Title and URL | Visible publication date | Approximate length | Topic | Representativeness and access |
| --- | --- | --- | --- | --- | --- |
| A1 | [The AI Cold War: When Ethical Guardrails Become a National Security Threat][A1] | 2026-02-25 | 1,175 words; 5 min | AI suppliers, military procurement, ethics and geopolitical pressure | Relevant recent analytical contrast; atypical combative register. Complete rendered body readable; no article-text access gate. |
| A2 | [Low-Code, High-Impact: Building Enterprise AI Learning Agent with n8n][A2] | 2025-05-20 | 4,350 words; 15 min | Employee learning, workflow design and enterprise adoption | Representative practical tutorial. Body readable; extensive embedded prompts/code are excluded from voice inference. Several diagrams/tables and the final advice appear as images; their wording was not transcribed. |
| A3 | [BIAN AI Assistant - A Multi-modal RAG knowledge base built in 12 hours][A3] | 2025-04-30 | 4,330 words; 13 min | Banking knowledge retrieval and product implementation | Representative explanatory case study. Body readable; diagrams and screenshots were not transcribed. Long quoted prompt templates excluded from prose-style inference. |
| A4 | [A Chronicle of an AI Product’s Birth][A4] | 2025-04-16 | 2,305 words; 9 min | Prototype-to-product development and distribution | Representative development narrative with an atypically extended autobiographical/promotional ending. Launch announcement frame retained because most of the body is a substantive engineering retrospective, not announcement boilerplate. Body readable; images not transcribed. |
| A5 | [Navigating the Frontiers of AI Programming: Insights from 10,000 Lines of Code][A5] | 2025-03-24 | 1,730 words; 8 min | AI coding limitations and working practices | Representative failure analysis. Body readable; opening infographic not transcribed. |
| A6 | [The Hidden Language Divide: How LLM Performance Gaps Could Shape Global AI Access][A6] | 2025-01-23 | 2,195 words including references; approximately 1,860 before references; 10 min | Language performance and unequal access | Representative technology-to-consequence argument; atypical bibliography-heavy survey sections. Body readable; figures not transcribed. Cited studies and factual assertions were not independently validated. |

Excluded: [🚀 Prompt Engineering Best Practices](https://www.linkedin.com/pulse/prompt-engineering-best-practices-hai-hu-faqle), a one-minute checklist according to the index, not a substantial analytical article. Its publication date was not collected. No reposts, comments, job updates, drafts, or private conversations were used. Each published URL was counted once. A3's cover label differs from its article heading; the table uses the article heading. A3 also contains an April 27 dateline; that is not substituted for its April 30 publication date.

### Sampling and inference method

Read each article through its ending; compare openings, transitions, claims, paragraph organization and closing moves. Treat embedded prompts, code, quoted third-party speech, bibliography entries, image captions and cover slogans as separate from the author's narrative prose. Their presence is structural evidence, but their wording is not a voice template. No hidden page state or unpublished drafts were used.

A rule is **HIGH** when the same editorial decision recurs in at least three articles and is not explained solely by one narrow topic. **MED** means supported by two examples or materially limited by genre. **LOW** means one example or insufficient evidence. Confidence describes this corpus, not the permanence of a personal trait. Only HIGH cross-article abstractions enter the JSON; evidence/safety safeguards are normative constraints, explicitly distinguished from observed behavior.

Five 2025 articles provide the broader base; A1 supplies the only 2026 comparison. Three of the five older articles are related project tutorials/retrospectives, so their agreement is not equivalent to three independent genres. Do not weight the six equally on every dimension. Count the corpus as six studied long-form articles, not six equally typical specimens of one uniform voice.

## High-confidence recurring patterns

| Pattern | Evidence across corpus | Confidence | Why it matters for generation |
| --- | --- | --- | --- |
| P1. Start from a problem with an identifiable user or affected group; connect the technology to useful work. | [A2][A2] derives relevance filtering and practical prompts from employees' learning needs; [A3][A3] derives diagram retrieval from architects' training needs; [A4][A4] connects verification friction to a product idea; [A6][A6] connects language performance to institutions' ability to use AI. | HIGH | Gives the article a reason to exist beyond announcing capabilities. |
| P2. Expose a position or practical promise early, then unfold its support. | [A2][A2] puts incremental implementation advice in the early summary; [A3][A3] leads with a concrete build outcome; [A4][A4] contrasts fast prototyping with finishing work in its TLDR; [A6][A6] interprets the language gap in the opening; [A1][A1] begins with a strong judgment. | HIGH | Prevents a neutral inventory from postponing the argument indefinitely; does not impose an identical lead. |
| P3. Explain decisions through constraints and rejected alternatives. | [A2][A2] contrasts script maintenance with workflow tools and model latency with task needs; [A3][A3] explains why generic RAG/UI tools do not fit the required custom flow; [A5][A5] links project failures to context and debugging constraints. | HIGH | A tool recommendation becomes a conditional choice with a reason. |
| P4. Develop an argument through artifacts and observable steps rather than abstract endorsement alone. | [A2][A2] follows data inputs and workflow roles; [A3][A3] follows requirements, retrieval and UI implementation; [A4][A4] follows prototype, API, extension and store review; [A5][A5] uses project-specific failure episodes. | HIGH | Makes claims inspectable in the story. It does not make the historical claims verified facts for reuse. |
| P5. Translate a mechanism into an operating consequence. | [A3][A3] explains query rewriting through vocabulary mismatch and retrieval usefulness; [A5][A5] relates context/logging constraints to rework and debugging effort; [A2][A2] relates model selection to waiting time and workflow maintenance; [A6][A6] scales a performance gap into institutional disadvantage. | HIGH | Supplies the causal bridge between technical detail and reader decisions. |
| P6. Distinguish getting a demonstration working from making it usable. | [A4][A4] separates a quick script from weeks of UX and distribution work; [A3][A3] moves explicitly from MVP to product refinements; [A2][A2] distinguishes experimentation from maintenance and iteration at work. | HIGH | Keeps the article attentive to integration and adoption rather than benchmark spectacle alone. |
| P7. Alternate explanation with shorter pivots; let lists carry genuinely parallel material. | [A2][A2] mixes explanatory paragraphs, compact workflow steps and short result pivots; [A3][A3] mixes mechanism explanations with requirements/tool lists; [A5][A5] mixes failure narratives with remedies; [A1][A1] uses especially short judgment beats after reported developments. | HIGH at the structural level | Preserve paragraph variety; do not convert one recent article's staccato into a universal sentence quota. |
| P8. Advance by dependency, obstacle or consequence. | [A4][A4] progresses from a running prototype to the next product requirement; [A3][A3] progresses from knowledge access to specialized retrieval to usable UX; [A2][A2] moves from audience needs to data preparation to agents and adoption. | HIGH | Produces transitions that carry reasoning, even when ordinary signposts are used. |
| P9. Make headings navigational and specific to the section's job. | [A3][A3] labels build stages and tools; [A5][A5] labels distinct capability boundaries; [A2][A2] names data-source and implementation stages; [A1][A1] labels stages of the conflict. | HIGH | Use concrete task/constraint headings. Argumentative sentence headings are not the universal norm. |
| P10. End by returning to human or operational stakes. | [A2][A2] closes its readable prose with adoption factors and actionable advice; [A3][A3] returns to the ability to build useful knowledge tools; [A5][A5] closes on a revised assessment and invites correction; [A6][A6] returns to access and collective choices. | HIGH at the functional level | End with the consequence for a reader or affected group, without imposing a uniformly cold or inspirational tone. |
| P11. Put limitations at the affected choice rather than in a recurring disclaimer block. | [A2][A2] places limitations beside agent-node experience and model choice; [A3][A3] qualifies platform suitability where customization is discussed; [A4][A4] introduces hosting/review obstacles in the release sequence; [A5][A5] pairs capability boundaries with failure cases. | HIGH for practical constraints | A caveat should change the decision. This is not evidence that all factual uncertainty is handled rigorously in the publications. |
| P12. A headline usually names the subject and adds a result, boundary or consequence. | [A2][A2] pairs low-code with an enterprise build; [A3][A3] names the RAG product and a time-bound result; [A5][A5] ties programming lessons to project scale; [A6][A6] connects a technical gap to access. | HIGH | Replace an internal research-note label with a recognizable subject and meaningful stakes. |

## Opening patterns

| Opening type | Observation and examples | Inference |
| --- | --- | --- |
| Event-first | [A4][A4] opens with a product launch and elapsed development time; [A6][A6] opens with model releases before introducing the language issue. | Recurring option, not mandatory news chronology. |
| Contradiction-first | [A1][A1] begins with the conflict between ethical and security imperatives. [A4][A4]'s early summary contrasts rapid prototyping with product completion, but its first paragraph is event-first. | Useful tension, but only one unambiguous contradiction-first lead. LOW as a fixed opening template; excluded as a mandate. |
| Number-first | [A3][A3] embeds the 12-hour result in its opening summary; [A5][A5] begins its introduction with months, projects and code scale; [A4][A4] contrasts minutes and weeks. | Numbers establish the case's scale or cost. Not all are literally the first word. |
| Consequence-first | [A1][A1] begins with strategic judgment; [A3][A3] foregrounds the build outcome. | Both make payoff visible, but their tones and evidence forms differ. |
| Anecdote-first | [A4][A4]'s family-chat episode appears after the lead, links and TLDR; [A2][A2]'s work scenario follows an introduction and summary. | Personal cases are common; an anecdote as the literal opening is not established. |
| Rhetorical-question opening | None of the six begins its authored body with a question. [A3][A3] soon stages a reader's practical question; [A1][A1] reaches an unresolved ethical question in the opening passage. | A question need not be banned, but a question-answer shell is not the default first paragraph. |

**First-screen pacing:** five of six use an early TLDR/summary or infographic cue (A1–A5). A4 interposes product links; A2 and A5 introduce what the article will cover; A3 presents a result and demo cue. A6 proceeds directly from event to interpretation. The common decision is early orientation/payoff, not a common visual first screen or a compulsory summary box. Actual screen occupancy depends on viewport and image layout and was not measured.

**Judgment timing:** A1 judges immediately; A6 shifts to concern by its second substantive paragraph; A2/A4 summarize practical judgments before the narrative; A3 asserts usefulness early; A5 states scope early but develops stronger judgments through cases. The proposed example rule “judgment after 1–3 evidence-bearing paragraphs” would be too rigid and is not adopted.

## Headline patterns

The six displayed article titles contain approximately 8–16 whitespace-delimited words. Four use a colon, A3 uses a dash, and A4 uses a compact narrative title. None uses a question mark. These are headline constructions; they do not establish that separate subtitles are common. Cover text on A3/A4/A5 is not counted as an independent subtitle convention.

[A2][A2], [A3][A3], [A5][A5] and [A6][A6] earn specificity through a tool, technical domain, quantity or consequence. A1 adds explicit conflict. A4 is less specific without its accompanying launch lead. The practical runtime preference is subject plus result/stakes, not mandatory punctuation, headline length or outrage. [A1][A1]'s dramatic threat framing and [A3][A3]'s rapid-build promise should not become a requirement to maximize alarm or promise speed.

Clickability arises from a recognizable task, a constrained result, or a consequential tension. The corpus does contain broad promotional framing; it does not prove an absolute absence of clickbait. Future evidence must independently justify any numerical promise.

## Paragraph and sentence rhythm

Narrative paragraphs are often one to three sentences, but this is a qualitative reading, not a mechanically verified distribution. A1 is markedly shorter and punchier; A6 uses longer explanatory blocks and research lists; A2/A3 include prompts, code and captions that would distort a raw paragraph average. No exact word-count target or paragraph cap is inferred.

[A1][A1] frequently follows detail with a compressed judgment. [A2][A2] and [A3][A3] use shorter result/pivot paragraphs between fuller explanations and step lists. [A5][A5] sometimes keeps explanation and judgment together in a longer paragraph. The stable rule is variation by rhetorical job, not shortness for its own sake.

Sentence lengths vary with explanation: A3's retrieval mechanism and A5's debugging failures need fuller clauses; A2's practical workflow steps and A1's judgments can be brief. The corpus does not support a universal 25-word sentence limit, a fixed number of standalone punches, or a rule that every dense paragraph must be followed by one.

Transitions are often explicit: A3/A4 use chronological and dependency cues; A2 uses reader address and questions; A5/A6 use conventional contrast/addition language. Causal progression is recurrent, but an absolute ban on ordinary connective words would be invented.

## Authorial judgment

**Strength and ratio.** A1/A6 are judgment-forward; A2–A5 devote more space to explanation, artifacts and project sequences. All contain an identifiable view. There is no defensible universal numerical fact-to-judgment ratio: separating fact, recollection, interpretation and embedded material requires annotation that this study did not perform. The usable instruction is to make a judgment and show its basis, not to enforce a percentage.

**Evidence boundaries.** A5 scopes observations to described projects; A2 acknowledges gaps in the author's node/tool usage; A1 names reports and distinguishes some allegations from its own view; A6 uses author-year references. Those forms indicate evidence presentation, not independent validation. Neither the numerical claims nor the references in these articles were fact-checked here. Do not transfer them into new reporting merely because they appeared under the author's byline.

**Explicit implications.** A2 has an enterprise-strategy section after the build sequence; A3 moves from technical implementation to who can now build; A6 repeatedly explains societal consequences. The author often does explain significance. The research does not support “never say why this matters.” A useful consequence introduces a new decision or causal step; repeating the same implication without new reasoning is not needed to preserve voice.

**Letting evidence stand.** A2's snippets and A4's implementation artifacts sometimes demonstrate a point without immediate abstract restatement. However, both also explain outcomes extensively. Evidence-only understatement is MED as an occasional behavior, not a runtime requirement.

**Technical translation.** A3 converts vocabulary mismatch into query rewriting and usable answers; A5 converts lost context and poor logging into debugging cost and module strategy; A2 converts latency and maintenance into platform/model choices. This is stronger cross-article evidence than a generic instruction to “write for CTOs.” The audience is often learning to use AI; explaining unfamiliar concepts is part of the style.

**First person.** First person appears in all six, but serves different purposes: project chronology and learning in A2–A5, explicit perspective in A1, situated framing in A6. It is not a license to fabricate employment, testing, deployment, biography or beliefs. Use only the current assignment's documented actions or supplied viewpoint. The JSON's first-person restriction is an evidence safeguard, not an empirical claim that the corpus never makes unsupported claims.

**Humor and irony.** A2 includes self-deprecating tool credits and light emoji humor; A1 uses sharper sarcasm and combative metaphors; A5 occasionally uses a biting label for unreliable tools. MED and genre-sensitive. No required joke, profanity, emoji quota or cynical persona enters runtime.

**Metaphors.** A3 uses a kitchen-role analogy to explain RAG; A2 uses familiar physical/workplace analogies for workflow components; A6 compares degraded tools to less efficient infrastructure. HIGH for the function of making a mechanism intelligible, not for any signature image. A1's many conflict metaphors are a stylistic extreme. There is no established one-metaphor-per-article rule.

**Disagreement and counterevidence.** A1 grants some force to an objection against the company's position; A5 revises initial enthusiasm after failures; A2/A3 reject attractive tools when they fail a requirement. HIGH for letting a material obstacle change an assessment. Balanced treatment of every possible opposing position is not established, and the profile does not demand a performative both-sides paragraph.

## Caveat behavior

Practical caveats are usually local: A2's knowledge limits sit near agent features, A3's platform limitations near customization, A4's hosting and review problems near release work. A5 makes limitations the organizing subject of the whole article. A4's early TLDR also qualifies rapid-prototype optimism with finishing effort. Therefore caveats can be front-loaded or inline when useful; they are not uniformly deferred.

There is little evidence of a repeated, identical legalistic disclaimer after every claim. That narrow absence should not be exaggerated into “the author rarely qualifies anything”: A5 is a sustained limitation analysis and A6 includes repeated uncertainty and urgency framing. No firm repetition quota can be justified.

Uncertainty is often expressed as a capability boundary, scenario limitation, reported allegation, or forward-looking risk. These expressions can preserve momentum by identifying what follows from the limit. The runtime rule favors decision-relevant qualification, while the existing evidence contract still determines which uncertainty disclosures are mandatory.

## Section-heading behavior

Descriptive noun phrases and procedural labels are common: A3 organizes a build by stages and tools; A5 identifies specific failure boundaries; A2 groups sources, workflow work and enterprise application. A6 often uses broad report-like topic headings. A1 uses more dramatic thematic headings. Heading lengths vary from a few words to extended stage descriptions; there is no reliable universal length limit.

Some headings imply a claim, especially capability boundaries in A5 or conflict framing in A1, but most are not full argumentative sentences. Numbering is common where sequence is real. Runtime therefore prefers headings that identify the work, constraint or consequence; it does not claim the author avoids descriptive, numbered or white-paper-like headings altogether.

## Endings

| Ending function | Evidence | Runtime consequence |
| --- | --- | --- |
| Decision rule / practical application | [A2][A2] returns to suitability, data readiness, human involvement and adoption; [A5][A5] lands on a revised capability assessment. | Strong evidence for returning to decisions. A2's final image-only suggestions were not read, so its exact final wording is not claimed. |
| Hard judgment / unresolved tension | [A1][A1] ends with an ethical boundary question; [A6][A6] ends with access-related urgency. | Supported as options; not evidence for a universally cold kicker. |
| Encouragement and CTA | [A3][A3] encourages building; [A4][A4] has explicit promotion and an extended inspirational ending; [A5][A5] invites feedback/corrections. | These are present, not anti-patterns absent from the author. Do not mandate them in runtime; story/distribution contracts decide. |

The stable ending function is a return to what people can do or what is at stake. A4's personal reminiscence and cultural quotation are an outlying execution of that function and must not be replicated as borrowed personal history.

## Anti-patterns

This section tests the requested concerns against the corpus; it does not recast desired future improvements as historical facts.

| Proposed anti-pattern | Corpus finding | Evidence-bounded use |
| --- | --- | --- |
| Research memo voice | Present in parts of A6 and the taxonomy of A5; absent as a total description of the practical build narratives. | Prefer a concrete problem and a point of view. Do not infer that research exposition itself is foreign to the author. |
| Consulting language | Present in A2/A3's enterprise framing and A6's institutional recommendations. | Preserve useful operational specificity, not inflated role language. A categorical vocabulary ban is editorial policy, not corpus evidence. |
| Generic significance paragraphs | A2 explicitly discusses enterprise-strategy significance; A6 repeatedly develops stakes. | Use a mechanism and a new consequence; do not claim significance is always left implicit. |
| Self-question / self-answer | Clearly present in A2/A3/A4, though none of the six opens its body with a literal question. | Questions should frame a real requirement or tradeoff. A blanket ban would contradict the sample. |
| Excessive scene-setting | Most leads orient quickly, but A4 has substantial personal narrative near the end and A2/A3 take time to establish context. | Keep early orientation; no universal ban on scenes. |
| Repeated disclaimers | Repeated boilerplate disclaimer blocks are not conspicuous in the six bodies. A5's repeated limitations have distinct substantive jobs. | Attach necessary caveats to the relevant decision; do not hide uncertainty to imitate confidence. |
| Mechanical first/second/third | Real numbered steps and lists are frequent in A2/A3/A5. | Distinguish actual sequence from a template. No ban on numbered exposition. |
| Inspirational wrap-up | Prominent in A3/A4 and present as collective urgency in A6. | Do not encode “always end cold” as author fidelity. |

What most reliably distinguishes the stronger passages from generic AI/consulting prose is a named problem, a concrete choice, and the consequence of that choice: retrieval design in A3, product completion in A4, debugging failures in A5, and workflow suitability in A2. Abstract enthusiasm, stock transitions and broad claims also occur in this corpus. This is calibration, not a claim that every published passage is exemplary.

**What tends to be omitted:** in the practical cases A2/A3/A4, implementation depth is selective rather than exhaustive: enough artifact detail to understand the chosen path, not a complete reproducibility package in the prose. In A1/A6, the argument similarly selects material for consequences rather than a full technical specification. This supports selecting details for their explanatory job, not omitting evidence required for verification. No claim is made about private testing, unpublished methodology or what the author deliberately chose not to disclose.

## Outliers

- **A1 — register, not wholesale exclusion:** only recent geopolitical polemic in this sample. Its profanity, compressed punches and martial imagery are LOW as general author rules. Use its concrete consequence chain as corroboration where older pieces agree. One newer piece cannot establish a permanent shift in voice.
- **A4 — ending, not substantive body:** unusually long autobiographical reflection, promotional CTA and cultural quotation. Its prototype-to-product analysis remains relevant; its personal history is not reusable narrative material.
- **A6 — format, not technical-to-social reasoning:** reference-heavy survey and broad policy recommendations. Do not make bibliography density, institutional language or repeated urgency the runtime default. The cited literature was not independently checked.
- **A2/A3 — topic-dependent tutorial machinery:** pasted prompts, code, screenshots, procedural numbering, platform prices and deployment steps reflect how-to subjects. Do not force those elements into analytical news articles. A2's light emoji humor is not a universal voice marker.

No article is discarded merely because it contradicts an intended cleanup rule. Only patterns supported across articles govern runtime strongly.

## Runtime evidence map

The companion JSON deliberately omits examples and confidence notes. The map below covers every substantive rule group; alternatives/avoid rules are narrow operational counterparts of the positive behavior, not claims of absolute absence.

| JSON field | Supporting patterns and articles |
| --- | --- |
| `voice.core` | P1–P5; A2/A3/A4/A5/A6. |
| `voice.judgment_style` | P2/P3; A2/A3/A5, with A1/A6 supporting visible judgment. |
| `voice.evidence_style[0]` | P4/P5; A2/A3/A4/A5. |
| `voice.evidence_style[1]` | Attribution visible in A1/A6 and project-scoped observation in A5; preserving attribution is also an explicit task safety requirement. |
| `voice.evidence_style[2]` | First-person functions in A1–A6; prohibition on invented experience is the user's hard boundary, not a style-frequency claim. |
| `voice.technical_to_operational_translation` | P5/P6; A2/A3/A4/A5/A6. Functional analogy/explanation: A2/A3/A6. |
| `headline` | P12; A2/A3/A5/A6. |
| `opening` | P1/P2; A2/A3/A4/A5/A6. No fixed lead sequence inferred. |
| `paragraph_rhythm` | P7; A2/A3/A5, with A1 as a shorter-register contrast. |
| `transitions` | P8; A2/A3/A4. Genuine reader questions: A2/A3/A4. |
| `section_headings` | P9; A2/A3/A5. |
| `caveats` | P3/P11; A2/A3/A4/A5. Counter-objection: A1; revised assessment: A5. |
| `ending` | P10; A2/A3/A5/A6. |
| `anti_generic_ai` | P1/P3/P4/P5/P8; A2/A3/A4/A5. |
| `hard_safety` | Normative task requirements, not an empirical inference about the author. |

## Confidence and limitations

- **Corpus size:** six substantial relevant articles studied, spanning 2025-01-23 to 2026-02-25; five older base articles and one newer register contrast. Preferred 8–12 unavailable in the observed list. If “five representative” means five examples of the current 2026 news-analysis register, that stricter threshold is **not met**; there is only one such piece here.
- **Access:** authenticated browser could read all six rendered text bodies. Image-only information, including A2's final recommendations and A5's summary infographic, was not transcribed. The analysis does not claim full image-text coverage. No login or paywall workaround was used.
- **Freshness:** no article later than February 2026 appeared in the observed list. That is a discovery limit, not proof of no later publication. The nine-month gap before A1 and concentration of tutorials limit inference about today's preferred EN voice.
- **Text statistics:** lengths include non-narrative material; paragraph/sentence observations are qualitative. A fast structural DOM pass returned empty sets during page transitions and was discarded rather than treated as zero paragraphs. No false precision from that pass enters the profile.
- **Fact checking:** this is a style study. Historical product, pricing, benchmark, research and geopolitical claims remain attributed statements from the corpus, not verified inputs for future stories. No biography, beliefs, emotional state, employer position or private experience is inferred.
- **Existing policy:** `knowledge/en-author-style.md` contains prescriptive rules such as strict paragraph limits, a cold ending and controlled jokes. It is not evidence of published author behavior. Neither it nor any writer prompt/workflow was changed. The new JSON is an inert calibration artifact until separately integrated; evidence and story contracts outrank it.
- **Improvement potential:** the profile supports subject-and-consequence headlines, functional headings, choice-driven questions, local caveats and causal implications. It cannot honestly promise to eliminate all question-answer passages, report-like headings or inspirational endings while claiming those forms are absent from the author's work. Any stricter cleanup belongs to a separately approved editorial policy.

### Validation checklist

- [x] Six long-form text bodies read; minimum useful corpus achieved with the representativeness qualifications above.
- [x] Every major runtime style rule maps to multiple articles; single-article and genre-specific surface habits stay in this report.
- [x] Runtime rules paraphrase editorial decisions, without copied signature phrases, personal anecdotes or imported quotations.
- [x] First-hand claims, biography and evidence authority are explicitly constrained.
- [x] JSON follows the supplied key structure, parses, and is checked against the approximate 1,500-token ceiling before delivery.
- [x] Stable patterns, topic-dependent machinery and outliers are separated; contrary evidence is retained.
- [x] No Lead Writer prompt, workflow code or existing style contract modified by this task.

[A1]: https://www.linkedin.com/pulse/ai-cold-war-when-ethical-guardrails-become-national-security-hai-hu-dmdmc
[A2]: https://www.linkedin.com/pulse/low-code-high-impact-building-enterprise-ai-learning-agent-hai-hu-v84be
[A3]: https://www.linkedin.com/pulse/bian-ai-assistant-multi-modal-rag-knowledge-base-built-hai-hu-iozue
[A4]: https://www.linkedin.com/pulse/chronicle-ai-products-birth-hai-hu-51e3e
[A5]: https://www.linkedin.com/pulse/navigating-frontiers-ai-programming-insights-from-10000-hai-hu-mdv5e
[A6]: https://www.linkedin.com/pulse/hidden-language-divide-how-llm-performance-gaps-could-hai-hu-qobff
