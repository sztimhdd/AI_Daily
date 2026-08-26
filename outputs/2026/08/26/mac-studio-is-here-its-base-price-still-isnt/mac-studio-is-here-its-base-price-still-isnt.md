# Apple's New Macs Are a Local-AI Deployment Ladder

**Apple** refreshed the two desktops its pro buyers actually use, and the pattern in the price list is the real announcement. The **Mac mini** starts at **$899** with 16GB of unified memory; the **Mac Studio** reaches **512GB** at **$5,499**. Between them sits a ladder of memory sizes, and each rung is a class of model you can run entirely on your own desk. [1](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/) [2](https://www.apple.com/newsroom/2026/08/apple-unveils-a-more-powerful-mac-mini-featuring-the-all-new-m6-and-m5-pro/)

That is the frame worth keeping: in local AI, memory is the deployment limit. A model either fits in unified memory or it does not, so every configuration **Apple** released on August 25 is a statement about which workloads can move off the cloud. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/)

The entry rung is the **M6 Mac mini** at **$899**: 16GB of memory, a 12-core CPU, a 12-core GPU, and 153GB/s of bandwidth. Community analysis puts its realistic range at 7B–8B 4-bit models, embeddings, transcription, and tightly scoped agents. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/) MacStories estimates a base-model 7B workload could clear 60 tokens per second, up from roughly 17 on an M4 mini. [4](https://www.macstories.net/notes/the-potential-of-m6-and-m5-ultra-for-local-ai-on-macos/)

**Apple** now calls the mini an always-on agentic device, and the specs support the label: 2.5Gb Ethernet standard, 10Gb optional, and a 155W continuous power ceiling. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/) A box that stays powered all night is a different deployment shape from a laptop that sleeps in a bag.

The serious AI configuration starts one step up. At **$1,299**, the 24GB and 32GB M6 variants double the base bandwidth to 170GB/s and open the 14B-class range, with 32B experiments possible on the 32GB version. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/) **Apple**'s own headline number — up to 4.8x faster time-to-first-token in LM Studio — was measured on a 32GB preproduction machine, not the $899 base. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/)

![An Apple Studio Display and a compact silver Mac mini on a light gray surface, with a Magic Mouse, two keyboards, and cables running between the screen and the desktop.](https://raw.githubusercontent.com/sztimhdd/AI_Daily/main/outputs/2026/08/26/mac-studio-is-here-its-base-price-still-isnt/images/01.webp)
*The desk is the new deployment target. (Image: Apple)*

The **M5 Pro Mac mini** is the crossover rung: up to 64GB of unified memory and 307GB/s of bandwidth, enough headroom for 32B models, long context, and concurrent services. [2](https://www.apple.com/newsroom/2026/08/apple-unveils-a-more-powerful-mac-mini-featuring-the-all-new-m6-and-m5-pro/) [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/) **Apple** rates its LLM prompt processing at up to 8.5x an M2 Pro. [2](https://www.apple.com/newsroom/2026/08/apple-unveils-a-more-powerful-mac-mini-featuring-the-all-new-m6-and-m5-pro/)

Then comes the tier the community has already stress-tested. **M5 Max** reaches **128GB** of unified memory at **$2,499**, and the reports are not hypothetical: a developer ran a **122B-parameter** Qwen model entirely on an M5 Max with 128GB, and r/LocalLLaMA benchmarks now rate the 128GB configuration as the single-user inference leader, at an estimated 30–45 tokens per second for agent workloads. [5](https://theagenttimes.com/articles/local-llm-hardware-showdown-reveals-no-clear-winner-for-agen-ef110f7c) [6](https://noticias.ai/apple-silicon-apunta-alto-un-m5-max-mueve-un-modelo-de-122b-en-local/) Another report has a 35B model on an M5 Max matching Claude for agentic coding at zero API cost. [5](https://theagenttimes.com/articles/local-llm-hardware-showdown-reveals-no-clear-winner-for-agen-ef110f7c)

![A silver Mac mini with a black Apple logo sits at the center of a desk, surrounded by a keyboard, a sketch notebook, and an iPhone on a light beige background.](https://raw.githubusercontent.com/sztimhdd/AI_Daily/main/outputs/2026/08/26/mac-studio-is-here-its-base-price-still-isnt/images/02.webp)
*A machine that sits quietly while the models run. (Image: Apple)*

The top rung is **M5 Ultra**: up to **512GB** of unified memory and **1.2TB/s** of bandwidth for **$5,499**, with the 512GB variant shipping in late October. [1](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/) **Apple** frames it as the first desktop that runs frontier-class open-weight models on device. [1](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/) That memory pool dwarfs the VRAM of any consumer GPU, and the bandwidth beats the fastest cards on sale. [7](https://www.macrumors.com/2026/08/26/new-mac-studio-can-be-clustered-together/)

The first **Qwen** data point for that rung is already on the board: a benchmark page reviewed for this story lists **Qwen 2.5 72B** at **23 tok/s** on an M5 Ultra with 96GB, Q4_K_M quantized under MLX. It is a listing, not a lab test, and the machine does not ship until September 22 — treat the number as a preview, not a verdict.

![A dark benchmark page titled Run Qwen 2.5 72B on M5 Ultra, showing 23 tok/s, 96 GB RAM, Q4_K_M quantization via MLX, with Speed and First Token metric cards.](https://raw.githubusercontent.com/sztimhdd/AI_Daily/main/outputs/2026/08/26/mac-studio-is-here-its-base-price-still-isnt/images/04.png)
*A 23 tok/s listing for Qwen 2.5 72B is a preview to verify once units ship, not a certified result.*

The deployment ceiling rises further when machines are pooled: four **Mac Studio** units can share memory over Thunderbolt 5 and RDMA, which **Apple** says delivers up to 3x faster inference than a single system. [7](https://www.macrumors.com/2026/08/26/new-mac-studio-can-be-clustered-together/)

The cluster story is not new — RDMA arrived in macOS Tahoe 26.2 and works on any Thunderbolt 5 Mac — and the community notes practical limits of two-to-five nodes with ring topology. [7](https://www.macrumors.com/2026/08/26/new-mac-studio-can-be-clustered-together/) Independent testing of the previous generation measured a 122.6 percent speedup running DeepSeek V3.1 across four M3 Ultra Studios, so the mechanism is real even if **Apple**'s 3x figure needs its own test. [8](https://m.ithome.com/html/907113.htm)

The honest caveats are bandwidth and software. The $899 M6 gets 153GB/s, not the 170GB/s of the higher configurations, and every Neural Accelerator gain still depends on the runtime — MLX and Core ML reach the hardware, but a typical llama.cpp or Ollama workload will not automatically touch every block. [3](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/)

Pricing closes the ladder in China as well: media cite **¥19,999** for the M5 Max **Mac Studio** and **¥46,999** for the M5 Ultra, figures that match what Chinese tech media had already circulated before the launch. [9](https://pc.zol.com.cn/1238/12382882.html) The rumor and the official list finally agree.

![A Mac configuration table comparing four models across Price, Chip, and spec rows, with M6 and M5 Pro chip options shown.](https://raw.githubusercontent.com/sztimhdd/AI_Daily/main/outputs/2026/08/26/mac-studio-is-here-its-base-price-still-isnt/images/03.png)
*The configuration page is the deployment menu.*

**Apple** did not just release faster computers. It priced a deployment map: every memory tier is a model class, and every model class is a workload that no longer needs a cloud bill. [1](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/)

## Sources

1. [Apple introduces new Mac Studio with M5 Max and M5 Ultra](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/)
2. [Apple unveils a more powerful Mac mini featuring the all-new M6 and M5 Pro](https://www.apple.com/newsroom/2026/08/apple-unveils-a-more-powerful-mac-mini-featuring-the-all-new-m6-and-m5-pro/)
3. [The $899 M6 Mac mini Isn't the AI Mac Apple Benchmarked — Kingy AI](https://kingy.ai/blog/m6-mac-mini-local-ai-edge-llm/)
4. [The Potential of M6 and M5 Ultra for Local AI on macOS — MacStories](https://www.macstories.net/notes/the-potential-of-m6-and-m5-ultra-for-local-ai-on-macos/)
5. [Local LLM Hardware Showdown — The Agent Times](https://theagenttimes.com/articles/local-llm-hardware-showdown-reveals-no-clear-winner-for-agen-ef110f7c)
6. [Apple Silicon apunta alto: un M5 Max mueve un modelo de 122B en local](https://noticias.ai/apple-silicon-apunta-alto-un-m5-max-mueve-un-modelo-de-122b-en-local/)
7. [New Mac Studio Can Be Clustered Together for Faster AI Performance — MacRumors](https://www.macrumors.com/2026/08/26/new-mac-studio-can-be-clustered-together/)
8. [4 台苹果 Mac Studio 池化 1.5TB 内存，DeepSeek V3.1 AI 推理速度提高 122.6% — IT之家](https://m.ithome.com/html/907113.htm)
9. [苹果发布全新Mac Studio：M5 Max/Ultra双芯加持 — ZOL](https://pc.zol.com.cn/1238/12382882.html)
