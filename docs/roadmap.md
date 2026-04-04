# Hermes Agent Fork - Roadmap

---

## Phase 1: Deep Research Tool

**Branch:** `feat/deep-research`
**Plan:** `docs/deep-research-plan.md`

Multi-step research tool with a source trust hierarchy (arXiv, Semantic Scholar, Wikipedia, filtered web search). Accessible via CLI and Telegram as a registered tool.

**Sub-phases:**

1. Skeleton -- tool registration, schema, handler stub, integration in model_tools + toolsets
2. Tier 1 fetchers -- arXiv API client, Semantic Scholar API client, Wikipedia API client
3. Tier 2/3 fetchers -- web_search integration with domain filtering
4. Ranking + synthesis -- tier ranking, recency scoring, citation weighting, report generation
5. Test suite -- unit + integration tests
6. Manual verification -- CLI test, then Telegram test

**Dependencies:** `httpx`, existing `web_tools` functions. No new API keys needed.

---

## Phase 2: X Bookmarks Tool

**Branch:** `feat/x-bookmarks`

Hermes tool that syncs your X bookmarks to a local SQLite database, queryable by the agent. This is the first data source feeding into the future Knowledge Base (Phase 4).

### 2.1 API and Auth

- X API v2 `GET /2/users/{id}/bookmarks` endpoint
- OAuth 2.0 user-context with scopes: `bookmark.read`, `tweet.read`, `users.read`
- Manual setup: user creates X developer app, configures `X_CLIENT_ID`, `X_CLIENT_SECRET`, `X_ACCESS_TOKEN`, `X_REFRESH_TOKEN` in `~/.hermes/.env`
- Tool handles token refresh automatically using the refresh token
- Add to `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`

### 2.2 Database Schema (`~/.hermes/x_bookmarks.db`)

```sql
CREATE TABLE bookmarks (
    tweet_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    note_tweet_text TEXT,
    author_id TEXT NOT NULL,
    author_username TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bookmarked_at TEXT NOT NULL,
    conversation_id TEXT,
    in_reply_to_tweet_id TEXT,
    lang TEXT,
    retweet_count INTEGER,
    reply_count INTEGER,
    like_count INTEGER,
    bookmark_count INTEGER,
    impression_count INTEGER,
    raw_json TEXT
);

CREATE TABLE sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE VIRTUAL TABLE bookmarks_fts USING fts5(
    text, note_tweet_text, author_username,
    content=bookmarks,
    content_rowid=rowid,
    tokenize='unicode61'
);
```

Text-only storage. No media, no URL extraction tables. Articles linked in posts will be handled by the Knowledge Base ingestion pipeline (Phase 4), not by this tool.

### 2.3 Tool Schema

```json
{
  "name": "x_bookmarks",
  "description": "Sync and query your X/Twitter bookmarks from a local database",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["sync", "search", "stats", "recent"],
        "description": "sync: fetch new bookmarks, search: FTS query, stats: count/summary, recent: last N bookmarks"
      },
      "query": {"type": "string", "description": "Search query (for action=search)"},
      "limit": {"type": "integer", "description": "Max results (for search/recent, default 10)"},
      "full_sync": {"type": "boolean", "description": "Force full re-fetch instead of incremental (default: false)"}
    },
    "required": ["action"]
  }
}
```

### 2.4 Integration Points

1. `tools/x_bookmarks.py` -- new tool file with all logic
2. `model_tools.py` -- add `import tools.x_bookmarks` to `_discover_tools()`
3. `toolsets.py` -- add `x_bookmarks` to `web` toolset (or new `knowledge` toolset)
4. `hermes_cli/config.py` -- add X env vars to `OPTIONAL_ENV_VARS`
5. `hermes_constants.py` -- DB path via `get_hermes_home() / "x_bookmarks.db"`

### 2.5 Phased Delivery

| Step | Deliverable | Test Gate |
|------|------------|-----------|
| 2a | DB schema + migration, env vars config | Schema creates cleanly, config loads |
| 2b | X API client (auth, pagination, rate limiting) | Unit tests with mocked responses |
| 2c | Sync logic (incremental + full) | Integration test with fixture data |
| 2d | Search/query actions (FTS5) | Search accuracy tests |
| 2e | Tool registration + agent integration | CLI manual test |

### 2.6 Technical Notes

- **Rate limits:** Respect `x-rate-limit-*` headers, store reset times in `sync_state`
- **Pagination:** `max_results=100` per page, paginate via `next_token`. Incremental sync stops when hitting a bookmark already in the DB
- **Profile-safe:** DB path uses `get_hermes_home()`, each profile gets its own bookmarks DB
- **Token refresh:** Tool checks OAuth 2.0 token expiry before each call, refreshes automatically

---

## Phase 3: Knowledge Base and Memory Layer

**Branch:** TBD
**Research:** `docs/to-study/about-memory-systems.md`

### Vision

A personal knowledge base -- built from and for the user -- where Hermes Agent ingests papers, articles, blog posts, X posts, past sessions, and memories into a unified local store. The agent explores and reasons over this knowledge to provide better, more personalized responses over time. This is the foundation for Hermes to truly learn from the user.

### Research Foundation

The study materials in `docs/to-study/about-memory-systems.md` inform three key design decisions:

**1. Filesystem-first, not chunked RAG**

Traditional RAG embeds document chunks into vectors and retrieves top-K matches. This is structurally limited: meaning spans across chunks, across documents, across topics. The agent receives fragments with no structural context -- no sense of where a chunk sits in the hierarchy of ideas. It is like trying to understand a book by reading five random paragraphs.

The alternative converging across the industry is the filesystem approach. Mintlify built ChromaFs -- a virtual filesystem over their Chroma database where each doc page is a file and each section is a directory. The agent navigates with `grep`, `cat`, `ls`, `find` -- exploring structure, drilling down, cross-referencing, building its own mental model. With RAG the agent is passive (receives chunks). With a filesystem the agent is active (explores structure). Session creation dropped from 46 seconds to 100ms.

The paper "From Everything-is-a-File to Files-Are-All-You-Need" (arXiv:2601.11672) formalizes this: file-like abstractions and code-based specifications collapse diverse resources into consistent, composable interfaces that are more maintainable, auditable, and operationally robust for agents.

Hermes already has `file_tools.py` -- the agent already knows how to explore filesystems. The knowledge base should work the same way.

> Sources: [Mintlify ChromaFs](https://www.mintlify.com/blog/how-we-built-a-virtual-filesystem-for-our-assistant), [arXiv:2601.11672](https://arxiv.org/abs/2601.11672)

**2. Memory as Reasoning (not just storage)**

The dominant approach in agent memory is extract-facts-embed-store-retrieve. Plastic Labs argues this is skeuomorphic -- it copies database patterns into AI systems without leveraging what LLMs actually do well: reasoning. Their thesis: memory should be treated as a prediction task powered by logical reasoning (deductive, inductive, abductive). Instead of storing static facts, the system reasons over data to produce composable conclusions about the user that can be re-synthesized at inference time.

This is Honcho's secret sauce: it is not that Honcho has a better database. It is that Honcho applies a good LLM to reason over the user's data. The storage (Postgres + pgvector) is standard. What makes Honcho valuable is the dialectical reasoning layer -- `peer.chat()` takes a natural language question and returns reasoning-informed conclusions drawn from everything Honcho knows about the user.

For the knowledge base, this means: local search retrieves. Honcho (or an equivalent reasoning step) synthesizes. These are complementary capabilities.

> Source: [Memory as Reasoning](https://blog.plasticlabs.ai/blog/Memory-as-Reasoning)

**3. Tiered Context (L0/L1/L2)**

OpenViking introduces a three-tier content model: L0 (one-sentence summary for routing), L1 (core information for planning), L2 (full original data for deep reading). This avoids the all-or-nothing problem of stuffing entire documents into context. Combined with Hermes' existing context compression, this could dramatically reduce token usage while preserving relevance.

> Source: [OpenViking](https://github.com/volcengine/OpenViking)

### Data Sources

| Source | Ingestion Method | Content Type |
|--------|-----------------|--------------|
| X bookmarks | Phase 2 tool (already in SQLite) | Posts, threads |
| Papers (arXiv, etc.) | Deep Research tool results, direct PDFs | Academic papers |
| Articles and blog posts | `web_extract` via URL or RSS feeds | Long-form text |
| Chat sessions | Session history export | Conversations |
| Memories | Existing Hermes memory system | Notes, preferences |
| Manual entries | Direct text/file input | Any text |

### Current State of Memory in Hermes

Hermes already has a learning system:

- **Memory files** (`~/.hermes/memories/`) -- flat text files for user notes and preferences, read at session start, writable via the `memory` tool
- **Session history** -- full conversation logs stored in SQLite with FTS5 search (`hermes_state.py`)
- **Skill creation from experience** -- Hermes can create and improve skills from usage patterns
- **Cross-session user modeling** -- builds a model of the user across sessions
- **Honcho integration** -- existing integration (`plugins/memory/honcho/`, `docs/honcho-integration-spec.md`) with four tools (`honcho_profile`, `honcho_search`, `honcho_context`, `honcho_conclude`), async prefetch, per-peer memory modes, dialectical reasoning

What is missing: no unified schema across sources, no filesystem-style knowledge exploration, no semantic search over external content, no cross-referencing between memories and other knowledge, no tiered context loading, no automated ingestion pipeline for external content.

### Architecture: Filesystem-First with Search Acceleration

```
Data Sources --> Ingestion Pipeline --> Markdown Files (source of truth)
                                        + SQLite Index (derived, rebuildable)
                                              |
                              +---------------+---------------+
                              |                               |
                        Agent explores                  Agent queries
                   via existing file_tools          via knowledge_search tool
                   (ls, cat, grep, find)            (FTS5 + sqlite-vec)
                              |                               |
                              +---------------+---------------+
                                              |
                                     Reasoning Layer (optional)
                                     Honcho dialectical API or
                                     local LLM reasoning step
                                              |
                                              v
                                       Agent Context
```

**Source of truth: Markdown files on disk.**

```
~/.hermes/knowledge/
  topics/
    memory-systems.md
    rust-async-runtime.md
    x-api-bookmarks.md
  sources/
    x-bookmarks/
      2026-04-03-abc123.md
    papers/
      2601.11672-everything-is-a-file.md
    articles/
      mintlify-virtual-filesystem.md
    sessions/
      2026-04-03-project-foo.md
```

Why markdown files, not just a database:

- **Human-readable and agent-readable.** You can read and edit your knowledge base with any text editor. The agent can read it with `cat`. No serialization barrier.
- **Structural metadata for free.** Headings (`#`, `##`) create hierarchy. Links (`[text](url)`) create cross-references. The agent can `grep` for headings to navigate, just like navigating a codebase.
- **Composable via filesystem.** A directory of markdown files is a filesystem. The agent can `ls` to see topics, `cat` to read, `grep` to search. This is the ChromaFs / "everything is a file" pattern. Hermes already has `file_tools.py` -- the agent already knows how to do this.
- **No schema lock-in.** SQLite tables force you to predict what fields you will need. Markdown with YAML frontmatter gives you structured metadata where needed without constraining the format.
- **Resilient.** If the index gets corrupted, `hermes knowledge rebuild-index` regenerates it from the files. The files are always the source of truth.
- **Portable.** Standard markdown. Works with git, any editor, any static site generator, any future tool.

**Search acceleration: SQLite index (derived artifact).**

A single SQLite database at `~/.hermes/knowledge.db` (profile-safe via `get_hermes_home()`) provides fast search over the markdown content:

- **FTS5** for keyword/exact match -- already used in Hermes sessions, extend to knowledge base
- **sqlite-vec** for semantic/concept match -- brute-force KNN is acceptable for a personal-scale dataset
- **File tracking** -- maps each markdown file to its indexed state (path, hash, last indexed timestamp). Detects new/modified/deleted files for incremental reindexing

The index is always derivable from the markdown files. It exists for speed, not for storage.

**Context tiering:** Every markdown file gets three representations stored in the index:
- **L0** -- one-sentence summary (~100 tokens) for relevance routing
- **L1** -- core information + key points (~2k tokens) for planning
- **L2** -- the full markdown file itself (unbounded, read directly from disk)

The `knowledge_search` tool retrieves L0 summaries first to identify relevant items, then promotes to L1 or reads L2 from disk as needed.

### File Format

Each markdown file uses YAML frontmatter for metadata:

```markdown
---
title: "How we built a virtual filesystem for our Assistant"
source: https://www.mintlify.com/blog/how-we-built-a-virtual-filesystem-for-our-assistant
type: article
authors: ["Dens Sumesh"]
tags: [filesystem, rag, agents, virtual-filesystem]
ingested: 2026-04-04
---

# How we built a virtual filesystem for our Assistant

RAG is great, until it isn't. Our assistant could only retrieve chunks
of text that matched a query...

## The Container Bottleneck
...
```

Frontmatter fields:
- `title` -- human-readable title
- `source` -- original URL or reference (optional for manual entries)
- `type` -- one of: `article`, `paper`, `post`, `session`, `memory`, `note`
- `authors` -- list of author names (optional)
- `tags` -- freeform tags for categorization
- `ingested` -- date the file was added to the knowledge base
- Additional fields allowed per source type (e.g., `tweet_id`, `arxiv_id`, `session_id`)

### Memory System Comparison

Four candidate systems evaluated from the research materials:

| Dimension | Honcho | mem0 | OpenViking | Local-first (markdown + sqlite) |
|-----------|--------|------|------------|----------------------------------|
| **License** | AGPL-3.0 | Apache 2.0 | AGPLv3 | N/A (custom) |
| **Core model** | Peer paradigm (entity-centric) | User/Session/Agent scopes | Virtual filesystem (viking://) | Real filesystem (markdown files) |
| **Storage** | Postgres + pgvector | Configurable vector store | Local filesystem + LanceDB | Markdown files + SQLite index |
| **Retrieval** | Dialectical reasoning + hybrid search | Semantic search | Recursive directory retrieval | FTS5 + sqlite-vec + file_tools |
| **Reasoning** | Built-in (deriver worker, LLM-powered) | Fact extraction via LLM | VLM-based tiering | Optional (Honcho or local LLM) |
| **Dependencies** | Postgres, 4+ LLM providers | OpenAI default, configurable | C++ compiler, embedding + VLM models | sqlite-vec extension |
| **Human-editable** | No (stored in Postgres) | No (stored in vector DB) | Partial (filesystem but viking:// URIs) | Yes (standard markdown files) |
| **Rebuildability** | No (Postgres is source of truth) | No (vector store is source of truth) | Partial | Yes (index derived from files) |
| **Privacy** | Self-hosted possible but heavy | Self-hosted possible | Self-hosted | Fully local |

**Key insight:** The filesystem-first approach is orthogonal to Honcho. Markdown files + SQLite index handle storage and retrieval. Honcho handles reasoning. They compose:

- **Storage/retrieval:** Local markdown + FTS5 + sqlite-vec (always available, no dependencies)
- **Reasoning:** Honcho's dialectical API as an optional layer, or a local LLM call over retrieved results

This avoids the false choice between "Honcho vs. local-first." Honcho is not a storage system you commit to -- it is a reasoning service you layer on top of your own data.

### What Needs to Be Built

1. **File layout and conventions** -- Directory structure under `~/.hermes/knowledge/`, markdown frontmatter schema, naming conventions. This is the foundation everything else builds on.

2. **SQLite search index** -- `~/.hermes/knowledge.db` with FTS5 tables, sqlite-vec virtual tables, and a file tracking table (path, content hash, last indexed). Incremental reindexing: scan for new/modified/deleted files, update only what changed. A `hermes knowledge rebuild-index` command regenerates the full index from the markdown files.

3. **Ingestion pipeline** -- Per-source importers that write markdown files:
   - **X bookmarks importer** -- reads Phase 2's `x_bookmarks.db`, writes one markdown file per bookmark (or threads merged into a single file) into `sources/x-bookmarks/`
   - **Article importer** -- takes a URL, calls `web_extract`, writes markdown file into `sources/articles/`
   - **Paper importer** -- takes an arXiv ID or PDF, extracts text, writes into `sources/papers/`
   - **Session importer** -- exports past Hermes sessions into `sources/sessions/`
   - **Manual importer** -- takes raw text, wraps in frontmatter, writes into `topics/` or `sources/notes/`
   - Each importer generates L0/L1 summaries and updates the SQLite index

4. **Embedding generation** -- Embed markdown content for sqlite-vec. Options: `sqlite-lembed` for local `.gguf` model embeddings (fully offline), `sqlite-rembed` for API-based embeddings (OpenAI, etc.), or a custom embedding step during ingestion. The embedding is stored in the index, not in the markdown file.

5. **`knowledge_search` tool** -- Registered Hermes tool with two retrieval lanes:
   - **FTS5 lane** -- keyword search over indexed content
   - **sqlite-vec lane** -- semantic search via vector similarity
   - Results return L0 summaries by default. The agent can request L1 (from index) or L2 (reads the markdown file from disk). The agent can also use `file_tools` to explore the `knowledge/` directory directly -- no special tool needed for browsing.

6. **CLI commands** -- `hermes knowledge` subcommands:
   - `hermes knowledge import <url|file|text>` -- ingest content
   - `hermes knowledge search <query>` -- search from CLI
   - `hermes knowledge rebuild-index` -- regenerate SQLite index from files
   - `hermes knowledge stats` -- show counts by source type, index health

7. **Reasoning layer (optional)** -- After retrieval, optionally pass results through a reasoning step:
   - **Honcho path:** Send retrieved knowledge + user query to Honcho's dialectical API. Honcho returns synthesized conclusions.
   - **Local path:** Pass retrieved knowledge + user query to the agent's LLM with a reasoning prompt (deductive/inductive/abductive). No external service needed.
   - This step transforms "here are relevant documents" into "here is what your accumulated knowledge says about this question."

8. **Cross-session user modeling** -- Extend the existing memory system. When the agent learns something new about the user, write it as a markdown note in `topics/` with proper frontmatter and indexing. Over time, the `topics/` directory becomes a rich model of the user's interests, expertise, and preferences -- queryable and explorable just like any other knowledge.

### Honcho's Role

Having analyzed Honcho's actual value proposition (see `plugins/memory/honcho/` for the existing integration), the conclusion is:

**Honcho's value is the reasoning layer, not the storage layer.**

What Honcho actually does well:
- `peer.chat()` -- dialectical reasoning over accumulated user data. Takes a natural language question, returns reasoning-informed conclusions. This is genuinely hard to replicate locally without a dedicated reasoning model and pipeline.
- `honcho_profile` / peer cards -- pre-computed representations of the user that update asynchronously. Zero-latency at retrieval time.
- Cross-session accumulation -- builds a model of the user across all conversations, all projects. More holistic than per-session context.

What Honcho does not do well for this use case:
- Storage is Postgres + pgvector -- heavy infrastructure for a personal knowledge base
- AGPL-3.0 license -- copyleft constraint
- Data leaves the machine unless self-hosted (and self-hosting requires Postgres + worker processes)
- No filesystem interface -- the agent cannot `ls` or `grep` Honcho's storage

**Strategy:** Keep Honcho as-is for user modeling (the existing integration works well). Do not use Honcho as the knowledge base storage layer. The knowledge base is markdown files + SQLite index, fully local. If the reasoning layer proves valuable in practice, add Honcho's dialectical API as an optional post-retrieval step -- it reasons over the knowledge base results without owning the data.

### Phased Delivery

| Step | Deliverable | Test Gate |
|------|------------|-----------|
| 3a | Spec document -- file layout, frontmatter schema, index schema, importer interfaces | Spec reviewed |
| 3b | File layout + SQLite index -- directory structure, FTS5 + sqlite-vec tables, file tracking, `rebuild-index` command | Index builds from fixture markdown files, FTS5 search works |
| 3c | Ingestion pipeline core -- importer base class, X bookmarks importer (reads Phase 2 DB, writes markdown), manual text importer | Import X bookmarks fixtures, verify files written correctly, index updated |
| 3d | `knowledge_search` tool -- FTS5 + sqlite-vec dual-lane search, L0/L1/L2 tiering | Search accuracy tests against imported bookmarks |
| 3e | Article/paper importers -- `web_extract`-based URL ingestion, arXiv PDF ingestion | End-to-end import test |
| 3f | Session importer -- past Hermes conversations into markdown files | Import existing sessions |
| 3g | CLI commands -- `hermes knowledge import/search/rebuild-index/stats` | CLI manual test |
| 3h | Reasoning layer evaluation -- test Honcho dialectical API vs. local LLM reasoning over retrieved results with real usage data | Decision documented |

This phase requires its own spec document (step 3a) before implementation begins.

---

## Phase 4: Rust Port (Long-Term)

**Branch:** TBD
**Status:** Long-term goal, not actively in progress

Full Python-to-Rust rewrite of the Hermes Agent codebase for improved performance.

### Prerequisites

- Phase 1 and Phase 2 shipped and stable
- Knowledge Base architecture (Phase 3) finalized, so the Rust port targets the final architecture
- Feasibility study completed: audit all Python dependencies for Rust crate equivalents, benchmark current hot paths

### Phased Approach

1. **Feasibility study** -- Audit dependencies, map module dependency graph, identify Rust crate equivalents, benchmark Python hot paths
2. **Core foundation** -- Agent loop, LLM provider clients (OpenAI-compatible), tool dispatch framework, message types
3. **Tool ports** -- Incremental, maintaining Python FFI bridge for complex tools. Priority by usage frequency: terminal, file, web, delegate, then browser, MCP, etc.
4. **CLI + Gateway** -- CLI with `clap` + `reedline`, skin engine port, gateway platform adapters, session persistence
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
Phase 1: Deep Research
    |
    v
Phase 2: X Bookmarks  --+
    |                    |
    v                    v
Phase 3: Knowledge Base and Memory Layer
    |   <-- depends on data sources from Phase 2 (X bookmarks importer)
    |   <-- informed by memory systems research (docs/to-study/)
    |   <-- filesystem-first architecture: markdown files + SQLite index
    |   <-- Honcho as optional reasoning layer, not storage layer
    v
Phase 4: Rust Port (Long-Term)  <-- targets final architecture from Phases 1-3
```

Phase 4's feasibility study can run in parallel with Phases 2-3 since it is purely research.

## References

- `docs/to-study/about-memory-systems.md` -- curated list of articles and repos on agent memory systems
- `docs/deep-research-plan.md` -- Phase 1 implementation plan
- `docs/honcho-integration-spec.md` -- existing Honcho integration architecture and patterns
- `plugins/memory/honcho/` -- existing Honcho memory provider plugin (client, session, CLI)
- `docs/migration/openclaw.md` -- OpenClaw migration guide
- [Mintlify: How we built a virtual filesystem for our Assistant](https://www.mintlify.com/blog/how-we-built-a-virtual-filesystem-for-our-assistant) -- ChromaFs pattern: virtual filesystem over indexed data
- [arXiv 2601.11672: From Everything-is-a-File to Files-Are-All-You-Need](https://arxiv.org/abs/2601.11672) -- Unix philosophy applied to agentic AI design
- [sqlite-vec](https://github.com/asg017/sqlite-vec) -- vector search extension for SQLite
- [Honcho](https://github.com/plastic-labs/honcho) -- memory library with dialectical reasoning
- [OpenViking](https://github.com/volcengine/OpenViking) -- context database with tiered L0/L1/L2 and filesystem paradigm
- [mem0](https://github.com/mem0ai/mem0) -- memory layer with graph-based approach
