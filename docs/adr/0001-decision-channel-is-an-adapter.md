# Decision channel is an adapter over the run state machine

The daily run's human decision points (topic selection and narrative selection) are
presented today through a CLI/TUI, but the TUI is a presentation surface, not the
source of truth. We decided that the durable decision contract is `run_id + decision_id
+ awaiting_* state + resume`, and that every channel — CLI, email, Telegram, or a future
WeChat adapter — is just an adapter that renders the decision request, accepts the reply,
and records the same choice through the same resume path. No channel owns workflow truth.

## Contract

- A decision request is versioned and always carries the run's `run_id` and a stable
  `decision_id`; it names the choices and the accepted reply shape.
- Reaching a decision point writes a durable `awaiting_topic` or `awaiting_narrative`
  state and ends the turn; the process never blocks waiting for a live reply.
- An adapter records the chosen value through the existing choice-recording function and
  then triggers the same resume entry point the CLI uses.
- At the topic gate, an adapter may also accept an explicit editor-specified topic. It
  is recorded as a normal human choice with no inherited factual claims; the existing
  research stage remains responsible for establishing the event and its evidence.
- Any channel may present and accept the decision, but each references the same
  `run_id`/`decision_id`; local chat and channel state are caches, never the truth.

## Consequences

- Adding or replacing a channel (CLI → Telegram → email) does not change the state
  machine; the TUI remains one adapter among several.
- Full-duplex adapters (Telegram bot, email/IMAP) can both push the request and accept
  the reply. WeChat has no compliant personal-account inbound bot API, so WeChat is a
  notification-only channel or uses WeCom; it is not assumed to accept in-band decisions.
