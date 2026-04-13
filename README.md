# Hermes Agent

<p align="center">
  <a href="https://github.com/joaomj/hermes-agent-fork/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge" alt="Python 3.11+">
</p>

A self-improving AI agent for personal use. Runs in your terminal, connects via Telegram, and remembers across sessions. Use any LLM provider -- [OpenRouter](https://openrouter.ai), [z.ai/GLM](https://z.ai), OpenAI, Anthropic, or your own endpoint. Switch with `hermes model`.

Fork of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com), with ~30,000 lines of removed code (RL training, 13 gateway adapters, marketplace infrastructure, vendor-specific routing). See [docs/roadmap.md](docs/roadmap.md) for the full simplification history.

---

## What It Does

<table>
<tr><td><b>Terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Telegram + API gateway</b></td><td>Telegram bot and HTTP API server from a single gateway process. Cross-platform conversation continuity.</td></tr>
<tr><td><b>Local skills and memory</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation from experience. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Local-only skill loading.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Cron scheduler (opt-in toolset). Daily reports, nightly backups, weekly audits -- all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere</b></td><td>Terminal backends: local, Docker, SSH, and Modal. Run it on a $5 VPS or a GPU cluster.</td></tr>
</table>

---

## Install

**One-line install (Linux/macOS):**

```bash
curl -fsSL https://raw.githubusercontent.com/joaomj/hermes-agent-fork/main/scripts/install.sh | bash
```

**From source:**

```bash
git clone https://github.com/joaomj/hermes-agent-fork.git
cd hermes-agent-fork
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all]"
hermes setup
```

**After installation:**

```bash
source ~/.zshrc    # or ~/.bashrc
hermes             # start chatting
```

---

## Getting Started

```bash
hermes              # Interactive CLI -- start a conversation
hermes model        # Choose your LLM provider and model
hermes tools        # Configure which tools are enabled
hermes config edit  # Open config in your editor
hermes gateway      # Start the messaging gateway (Telegram + API server)
hermes setup        # Full setup wizard (API keys, model, tools)
hermes doctor       # Diagnose configuration issues
```

### CLI vs Messaging

Hermes has two entry points: start the terminal UI with `hermes`, or run the gateway and talk to it from Telegram or via the API server. Slash commands are shared across both.

| Action | CLI | Telegram / API |
|---------|-----|----------------|
| Start chatting | `hermes` | `hermes gateway start`, then message the bot |
| Fresh conversation | `/new` or `/reset` | `/new` or `/reset` |
| Change model | `/model [provider:model]` | `/model [provider:model]` |
| Set personality | `/personality [name]` | `/personality [name]` |
| Retry / undo | `/retry`, `/undo` | `/retry`, `/undo` |
| Context / usage | `/compress`, `/usage` | `/compress`, `/usage` |
| Interrupt | `Ctrl+C` or new message | `/stop` or new message |

---

## Documentation

| Document | What's Covered |
|----------|---------------|
| [AGENTS.md](AGENTS.md) | Development guide -- project structure, architecture, coding conventions |
| [docs/tech-context.md](docs/tech-context.md) | Technical deep-dive -- classes, data flow, key decisions |
| [docs/roadmap.md](docs/roadmap.md) | Project roadmap and simplification history |

Upstream documentation at [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/) covers most features in detail (CLI usage, configuration, tools, skills, memory, MCP integration, security, context files).

---

## Development

```bash
git clone https://github.com/joaomj/hermes-agent-fork.git
cd hermes-agent-fork
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
python -m pytest tests/ -q
```

---

## License

MIT -- see [LICENSE](LICENSE).

Original work by [Nous Research](https://nousresearch.com). Fork modifications under the same license.
