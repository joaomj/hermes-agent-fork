# Hermes Agent — Technical Context

> **What is this document?** Single-File Memory Bank consolidating the project's architecture, design decisions, data flow, and key implementation details. Intended for AI assistants and developers working on the codebase.

**Last updated:** 2026-04-12
**Lines of code (approximate):** ~22,000 Python (root modules) + ~28,000 in packages = ~50,000 total

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Project Structure](#2-project-structure)
3. [Entry Points](#3-entry-points)
4. [Core Classes and Responsibilities](#4-core-classes-and-responsibilities)
5. [Tool System](#5-tool-system)
6. [Message Flow & Data Flow](#6-message-flow--data-flow)
7. [Gateway System](#7-gateway-system)
8. [ACP Adapter](#8-acp-adapter)
9. [Session & State Management](#9-session--state-management)
10. [Skill System](#10-skill-system)
11. [Configuration & Profiles](#11-configuration--profiles)
12. [Build & Packaging](#12-build--packaging)
13. [Key Architectural Decisions](#13-key-architectural-decisions)
14. [Testing](#14-testing)

---

## 1. System Overview

Hermes Agent is a **self-improving AI agent** that:

- Engages in multi-turn conversations with tool-calling capabilities
- Runs in multiple contexts: interactive CLI, messaging platforms (Telegram, etc.), ACP editor integrations (VS Code, Zed, JetBrains), and API server
- Persists conversation history across sessions
- Supports skill creation and improvement from experience
- Provides a modular tool system extensible via plugins and MCP servers

The system is primarily **synchronous** in its core loop (uses threading/futures for I/O parallelism) with an **asyncio bridge** for async tool handlers and the gateway's async platform adapters.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / Platform                               │
│   (CLI terminal, Telegram, VS Code, API call, etc.)        │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │                                  │
               │  hermes (CLI)                    │  hermes-agent (direct)
               │  hermes gateway (messaging)      │  hermes-acp (editor)
               │  hermes acp                     │
               └──────────┬──────────────────────┘
                          │
               ┌──────────▼──────────────────────────────────┐
               │              AIAgent (run_agent.py)          │
               │   Core synchronous conversation loop        │
               │   - Tool orchestration                       │
               │   - Context compression                     │
               │   - Interrupt propagation                    │
               │   - Memory management                        │
               │   - Session persistence                      │
               └──────────┬──────────────────────────────────┘
                          │
               ┌──────────▼──────────────────────────────────┐
               │           model_tools.py                     │
               │   - Tool discovery (imports all tools/)      │
               │   - Toolset filtering                        │
               │   - Schema generation                        │
               │   - Dispatch to registry                     │
               └──────────┬──────────────────────────────────┘
                          │
               ┌──────────▼──────────────────────────────────┐
               │           tools/registry.py                  │
               │   Central tool registry (singleton)          │
               │   Each tool/ registers itself at import time │
               └──────────┬──────────────────────────────────┘
                          │
          ┌───────────────┼───────────────────────────────────┐
          │               │                                   │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌─────────▼────────┐  ┌─▼────────┐
   │ tools/web_  │  │ tools/     │  │ tools/browser_   │  │ tools/   │
   │ tools.py    │  │ terminal_  │  │ tool.py          │  │ file_    │
   │             │  │ tool.py    │  │                  │  │ tools.py │
   └─────────────┘  └────────────┘  └──────────────────┘  └──────────┘
```

---

## 2. Project Structure

### Directory Map

| Directory | Purpose |
|-----------|---------|
| `agent/` | Internal agent components: prompt building, context compression, model metadata, ACP client, skill commands, trajectory saving |
| `tools/` | All tool implementations (~42 files). Each tool file self-registers via `tools.registry.register()` at import time |
| `hermes_cli/` | CLI application: orchestrator, config, auth, commands, skins, setup wizard, plugins, profiles, model switching |
| `gateway/` | Messaging platform gateway: core runner, session store, delivery router, platform adapters (Telegram, API server, etc.) |
| `cron/` | Background scheduler: job definitions, cron expression parsing |
| `acp_adapter/` | ACP (Agent Client Protocol) editor integration server |
| `plugins/` | Plugin system (including memory providers) |
| `tests/` | ~3,000 test functions |
| `docs/` | Design docs, roadmap, skin examples |
| `_skills-available/` | 27 bundled skills shipped with the agent |
| `_optional-skills-available/` | 16 optional/additional skills |
| `acp_registry/` | ACP protocol metadata |
| `docker/` | Docker build assets |
| `nix/` | Nix flake packages and modules |
| `packaging/` | Homebrew packaging |
| `scripts/` | Developer and installation scripts |
| `assets/` | Static assets (banner images, icons) |

### Root Python Modules (the "loose files" problem)

| File | Lines | Role |
|------|-------|------|
| `run_agent.py` | 10,444 | `AIAgent` class — core conversation loop |
| `cli.py` | 8,204 | `HermesCLI` class — interactive terminal UX |
| `hermes_state.py` | 1,270 | `SessionDB` — SQLite session store with FTS5 |
| `mcp_serve.py` | 868 | MCP server implementation |
| `toolsets.py` | 560 | Toolset definitions and resolution |
| `model_tools.py` | 502 | Tool discovery and dispatch |
| `hermes_time.py` | 120 | Time utilities |
| `utils.py` | 126 | Atomic file writes, env helpers |
| `hermes_constants.py` | 105 | `get_hermes_home()`, path utilities |

### Import Dependency Chain

```
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, gateway/run.py
```

This is the **only** guaranteed import order in the system. All other imports are ad-hoc.

---

## 3. Entry Points

### User-Facing Commands

| Command | Entry Point | Purpose |
|---------|-------------|---------|
| `hermes` | `hermes_cli.main:main` | CLI orchestrator (interactive chat, subcommands) |
| `hermes-agent` | `run_agent:main` | Standalone agent runner (direct CLI usage) |
| `hermes-acp` | `acp_adapter.entry:main` | ACP editor integration server |
| `hermes gateway` | `gateway.run:start_gateway` | Messaging platform gateway |

### Direct Python Execution

| Command | What it does |
|---------|--------------|
| `python cli.py` | Interactive CLI mode |
| `python cli.py -q "query"` | Single query, then exit |
| `python cli.py --list-tools` | Print available tools and exit |
| `python run_agent.py -q "query"` | Direct agent query |
| `python -m gateway.run` | Start messaging gateway |
| `python -m acp_adapter.entry` | Start ACP server |

### hermes_cli Subcommands

```
hermes                    # Interactive chat
hermes gateway            # Start messaging gateway
hermes setup              # Interactive setup wizard
hermes doctor             # Health checks
hermes status             # Runtime status
hermes profile            # Profile management
hermes skills             # Skill configuration
hermes tools              # Tool configuration
hermes acp                # ACP server
hermes model              # Model catalog and switching
```

---

## 4. Core Classes and Responsibilities

### AIAgent (`run_agent.py`)

The central orchestrator. All conversation flows through this class.

**Key attributes:**
- `model` — model name in `provider/model` format (e.g., `anthropic/claude-opus-4.6`)
- `client` — OpenAI-compatible API client
- `valid_tool_names` — tools enabled for this session
- `session_db` — optional `SessionDB` for persistence
- `context_compressor` — manages context truncation
- `memory_provider` — optional persistent memory plugin
- `todo_store` — in-memory todo state

**Key methods:**

| Method | Line | Purpose |
|--------|-------|---------|
| `chat(message)` | 7300 | Simple interface — returns final response string |
| `run_conversation()` | 7249+ | Full conversation loop — returns `dict` with response + messages |
| `_run_single_turn()` | ~6100 | Execute one LLM call + tool execution cycle |
| `_execute_tool_call()` | ~4900 | Dispatch a single tool call via `model_tools.handle_function_call()` |
| `_handle_interrupt()` | ~2512 | Propagate interrupts to running tools and subagents |
| `_compress_context()` | 6035 | Trigger context compression, creating a new session lineage |
| `_persist_session()` | 10153 | Save session after each turn |

**Conversation loop pseudocode:**

```python
while api_call_count < max_iterations and iteration_budget.remaining > 0:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

### HermesCLI (`cli.py`)

The interactive terminal application. Built on `prompt_toolkit` for input with autocomplete and `rich` for formatting.

**Key responsibilities:**
- Terminal UI: banner, spinner, tool output formatting
- Slash command registry and dispatch
- Session creation and resume
- `AIAgent` instantiation and reuse
- `SessionDB` early initialization
- Skin/theme loading

**Command dispatch** uses `resolve_command()` from `hermes_cli/commands.py` — the single source of truth for all slash commands across CLI, gateway, Telegram menu, and Slack.

### SessionDB (`hermes_state.py`)

SQLite-backed persistent session storage.

**Schema:**
- `sessions` table: session metadata, model config, parent session chain, token counts, cost tracking
- `messages` table: full message history with role, content, tool calls, token counts, reasoning
- `messages_fts` FTS5 virtual table for full-text search

**Design decisions:**
- **WAL mode** for concurrent readers + single writer across multiple gateway platforms
- **Application-level retry with jitter** instead of SQLite's deterministic busy handler (avoids lock convoy under high concurrency)
- **Parent session chain** (`parent_session_id`) — context compression creates a new session that chains to its parent, preserving lineage

---

## 5. Tool System

### Architecture

```
Tool file (e.g., tools/web_tools.py)
       │
       │  at module import time, calls:
       ▼
registry.register(
    name="web_search",
    toolset="web",
    schema={...},           # OpenAI function-calling format
    handler=lambda args, **kw: web_search_impl(...),
    check_fn=check_requirements,  # returns bool — is this tool available?
    requires_env=[...],
    is_async=False,
)
       │
       ▼
tools/registry.py  (ToolRegistry singleton)
       │
       │  queried by model_tools.py after all imports complete
       ▼
model_tools.py:
  - _discover_tools()  imports all tool modules
  - get_tool_definitions()  filters by toolset, runs check_fn, returns schemas
  - handle_function_call()  dispatches to registry.dispatch()
```

### Tool Registry (`tools/registry.py`)

**`ToolEntry`** stores: name, toolset, schema, handler, check_fn, requires_env, is_async, description, emoji

**`ToolRegistry`** methods:

| Method | Purpose |
|--------|---------|
| `register()` | Add a tool at import time |
| `deregister()` | Remove a tool (used by MCP dynamic discovery) |
| `dispatch()` | Execute a tool handler sync or async |
| `get_definitions()` | Return filtered tool schemas for LLM |
| `get_tool_to_toolset_map()` | Build reverse index |
| `check_toolset_requirements()` | Run all check_fn for a toolset |

### Tool Discovery (`model_tools.py:_discover_tools()`)

Explicit import list of 18 tool modules. Optional tools (fal_client for image generation, etc.) are wrapped in try/except so import failures are non-fatal.

After built-in tools:
1. **MCP discovery** — `tools.mcp_tool.discover_mcp_tools()` loads external MCP servers from config
2. **Plugin discovery** — `hermes_cli.plugins.discover_plugins()` finds tools from user/project/pip plugins

### Toolset System (`toolsets.py`)

Tools are grouped into **toolsets** for enable/disable filtering. Static toolsets are defined in the `TOOLSETS` dict. Plugin toolsets are discovered at runtime from the registry.

**Core toolsets:**

| Toolset | Tools | Purpose |
|---------|-------|---------|
| `web` | web_search, web_extract | Web research |
| `terminal` | terminal, process | Shell access |
| `file` | read_file, write_file, patch, search_files | File operations |
| `browser` | browser_navigate + 10 others, web_search | Browser automation |
| `skills` | skills_list, skill_view, skill_manage | Skill management |
| `todo` | todo | Task tracking |
| `memory` | memory | Persistent memory |
| `session_search` | session_search | Past conversation search |
| `clarify` | clarify | User clarifying questions |
| `code_execution` | execute_code | Sandboxed Python |
| `delegation` | delegate_task | Subagent spawning |
| `vision` | vision_analyze | Image analysis |
| `image_gen` | image_generate | Image generation |
| `messaging` | send_message | Cross-platform messaging |
| `safe` | web + vision + image_gen (no terminal) | Restricted tools |

**Platform-specific toolsets:** `hermes-cli` (full), `hermes-telegram`, `hermes-acp` (no messaging/clarify), `hermes-api-server` (no interactive UI tools)

**Toolset resolution** is recursive with cycle detection. `resolve_toolset("debugging")` returns `terminal + process + web + file` (resolves includes).

### Schema Dynamic Rewriting

Two cases where schemas are rewritten at runtime:

1. **`execute_code` sandbox tools** — the `SANDBOX_ALLOWED_TOOLS` list embedded in the schema is intersected with `available_tool_names` so the model doesn't hallucinate calls to unavailable tools
2. **`browser_navigate` cross-references** — the "prefer web_search or web_extract" sentence is stripped from the description when those tools aren't available

### Agent-Intercepted Tools

Some tools are handled directly by `AIAgent` rather than dispatched through `handle_function_call()`:

```python
_AGENT_LOOP_TOOLS = {"todo", "memory", "session_search", "delegate_task"}
```

This is because they need access to agent-level state (`TodoStore`, `MemoryStore`, etc.). If they slip through to the registry anyway, they return a stub error.

---

## 6. Message Flow & Data Flow

### CLI Message Flow

```
User types message
       │
       ▼
HermesCLI._read_line()  [prompt_toolkit input]
       │
       ▼
HermesCLI._process_message() / process_command()
       │  (slash command detected?)
       ├─ Yes → resolve_command() → CommandDef handler
       │
       │  No → run_conversation()
       ▼
AIAgent.run_conversation()
       │
       ├─ Load/restore system prompt (cached per session)
       │
       ├─ Preflight context compression check
       │
       ├─ pre_llm_call plugin hook
       │
       ├─ LLM API call (OpenAI-compatible)
       │       │
       │       ├─ No tool_calls → return text response
       │       │
       │       └─ Tool calls → for each:
       │               handle_function_call()
       │                   ├─ Agent-loop tool → AIAgent handles directly
       │                   ├─ pre_tool_call hook
       │                   ├─ registry.dispatch()
       │                   ├─ post_tool_call hook
       │                   └─ return JSON result
       │
       ├─ Context compression check
       │       (if history exceeds threshold, compress and create new session lineage)
       │
       ├─ Persist session to SQLite
       │
       └─ post_llm_call plugin hook
```

### Gateway Message Flow

```
Platform webhook / polling loop
       │
       ▼
PlatformAdapter.receive_message()  (normalizes to MessageEvent)
       │
       ▼
GatewayRunner._handle_message()
       ├─ Authorization check
       ├─ Command interception (/stop, /new, /queue)
       ├─ Interrupt/hard-stop handling
       ├─ Session lookup/creation
       └─ agent_execute() → AIAgent.run_conversation()
               │
               └─ DeliveryRouter.send() → platform-specific send method
```

### OpenAI API-Compatible Format

All LLM calls use the OpenAI API format (Chat Completions):

```python
client.chat.completions.create(
    model=model,           # "provider/model-name" (e.g., "anthropic/claude-opus-4.6")
    messages=[...],        # [{"role": "system"/"user"/"assistant"/"tool", ...}]
    tools=[...],           # OpenAI function-calling tool definitions
    tool_choice="auto",
    max_tokens=...,
    extra_headers={"HTTP-Referer": "...", "X-Title": "..."}  # for OpenRouter
)
```

The `model` field encodes both provider and model. The `model_metadata.py` module provides context lengths and token estimation per model.

---

## 7. Gateway System

### GatewayRunner (`gateway/run.py`)

Manages the lifecycle of all platform adapters and routes incoming messages to the agent.

**Responsibilities:**
- Start/connect all configured platform adapters in parallel
- Maintain a map of active `AIAgent` instances per session
- Background tasks: session expiry watcher, platform reconnect watcher
- Failure recovery: queue and retry failed platform connections
- Shutdown: clean up agents, adapters, background tasks

**Adapter lifecycle:**
```python
# For each enabled platform:
adapter = create_adapter(platform_config)
adapter.on_message(handle_message_fn)
adapter.on_fatal_error(fatal_error_fn)
await adapter.connect()
# Failed adapters are queued for retry with backoff
```

### SessionStore (`gateway/session.py`)

Maps `(source, chat_id, thread_id, user_id)` tuples to session IDs. Persists to `sessions.json` (simple) or SQLite (if `SessionDB` is available).

Key methods:
- `build_session_key()` — deterministic key from platform identifiers
- `get_or_create_session()` — enforces reset policy, can seed DM threads from parent transcripts
- `load_transcript()` — prefers whichever history source (SQLite or JSONL) is longer

### DeliveryRouter (`gateway/delivery.py`)

Routes outbound messages to the correct destination:

| Target | Delivery method |
|--------|----------------|
| `origin` | Reply in the same platform/chat |
| `local` | Write markdown file to `~/.hermes/delivery/` |
| `telegram:123` | Send to specific Telegram chat ID |
| `telegram` | Default Telegram bot chat |

### Platform Adapters

Base interface in `gateway/platforms/base.py`:
- `MessageEvent` normalizes incoming messages (handles Telegram updates, Discord messages, Slack events, etc.)
- `BasePlatformAdapter` handles connection state, send methods, fatal errors

Concrete adapters:
- **Telegram** (`telegram.py`) — polling or webhook, Bot Command menu, token-scoped locks
- **API Server** (`api_server.py`) — OpenAI-compatible HTTP endpoints for external clients

---

## 8. ACP Adapter

### What is ACP?

ACP (Agent Client Protocol) is a stdio-based protocol for editor integrations. Hermes exposes itself as an ACP agent that editors (VS Code, Zed, JetBrains) can communicate with over stdin/stdout.

### Architecture

```
Editor (VS Code / Zed / JetBrains)
       │
       │  ACP protocol over stdio
       ▼
acp_adapter/entry.py  — entry point, env loading, logging
       │
       ▼
acp_adapter/server.py  — HermesACPAgent
       │
       ├─ initialize()  — advertise capabilities, auth methods
       │
       ├─ Session primitives:
       │   new_session, load_session, resume_session, fork_session, list_sessions
       │
       ├─ prompt()  — run AIAgent.run_conversation() in threadpool, stream events
       │
       └─ Slash commands (/model, /tools, /reset, /compact) — handled locally in headless mode
       
acp_adapter/session.py  — session manager (in-memory + SessionDB persistence)
acp_adapter/tools.py  — maps Hermes tool names → ACP ToolKind, builds tool events
```

### ACP Events

The adapter streams events back to the editor:
- `agent_start` / `agent_end`
- `tool_call_start` / `tool_call_end` / `tool_call_error`
- `text_delta` / `error`
- `title_artifact` (session title)
- `needs_input` (clarify tool triggers editor input prompt)

---

## 9. Session & State Management

### SessionDB Schema

```sql
sessions (
    id TEXT PRIMARY KEY,
    source TEXT,          -- 'cli', 'telegram', 'api_server', etc.
    user_id TEXT,
    model TEXT,
    model_config TEXT,    -- JSON blob
    system_prompt TEXT,
    parent_session_id TEXT,  -- chain for compression lineage
    started_at REAL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER,
    tool_call_count INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_write_tokens INTEGER,
    reasoning_tokens INTEGER,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    title TEXT
)

messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    role TEXT,           -- 'system', 'user', 'assistant', 'tool'
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,    -- JSON array
    tool_name TEXT,
    timestamp REAL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,      -- Anthropic extended thinking
    reasoning_details TEXT,
    codex_reasoning_items TEXT
)

messages_fts (FTS5) -- full-text search over message content
```

### Context Compression

When accumulated context exceeds the compression threshold (50% of model context limit by default):

1. `AIAgent._compress_context()` builds a summary prompt
2. A new session is created with `parent_session_id = current_session.id`
3. The summary + recent messages become the new context
4. The old session is ended with `end_reason = "compressed"`

This creates a **session lineage chain** — any session can be traced back through its ancestors.

### Token Counting

Token counts are tracked per message using `agent/model_metadata.py` approximations. Costs are estimated using provider pricing data and stored in the session record.

---

## 10. Skill System

### What is a Skill?

A skill is a **self-contained document** in `~/.hermes/skills/<skill-name>/` containing:
- `skill.md` — main instructions and knowledge
- `references/` — additional reference docs
- `templates/` — reusable template files
- `scripts/` — executable scripts
- `assets/` — static assets
- `manifest.json` — metadata (name, description, version, platform compatibility)

### Skill Slash Commands

When a user types `/skill-name`, `agent/skill_commands.py`:
1. Loads the skill from `~/.hermes/skills/<skill-name>/skill.md`
2. Injects it as a **user message** (not system prompt — preserves prompt caching)
3. The LLM sees the skill instructions in context without rebuilding the system prompt

Skills are also preloaded at CLI startup via `build_preloaded_skills_prompt()` — their content is summarized and injected as prompt text to give the agent awareness of available skills without a per-turn file read.

### Skill Sync

`tools/skills_sync.py` seeds skills from `_skills-available/` (bundled) into `~/.hermes/skills/` using a manifest that tracks user edits. User modifications are preserved across syncs.

### Skill Configuration

`hermes_cli/skills_config.py` lets users enable/disable skills globally or per platform (`cli`, `telegram`, etc.).

---

## 11. Configuration & Profiles

### Profile System

Hermes supports **profiles** — isolated instances each with its own `HERMES_HOME` directory.

```bash
hermes -p coder      # Uses ~/.hermes/profiles/coder/
hermes -p research   # Uses ~/.hermes/profiles/research/
```

`_apply_profile_override()` in `hermes_cli/main.py` sets `HERMES_HOME` **before any module imports**. All 119+ references to `get_hermes_home()` automatically scope to the active profile.

**Rules for profile-safe code:**
- Use `get_hermes_home()` from `hermes_constants` for all file paths
- Use `display_hermes_home()` for user-facing messages
- Never hardcode `~/.hermes` or `Path.home() / ".hermes"`

### Config Loading

| Loader | File | Used By |
|--------|------|---------|
| `load_cli_config()` | `cli.py` | CLI mode |
| `load_config()` | `hermes_cli/config.py` | `hermes tools`, `hermes setup` |
| Direct YAML load | `gateway/run.py` | Gateway |

`DEFAULT_CONFIG` in `hermes_cli/config.py` provides all defaults. Environment variables in `~/.hermes/.env` take precedence over config file values.

### Auth / Provider Resolution

`hermes_cli/auth.py` resolves API credentials from:
1. Environment variables (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.)
2. `~/.hermes/.env`
3. Provider OAuth flows (`hermes login`)

Supported providers: OpenAI, Anthropic, OpenRouter, Nous Portal, OpenAI Codex, GitHub Copilot.

---

## 12. Build & Packaging

### Dependencies

Managed via `pyproject.toml`. `uv.lock` is the lockfile (hash-pinned, committed).

Key dependencies:
- `openai` (OpenAI-compatible API client)
- `anthropic` (Anthropic API client)
- `httpx` (async HTTP)
- `rich` (terminal formatting)
- `prompt_toolkit` (interactive input)
- `pydantic` (data validation)
- `pyyaml` (config)
- `fire` (CLI argument parsing)
- `tenacity` (retry logic)

### Optional Dependency Groups

```toml
[project.optional-dependencies]
modal = ["modal>=1.0.0,<2"]
messaging = ["python-telegram-bot>=22.6,<23", "aiohttp>=3.13.3,<4"]
cron = ["croniter>=6.0.0,<7"]
cli = ["simple-term-menu>=1.0,<2"]
honcho = ["honcho-ai>=2.0.1,<3"]
mcp = ["mcp>=1.2.0,<2"]
homeassistant = ["aiohttp>=3.9.0,<4"]
acp = ["agent-client-protocol>=0.8.1,<0.9"]
dev = ["debugpy>=1.8.0,<2", "pytest>=9.0.2,<10", "pytest-asyncio>=1.3.0,<2"]
all = [all of the above]
```

### Entry Points

```toml
[project.scripts]
hermes = "hermes_cli.main:main"
hermes-agent = "run_agent:main"
hermes-acp = "acp_adapter.entry:main"
```

### Docker

`Dockerfile` installs the package in a Debian-based image. `docker/` contains the entrypoint script.

### Nix

`flake.nix` with `pyproject-nix` integration for NixOS/Nix-based systems.

---

## 13. Key Architectural Decisions

### 1. Synchronous Core Loop

The `AIAgent` conversation loop is entirely **synchronous**. Async is only used for:
- Async tool handlers (via `_run_async` bridge)
- Gateway platform adapters (async receive/send)
- MCP server stdio communication

**Why:** Simpler mental model, easier debugging, avoids async context leaks in tool handlers. Thread-based parallelism handles I/O-bound tool execution.

### 2. Prompt Caching as First-Class Constraint

The system prompt is cached per session and only rebuilt when context compression occurs. Skills are injected as **user messages** (not system prompt) to avoid cache invalidation.

**Why:** Cache hits dramatically reduce token costs. The model metadata system tracks context lengths to enable accurate compression triggers.

### 3. Tool Schema Dynamic Rewriting

Tool schemas are rewritten at `get_tool_definitions()` call time to remove references to unavailable tools.

**Why:** Prevents the model from hallucinating calls to tools that aren't configured. The `execute_code` sandbox tool list and `browser_navigate` cross-references are dynamically narrowed based on what's actually available.

### 4. Application-Level SQLite Retry with Jitter

`SessionDB` uses a short SQLite timeout (1s) with application-level retries with random jitter instead of SQLite's built-in busy handler.

**Why:** Under high concurrency (gateway + CLI + worktree agents all sharing one `state.db`), SQLite's deterministic sleep schedule causes lock convoy effects. Jitter naturally staggers competing writers.

### 5. Profile-Safe Home Directory

`HERMES_HOME` environment variable is set before any module imports. All path operations use `get_hermes_home()`.

**Why:** Enables fully isolated multi-profile installations without code changes. Previously hardcoded `~/.hermes` paths caused 5+ profile-related bugs.

### 6. Token Lock for Platform Credentials

Platform adapters (Telegram, etc.) call `acquire_scoped_lock()` with their bot token as the lock key, and `release_scoped_lock()` on disconnect.

**Why:** Prevents two profiles from using the same bot token simultaneously (which would cause message routing conflicts).

### 7. Skills Injected as User Messages

Skill content is loaded and injected as a user message when a slash command is invoked, not added to the system prompt.

**Why:** Preserves prompt caching. The system prompt cache key is stable per session; adding skill content to the system prompt would invalidate it.

### 8. Self-Registering Tools

Each tool file calls `registry.register()` at module level (import time). No central list of tools exists in `model_tools.py` beyond the import trigger list.

**Why:** Adding a new tool only requires creating the file and adding one import line to `_discover_tools()`. The registry is the single source of truth for tool metadata.

---

## 14. Testing

### Test Suite

```
tests/
├── agent/           # Agent internals tests
├── tools/           # Tool-level tests
├── hermes_cli/      # CLI tests
├── gateway/         # Gateway tests
├── acp/             # ACP adapter tests
├── cron/            # Scheduler tests
├── integration/     # Integration tests (require API keys)
├── e2e/             # End-to-end tests
├── skills/          # Skill system tests
└── fakes/           # Test doubles (fake browser, fake MCP server)
```

Run with: `python -m pytest tests/ -q`

### Key Test Patterns

**Profile isolation fixture** (`tests/conftest.py`):
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

**Isolation fixture** redirects `HERMES_HOME` to a temp directory so tests don't write to `~/.hermes`.

### Coverage

~3,000 tests. Full suite runs in ~3 minutes.

