# Hermes Agent Fork

<p align="center">
  <a href="https://github.com/joaomj/hermes-agent-fork/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/NousResearch/hermes-agent"><img src="https://img.shields.io/badge/Fork%20of-Hermes%20Agent-blueviolet?style=for-the-badge" alt="Fork of Hermes Agent by Nous Research"></a>
</p>

A streamlined fork of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com) -- simplified for use as a personal AI assistant. Roughly 45,000 lines of dead code, niche integrations, voice/TTS subsystems, and vendor-specific infrastructure have been removed. The codebase is leaner, easier to maintain, and simpler to extend.

Use any model you want -- [OpenRouter](https://openrouter.ai) (200+ models), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), OpenAI, Anthropic, or your own endpoint. Switch with `hermes model` -- no code changes, no lock-in.

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Telegram + API gateway</b></td><td>Telegram bot and API server from a single gateway process. Cross-platform conversation continuity.</td></tr>
<tr><td><b>Local skills and memory</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation from experience. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Local-only skill loading.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Cron scheduler (opt-in toolset). Daily reports, nightly backups, weekly audits -- all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere</b></td><td>Terminal backends: local, Docker, SSH, and Modal. Run it on a $5 VPS or a GPU cluster.</td></tr>
</table>

---

## What Changed from Upstream

This fork completed a [simplification refactor](docs/roadmap.md) (Phase 1) across 14 commits:

| Removed | Lines | Step |
|---------|-------|------|
| RL training subsystem (Atropos, batch runner, trajectory compressor) | ~11,700 | 1a |
| Gateway adapters (Discord, Slack, WhatsApp, Signal, Matrix, Feishu, WeChat, DingTalk, Mattermost, Email, SMS, Home Assistant, Webhook) | ~12,200 | 1b |
| Memory plugins (holographic, openviking, hindsight, mem0, byterover, retaindb) | ~3,000 | 1c |
| Skills marketplace/hub and security scanner | ~4,000 | 1d |
| Mixture-of-agents tool; moved image gen, TTS, cron, Home Assistant to opt-in toolsets | ~3,200 | 1e |
| Static assets (website, landing page) | ~3.7MB | 1f |
| Voice mode, TTS, STT/transcription, Camofox browser backend | ~15,000+ | 1g |
| Nous-managed tool gateway and subscription routing | -- | 1g |
| Daytona and Singularity terminal backends | -- | 1g |

Steps 1h (config consolidation) and 1j (plugin file merge) were analyzed and deferred -- too risky without a dedicated spec.

See the full [roadmap](docs/roadmap.md) and [simplification plan](docs/simplification-plan.md) for details.

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Works on Linux and macOS. The installer handles everything -- Python, Node.js, dependencies, and the `hermes` command. No prerequisites except git.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
hermes              # start chatting!
```

---

## Getting Started

```bash
hermes              # Interactive CLI -- start a conversation
hermes model        # Choose your LLM provider and model
hermes tools        # Configure which tools are enabled
hermes config set   # Set individual config values
hermes gateway      # Start the messaging gateway (Telegram, API server)
hermes setup        # Run the full setup wizard (configures everything at once)
hermes update       # Update to the latest version
hermes doctor       # Diagnose any issues
```

## CLI vs Messaging Quick Reference

Hermes has two entry points: start the terminal UI with `hermes`, or run the gateway and talk to it from Telegram or via the API server. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action | CLI | Telegram / API |
|---------|-----|----------------|
| Start chatting | `hermes` | Run `hermes gateway setup` + `hermes gateway start`, then send the bot a message |
| Start fresh conversation | `/new` or `/reset` | `/new` or `/reset` |
| Change model | `/model [provider:model]` | `/model [provider:model]` |
| Set a personality | `/personality [name]` | `/personality [name]` |
| Retry or undo the last turn | `/retry`, `/undo` | `/retry`, `/undo` |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| Browse skills | `/<skill-name>` | `/<skill-name>` |
| Interrupt current work | `Ctrl+C` or send a new message | `/stop` or send a new message |
| Platform-specific status | `/platforms` | `/status`, `/sethome` |

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Simplification Refactor | Remove ~45k lines of dead/niche code, voice, TTS, vendor infrastructure | Completed |
| 2. Unified Knowledge Base | Filesystem-first knowledge layer (markdown + FTS5) | Planning |
| 3. Deep Research Tool | Multi-step research with source trust hierarchy | Planning |
| 4. Rust Port | Full Python-to-Rust rewrite (long-term) | Long-term |

See [docs/roadmap.md](docs/roadmap.md) for details.

---

## Documentation

Upstream documentation lives at **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**. Most content applies to this fork. Differences are documented in [docs/roadmap.md](docs/roadmap.md).

| Section | What's Covered |
|---------|---------------|
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | Install, setup, first conversation |
| [CLI Usage](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | Commands, keybindings, personalities, sessions |
| [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | Config file, providers, models, all options |
| [Security](https://hermes-agent.nousresearch.com/docs/user-guide/security) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 20+ tools, toolset system, terminal backends |
| [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | Procedural memory, local skill creation |
| [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | Persistent memory, user profiles, best practices |
| [MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | Connect any MCP server for extended capabilities |
| [Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | Project context that shapes every conversation |
| [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | Project structure, agent loop, key classes |

---

## Contributing

Quick start for contributors:

```bash
git clone https://github.com/joaomj/hermes-agent-fork.git
cd hermes-agent-fork
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m pytest tests/ -q
```

---

## Upstream

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com)

---

## License

MIT -- see [LICENSE](LICENSE).

Original work by [Nous Research](https://nousresearch.com). Fork modifications under the same license.
