# Hermes Agent Fork - Roadmap

---

## Phase 1: Simplification Refactor

**Branch:** `refactor/simplify`
**Status:** Completed

Remove unnecessary interfaces, integrations, and dead code to reduce the codebase by ~30,000 lines. A leaner codebase is easier to maintain, test, and port. Run this first -- work on a smaller surface.

Implemented through steps 1a-1g. Steps 1h and 1j were analyzed and deferred for future follow-up.

### 1.1 Remove RL Training Subsystem (~11,700 lines)

The entire RL training pipeline is self-contained with no connection to core agent functionality.

| Remove | Lines | Description |
|--------|-------|-------------|
| `tools/rl_training_tool.py` | 1,402 | 10 RL training tools (Tinker-Atropos) |
| `rl_cli.py` | 446 | RL Training CLI runner |
| `batch_runner.py` | 1,285 | Parallel batch processing for RL data gen |
| `mini_swe_runner.py` | 709 | SWE benchmark runner |
| `trajectory_compressor.py` | 1,518 | RL trajectory post-processing |
| `toolset_distributions.py` | 364 | Toolset probability distributions for RL |
| `environments/` (entire dir) | 7,175 | Atropos training envs + 11 tool call parsers |
| `tinker-atropos/` | -- | Empty submodule placeholder |
| `datagen-config-examples/` | -- | RL pipeline YAML configs |

Also remove `rl_training_tool` from `_discover_tools()` in `model_tools.py` and `_HERMES_CORE_TOOLS` in `toolsets.py`.

### 1.2 Remove Gateway Adapters Except Telegram + API Server (~12,200 lines)

Keep only `telegram.py`, `telegram_network.py`, `base.py`, and `api_server.py`.

| Remove | Lines | Description |
|--------|-------|-------------|
| `discord.py` | 2,346 | Discord bot adapter |
| `feishu.py` | 3,255 | Feishu/Lark (Chinese enterprise) |
| `wecom.py` | 1,338 | WeChat Work (Chinese enterprise) |
| `dingtalk.py` | 340 | DingTalk (Chinese enterprise) |
| `slack.py` | 998 | Slack bot adapter |
| `whatsapp.py` | 941 | WhatsApp adapter |
| `signal.py` | 807 | Signal adapter |
| `matrix.py` | 1,217 | Matrix adapter |
| `email.py` | 621 | IMAP/SMTP adapter |
| `mattermost.py` | 723 | Mattermost adapter |
| `webhook.py` | 616 | Generic webhook receiver |
| `sms.py` | 276 | Twilio SMS adapter |
| `homeassistant.py` | 449 | HA gateway adapter |

Also remove their tests and gateway dispatch code for these platforms in `gateway/run.py`.

### 1.3 Consolidate Memory Plugins (~3,000 lines removed)

Remove 6 memory provider plugins, keep only Honcho:

| Keep | Remove |
|------|--------|
| `plugins/memory/honcho/` (3,389 lines) | `plugins/memory/holographic/` (1,778 lines) |
| `plugins/memory/__init__.py` (discovery) | `plugins/memory/openviking/` (582 lines) |
| | `plugins/memory/hindsight/` (358 lines) |
| | `plugins/memory/mem0/` (344 lines) |
| | `plugins/memory/byterover/` (383 lines) |
| | `plugins/memory/retaindb/` (302 lines) |

### 1.4 Simplify Skills System (~4,000 lines removed)

Strip to local-only skill loading. Remove the marketplace/hub infrastructure:

| Remove | Lines | Description |
|--------|-------|-------------|
| `tools/skills_hub.py` | 2,707 | Full skill registry/marketplace with GitHub auth |
| `tools/skills_guard.py` | 1,105 | Security scanner for community skills |
| `hermes_cli/skills_hub.py` | 1,219 | CLI `/skills` marketplace command |

Keep: `tools/skills_tool.py` (agent reads local skills), `tools/skill_manager_tool.py` (agent creates skills), `tools/skills_sync.py` (manifest sync), `agent/skill_commands.py` (slash commands), local `~/.hermes/skills/`, plus bundled `_skills-available/` and `_optional-skills-available/` directories.

### 1.5 Remove Niche Tools from Core (~3,200 lines from tool schemas)

Move these out of `_HERMES_CORE_TOOLS` into opt-in toolsets or remove entirely:

| Tool | Lines | Action |
|------|-------|--------|
| `tools/mixture_of_agents_tool.py` | 562 | Remove -- experimental, 4x API calls per invocation |
| `tools/image_generation_tool.py` | 703 | Move to `image_gen` opt-in toolset (zero tests) |
| `tools/homeassistant_tool.py` | 490 | Move to `homeassistant` opt-in toolset |
| `tools/browser_camofox.py` + state | 618 | Move to `camofox` opt-in toolset |
| `tools/cronjob_tools.py` | 458 | Move to `cron` opt-in toolset |
| `tools/voice_mode.py` | 812 | Keep but make fully lazy/optional |
| `tools/tts_tool.py` + `neutts_synth.py` | 990 | Move to `tts` opt-in toolset |

### 1.6 Remove Static Assets

| Remove | Description |
|--------|-------------|
| `website/` (3.4MB) | Docusaurus docs site -- separate project |
| `landingpage/` (316KB) | Static landing page -- separate project |

### 1.7 Architectural Simplification (Higher Effort)

| Task | Description |
|------|-------------|
| Consolidate config loaders | Merge 3 separate config systems (`cli.py`, `hermes_cli/config.py`, `gateway/run.py`) into one canonical loader |
| Remove Nous-specific routing | `tools/managed_tool_gateway.py` + `hermes_cli/nous_subscription.py` -- vendor-specific infrastructure |
| Merge `hermes_cli/plugins.py` + `plugins_cmd.py` | Two files doing one job |
| Remove niche terminal environments | `daytona.py` and `singularity.py` -- very few users |

### Phased Delivery

| Step | Deliverable | Test Gate |
|------|------------|-----------|
| 1a | Remove RL subsystem + static assets | Full test suite passes, no dangling imports |
| 1b | Remove all gateway adapters except Telegram + API server | Gateway tests pass for remaining platforms |
| 1c | Remove memory plugins (keep Honcho only) | Memory tests pass for Honcho |
| 1d | Strip skills system to local-only | Skill loading/creation still works |
| 1e | Move niche tools out of core | Tool discovery tests pass, opt-in toolsets work |
| 1f | Consolidate config loaders | All 3 entry points (CLI, setup, gateway) use single loader |
| 1g | Remove Nous-specific routing + merge plugin files | No vendor-specific code paths remain |

### Estimated Impact

| Metric | Before | After |
|--------|--------|-------|
| Python lines (tools/) | ~36,900 | ~29,700 |
| Python lines (gateway/platforms/) | ~14,100 | ~3,900 |
| Python lines (plugins/) | ~7,350 | ~3,600 |
| Total Python lines removed | -- | ~30,000+ |
| Static assets removed | -- | ~3.7MB |
| Tools in `_HERMES_CORE_TOOLS` | ~30 | ~20 |
| Gateway platform adapters | 15 | 2 (Telegram + API server) |

---

## Phase 2: Unified Knowledge Base

**Branch:** TBD
**Research:** `docs/to-study/about-memory-systems.md`

Filesystem-first, not RAG. The agent explores knowledge the same way it explores code -- with `ls`, `cat`, `grep`. No sqlite-vec, no embeddings, no L0/L1/L2 tiering. Just directories of markdown files and FTS5.

### Why Filesystem-First

AI agents thrive in filesystem architectures. The agent already knows how to navigate directories, read files, and search content -- why build a parallel retrieval system when `file_tools.py` already works?

Traditional RAG is passive: the agent receives chunks. Filesystem-first is active: the agent explores structure, drills down, cross-references. Meaning stays in context. Sources: [Mintlify ChromaFs](https://www.mintlify.com/blog/how-we-built-a-virtual-filesystem-for-our-assistant), [arXiv:2601.11672](https://arxiv.org/abs/2601.11672)

### Architecture

```
Knowledge Directory (source of truth)
~/.hermes/knowledge/
  bookmarks/        -- X bookmarks (one .md per tweet or thread)
  sessions/        -- Hermes session exports
  articles/        -- web_extract'd articles
  papers/          -- arXiv / PDF papers
  notes/           -- manual entries

Agent explores via file_tools (ls, cat, grep) -- no special tool needed
Agent searches via knowledge_search tool (FTS5 across all sources)
```

**No sqlite-vec, no embeddings, no L0/L1/L2.** FTS5 keyword search is sufficient for a personal knowledge base. If semantic search is needed later, add it as a thin layer over the existing FTS5 foundation.

**No separate SQLite index.** The markdown files are the index. Directories and filenames provide structure. Frontmatter provides metadata. No derived state to keep in sync.

### File Format

```markdown
---
source: https://x.com/user/status/123456
type: bookmark
author: username
bookmarked_at: 2026-04-03
tags: [topic, topic]
---

@username · Apr 3, 2026

Post text here. Full tweet content, no truncation.
Links, mentions, hashtags all preserved.
```

Frontmatter fields: `source`, `type` (bookmark/article/paper/session/note), `author`, `bookmarked_at`/`ingested`/`created_at`, `tags`. No enforced schema -- frontmatter is optional metadata.

### Data Sources

| Source | Storage | How agent accesses it |
|--------|---------|---------------------|
| X bookmarks | `bookmarks/*.md` | `cat` + `grep` via file_tools |
| Hermes sessions | `sessions/*.md` | `cat` + `grep` via file_tools |
| Articles | `articles/*.md` | `cat` + `grep` via file_tools |
| Papers | `papers/*.md` | `cat` + `grep` via file_tools |
| Notes | `notes/*.md` | `cat` + `grep` via file_tools |

### Tool: `knowledge_search`

```json
{
  "name": "knowledge_search",
  "description": "Search the local knowledge base (bookmarks, sessions, articles, papers, notes) using keyword search",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query"},
      "source": {"type": "string", "enum": ["all", "bookmarks", "sessions", "articles", "papers", "notes"], "default": "all"},
      "limit": {"type": "integer", "default": 10}
    },
    "required": ["query"]
  }
}
```

Internally: walks `~/.hermes/knowledge/<source>/`, does FTS5 across all `.md` files. Returns matching file paths + snippets. The agent then uses `cat` to read the full content.

### Tool: `knowledge_import`

```json
{
  "name": "knowledge_import",
  "description": "Import content into the knowledge base",
  "parameters": {
    "type": "object",
    "properties": {
      "url": {"type": "string", "description": "URL to extract and import"},
      "text": {"type": "string", "description": "Raw text to import as a note"},
      "type": {"type": "string", "enum": ["article", "paper", "note"], "default": "article"}
    }
  }
}
```

For URLs: calls `web_extract`, writes markdown to `articles/`. For text: wraps in minimal frontmatter, writes to `notes/`. For X bookmarks: reads `~/.hermes/x_bookmarks.db` directly, writes each bookmark to `bookmarks/`.

**Note:** X bookmark sync is now a read path, not a separate tool. The agent reads the SQLite DB and writes markdown on demand (or once, as a batch import). No continuous sync loop. User runs `hermes kb sync bookmarks` from CLI to import.

### CLI Commands

- `hermes kb search <query>` -- search from CLI, print results
- `hermes kb import <url|text>` -- import article or note
- `hermes kb sync bookmarks` -- batch import X bookmarks from SQLite to markdown
- `hermes kb ls [source]` -- list entries by source
- `hermes kb stats` -- count entries per source

### What NOT to Build

- No sqlite-vec or vector embeddings
- No L0/L1/L2 tiered context (Hermes already has context compression)
- No sqlite-vec / embedding generation pipeline
- No separate `knowledge.db` index -- files are the index
- No continuous X bookmark sync -- just batch import on demand

### Phased Delivery

| Step | Deliverable | Test Gate |
|------|------------|-----------|
| 2a | File layout + `knowledge_search` FTS5 tool over bookmarks | Search accuracy tests against fixture bookmarks |
| 2b | Session and article sources in `knowledge_search` | Each source searchable |
| 2c | `knowledge_import` for URL and text | Import fixtures, verify files written |
| 2d | `hermes kb` CLI commands | CLI manual test |
| 2e | X bookmark batch import (`hermes kb sync bookmarks`) | Import fixture DB, verify markdown files |

---

## Phase 3: Deep Research Tool

**Branch:** `feat/deep-research`
**Plan:** `docs/deep-research-plan.md`

Multi-step research tool with a source trust hierarchy (arXiv, Semantic Scholar, Wikipedia, filtered web search). Accessible via CLI and Telegram as a registered tool. Results feed into the Knowledge Base (Phase 2) as papers and articles.

**Sub-phases:**

1. Skeleton -- tool registration, schema, handler stub, integration in model_tools + toolsets
2. Tier 1 fetchers -- arXiv API client, Semantic Scholar API client, Wikipedia API client
3. Tier 2/3 fetchers -- web_search integration with domain filtering
4. Ranking + synthesis -- tier ranking, recency scoring, citation weighting, report generation
5. Test suite -- unit + integration tests
6. Manual verification -- CLI test, then Telegram test

**Dependencies:** `httpx`, existing `web_tools` functions. No new API keys needed.

---

## Phase 4: Rust Port (Long-Term)

**Branch:** TBD
**Status:** Long-term goal, not actively in progress

Full Python-to-Rust rewrite of the Hermes Agent codebase for improved performance. Targets the simplified architecture from Phase 1.

### Prerequisites

- Phases 1-3 shipped and stable
- Simplification refactor (Phase 1) completed -- port targets the lean codebase
- Feasibility study completed: audit all Python dependencies for Rust crate equivalents, benchmark current hot paths

### Phased Approach

1. **Feasibility study** -- Audit dependencies, map module dependency graph, identify Rust crate equivalents, benchmark Python hot paths
2. **Core foundation** -- Agent loop, LLM provider clients (OpenAI-compatible), tool dispatch framework, message types
3. **Tool ports** -- Incremental, maintaining Python FFI bridge for complex tools. Priority by usage frequency: terminal, file, web, delegate, then browser, MCP, etc.
4. **CLI + Gateway** -- CLI with `clap` + `reedline`, skin engine port, Telegram adapter, API server, session persistence
5. **Testing + Migration** -- Port or rewrite test suite, configuration migration from Python format, parallel deployment for A/B validation

### Preliminary Rust Crate Mapping

| Component | Rust Crate |
|-----------|-----------|
| Async runtime | `tokio` |
| HTTP client | `reqwest` |
| LLM API | `async-openai` or custom |
| CLI framework | `clap` |
| Terminal UI | `indicatif` + `console` |
| SQLite | `rusqlite` or `sqlx` |
| YAML config | `serde_yaml` |
| OAuth 2.0 | `oauth2` |
| Serialization | `serde` + `serde_json` |

---

## Dependency Graph

```
Phase 1: Simplification Refactor  <-- FIRST: clean the surface
    |   <-- removes ~30,000 lines of niche/dead code
    |   <-- reduces gateway to Telegram + API server
    |   <-- consolidates memory plugins to Honcho only
    |   <-- strips skills to local-only
    v
Phase 2: Unified Knowledge Base
    |   <-- filesystem-first: directories of markdown + FTS5
    |   <-- no sqlite-vec, no embeddings, no tiered context
    |   <-- X bookmarks as one source (read from SQLite, write markdown)
    v
Phase 3: Deep Research Tool  --> feeds into Phase 2 (KB import)
    |
    v
Phase 4: Rust Port  <-- targets simplified architecture from Phases 1-3
```

Phase 1 can run immediately since it removes self-contained subsystems. Phase 3's feasibility study can run in parallel with Phase 2.

## References

- `docs/to-study/about-memory-systems.md` -- curated list of articles and repos on agent memory systems
- `docs/deep-research-plan.md` -- Phase 3 implementation plan
- `docs/honcho-integration-spec.md` -- existing Honcho integration architecture and patterns
- `plugins/memory/honcho/` -- existing Honcho memory provider plugin (client, session, CLI)
- [Mintlify: How we built a virtual filesystem for our Assistant](https://www.mintlify.com/blog/how-we-built-a-virtual-filesystem-for-our-assistant) -- ChromaFs pattern: virtual filesystem over indexed data
- [arXiv 2601.11672: From Everything-is-a-File to Files-Are-All-You-Need](https://arxiv.org/abs/2601.11672) -- Unix philosophy applied to agentic AI design
- [Honcho](https://github.com/plastic-labs/honcho) -- memory library with dialectical reasoning
