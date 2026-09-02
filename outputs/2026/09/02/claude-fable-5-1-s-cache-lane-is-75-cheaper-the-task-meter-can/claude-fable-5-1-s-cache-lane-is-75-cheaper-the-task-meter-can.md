# Claude Fable 5.1’s Cache Lane Is 75% Cheaper. The Task Meter Can Still Run 20% Hot

Watch two meters beneath the same coding agent. The cache price drops **75%**, while the cost of completing one task climbs **20%**. That contradiction is the real **Claude Fable 5.1** launch—not the discount printed across the release banner.

**Anthropic** has made repeated context dramatically cheaper, but it hasn’t shown how much context its new model consumes per successful job. The bill depends on both numbers: the price of each token and how many tokens the agent burns before it stops.

**Fable 5.1** went live in **Claude Code** and the **Claude Platform** on September 1, alongside **Claude Mythos 5.1**.[1](https://www.anthropic.com/claude-fable-and-mythos-5-1) Anthropic positions the models as upgrades for coding, knowledge work, research, and long-running agentic tasks.

The headline economics sound unusually clean. **ClaudeDevs** said Fable 5.1 retains Fable 5’s base pricing while cutting API cache-read prices by **75%**.[2](https://x.com/ClaudeDevs/status/2094851229734277228) **TestingCatalog** reported the same terms, while noting that Claude subscriptions may require extra usage credits.[3](https://x.com/testingcatalog/status/2094852015415242825)

A cache read lets an application reuse previously processed context instead of paying the full input price again. That matters when an agent repeatedly consults the same repository, instructions, tool definitions, or conversation history. *Cache hits are workload behavior, not a model feature.*

Picture a developer watching a terminal scroll after midnight. The agent reads the same architectural notes on every loop, opens another file, runs another test, and keeps moving. Each repeated page may now cost less, but the cursor can still travel farther.

Anthropic estimates that typical workloads can become roughly **25%** cheaper, with savings reaching **45%** for long agentic runs. Coverage from **The Verge** and **The Decoder** repeats the upper figure and ties it to autonomous work involving many tool calls.[4](https://www.theverge.com/ai-artificial-intelligence/987830/anthropic-claude-fable-mythos-5-1)[5](https://the-decoder.com/anthropics-claude-fable-5-1-promises-better-coding-and-research-at-up-to-45-percent-less)

Then the second meter moved. **Artificial Analysis** reported that Fable 5.1 topped its Intelligence Index but cost **20% more per task** than Fable 5, despite the cache discount.[6](https://x.com/ArtificialAnlys/status/2094881171066978525)

That result is important, but it isn’t fully independent: Artificial Analysis says it supported Anthropic’s pre-release evaluation. Its post also doesn’t disclose the task-level token totals, cache-hit ratios, or effort settings needed to reconcile the result with Anthropic’s estimates.[6](https://x.com/ArtificialAnlys/status/2094881171066978525)

The two claims can therefore be true at once. Anthropic can charge less for each cached token while Fable 5.1 generates, rereads, reasons over, or routes through enough additional tokens to raise total task cost. A cheaper ingredient doesn’t guarantee a cheaper meal.

> “It gets a lot further into a long task before it needs your input,” **ClaudeDevs** said.[2](https://x.com/ClaudeDevs/status/2094851229734277228)

That sounds like a capability gain, not an admission of higher consumption. But if “further” means more autonomous steps, more tool calls, or longer internal and visible outputs, the model’s token appetite could grow. The missing links are the extra step count, tokens per step, and cache reuse across those steps.

Heavy developers are already primed to distrust percentage headlines because subscription meters hide those mechanics. One circulating complaint described a 30-minute session consuming 20% of a weekly allowance, but that account could not be independently reviewed and shouldn’t be promoted as a benchmark. It is a warning signal, not verified evidence.

The verified signals remain mixed. Anthropic staffer **Boris Cherny** praised Fable 5.1 for difficult, long-running agentic work and said he had been using it broadly.[7](https://x.com/bcherny/status/2094864060609376748) That establishes practitioner enthusiasm inside Anthropic, not neutral cost performance across external repositories.

Subscription quotas further muddy the picture. A weekly percentage can reflect platform capacity rules, model multipliers, or “extra usage credits,” while an API invoice reflects metered token categories.[3](https://x.com/testingcatalog/status/2094852015415242825) Treating those two gauges as interchangeable creates false certainty in either direction.

The benchmark gains may still justify higher task cost. One report lists a **52.6%** result on Terminal-Bench-Science, while another says agentic coding improved by more than 30%.[8](https://www.marktechpost.com/2026/09/01/anthropic-releases-claude-fable-5-1-and-claude-mythos-5-1-52-6-on-terminal-bench-science-and-75-cheaper-cache-reads)[5](https://the-decoder.com/anthropics-claude-fable-5-1-promises-better-coding-and-research-at-up-to-45-percent-less) Paying 20% more for a materially higher completion rate can improve unit economics—but only if the model actually closes more of your jobs.

That is why cost per million tokens is the wrong final column. The useful denominator is successful tasks: merged fixes, accepted analyses, completed migrations, or another outcome your team can count. *The denominator is doing most of the work.*

Run Fable 5 and Fable 5.1 against one representative week, using the same tasks, tools, repository state, and stopping conditions. Record total input, output, cache-write, and cache-read tokens, then divide total spend by successful completions. Keep failed and human-rescued runs visible.

Also inspect the shape of the work. Long sessions with stable instructions and repeated repository context should expose more tokens to the cheaper cache-read rate. Short prompts, rapidly changing context, or low cache reuse may barely touch the discount.

The decision rule is narrow. Move long, agentic, high-reuse workloads to Fable 5.1 when measured cost per successful task falls—or when a higher completion rate clearly earns its premium. Keep short or low-hit workloads on the existing model until their own ledger says otherwise.

Several cells remain blank: cache-write economics, task-level token expansion, subscription-credit multipliers, and the precise assumptions behind the **25%**, **45%**, and **20%** figures. Those unknowns don’t erase the launch’s value; they define what must be measured before the headline becomes a budget.

The cache lane is **75%** cheaper. The task meter still counts every mile the agent chooses to drive.


## Sources

1. [Introducing Claude Fable 5.1 and Claude Mythos 5.1 \ Anthropic](https://www.anthropic.com/claude-fable-and-mythos-5-1)
2. [ClaudeDevs (@ClaudeDevs) on X](https://x.com/ClaudeDevs/status/2094851229734277228)
3. [🚨 AI News | TestingCatalog (@testingcatalog) on X](https://x.com/testingcatalog/status/2094852015415242825)
4. [Anthropic launches Claude Fable 5.1 and says it’s up to 45 percent cheaper for agentic work](https://www.theverge.com/ai-artificial-intelligence/987830/anthropic-claude-fable-mythos-5-1)
5. [Anthropic's Claude Fable 5.1 promises better coding and research at up to 45 percent less](https://the-decoder.com/anthropics-claude-fable-5-1-promises-better-coding-and-research-at-up-to-45-percent-less)
6. [Artificial Analysis (@ArtificialAnlys) on X](https://x.com/ArtificialAnlys/status/2094881171066978525)
7. [Boris Cherny (@bcherny) on X](https://x.com/bcherny/status/2094864060609376748)
8. [Anthropic Releases Claude Fable 5.1 and Claude Mythos 5.1: 52.6% on Terminal-Bench-Science and 75% Cheaper Cache Reads](https://www.marktechpost.com/2026/09/01/anthropic-releases-claude-fable-5-1-and-claude-mythos-5-1-52-6-on-terminal-bench-science-and-75-cheaper-cache-reads)
