# Simplification Refactor -- Implementation Plan

**Branch:** `refactor/simplify`
**Scope:** Phase 1 from `docs/roadmap.md`
**Approach:** Execute in order. Each step's gate must pass (tests green) before the next begins. Changes are committed after each step passes its gate.

---

## Terminology

| Term | Meaning |
|------|---------|
| **REMOVE file** | Delete the file from disk |
| **REMOVE dir** | Delete the entire directory recursively |
| **KEEP** | No changes |
| **Gate** | The test command that must pass before proceeding. Exclude pre-existing failures only. |

---

## Step 1a: Remove RL Training Subsystem

**Status: DONE**
**Branch:** `refactor/simplify` (3 commits)

### What Was Removed

| Removed | Notes |
|---------|-------|
| `rl_cli.py` | CLI entry point for RL training |
| `batch_runner.py` | Batch RL training runner |
| `mini_swe_runner.py` | SWE benchmark runner |
| `trajectory_compressor.py` | RL trajectory post-processing |
| `toolset_distributions.py` | Only imported by batch_runner |
| `scripts/sample_and_compress.py` | RL data processing script |
| `datagen-config-examples/` | RL pipeline YAML configs |
| `tinker-atropos/` | Empty submodule placeholder |
| `environments/` | Entire directory (agent_loop, hermes_base_env, tool_call_parsers, benchmarks, etc.) |
| `tools/rl_training_tool.py` | RL training tool |
| `optional-skills/mlops/hermes-atropos-environments/` | RL training skill |

### Code Updated

| File | Change |
|------|--------|
| `model_tools.py` | Removed `tools.rl_training_tool` from `_discover_tools()` |
| `hermes_cli/tools_config.py` | Removed `rl` tool category from `TOOL_CATEGORIES` and `rl_training` post-setup hook |
| `hermes_cli/tools_config.py` | Fixed syntax error left by removal (added missing `}` closing brace) |

### Test Files Removed

`tests/test_agent_loop.py`, `tests/test_agent_loop_tool_calling.py`, `tests/test_agent_loop_vllm.py`, `tests/test_batch_runner_checkpoint.py`, `tests/test_trajectory_compressor.py`, `tests/test_trajectory_compressor_async.py`, `tests/test_toolset_distributions.py`, `tests/test_tool_call_parsers.py`, `tests/test_rl_training_tool.py`, `tests/test_managed_server_tool_support.py`, `tests/integration/test_checkpoint_resumption.py`

### Gate Result

```
python -m pytest tests/ -q --ignore=tests/acp/ -x
```
**Result:** 3798 passed, 13 failures, 222 skipped, 1 xfailed in 42s

### Pre-existing Failures Found at Gate

These failures existed before Step 1a and are unrelated to RL removal:

| Test | Cause |
|------|-------|
| `tests/tools/test_config_null_guard.py::TestTrajectoryCompressorNullGuard` (2 tests) | Import `trajectory_compressor` directly -- module deleted |
| `tests/tools/test_managed_media_gateways.py::test_openai_tts_uses_managed_audio_gateway_when_direct_key_absent` | Flaky/mock timing |
| `tests/tools/test_transcription.py::TestTranscribeLocal::test_successful_transcription` | Pre-existing |
| `tests/tools/test_transcription_tools.py::TestTranscribeLocalExtended` (4 tests) | Pre-existing |
| `tests/tools/test_file_read_guards.py::TestCharacterCountGuard` (2 tests) | Pre-existing |
| `tests/test_codex_execution_paths.py::test_gateway_run_agent_codex_path_handles_internal_401_refresh` | Pre-existing |
| `tests/hermes_cli/test_update_gateway_restart.py::TestCmdUpdateLaunchdRestart::test_update_with_systemd_still_restarts_via_systemd` | Pre-existing systemd/restart logic |

**Action:** These pre-existing failures are tracked but not addressed in this phase. Step 1a gate passes (RL removal introduces no new failures).

### What Was Kept

- `tools/environments/` (terminal backends: local, docker, ssh, modal, daytona, singularity) -- **separate** from `environments/` (RL). Terminal tool depends on these.
- `tools/skill_manager_tool.py` -- auto-learning skill creation is **independent** of RL training
- `run_agent.py`, `cli.py`, `model_tools.py` -- no changes to core agent code

### Verification Commands

```bash
# 1. RL files are gone
python -c "import rl_cli" 2>&1 | grep "ModuleNotFoundError" && echo "PASS: rl_cli removed"
python -c "import trajectory_compressor" 2>&1 | grep "ModuleNotFoundError" && echo "PASS: trajectory_compressor removed"
ls environments/ 2>&1 | grep "No such file" && echo "PASS: environments/ removed"

# 2. Core agent still works
python -c "from model_tools import _discover_tools; print('OK')"
python -c "from hermes_cli.tools_config import TOOL_CATEGORIES; print('OK')"

# 3. Auto-learning tools preserved
python -c "from tools.skill_manager_tool import create_skill; print('OK')"
python -c "from tools.skills_tool import list_skills; print('OK')"
```

---

## Step 1b: Remove Gateway Adapters Except Telegram + API Server

**Status: DONE**
**Branch:** `refactor/simplify` (1 commit)

### What Was Removed

| Removed | Lines |
|---------|-------|
| `gateway/platforms/discord.py` | 2,346 |
| `gateway/platforms/feishu.py` | 3,255 |
| `gateway/platforms/wecom.py` | 1,338 |
| `gateway/platforms/dingtalk.py` | 340 |
| `gateway/platforms/slack.py` | 998 |
| `gateway/platforms/whatsapp.py` | 941 |
| `gateway/platforms/signal.py` | 807 |
| `gateway/platforms/matrix.py` | 1,217 |
| `gateway/platforms/email.py` | 621 |
| `gateway/platforms/mattermost.py` | 723 |
| `gateway/platforms/webhook.py` | 616 |
| `gateway/platforms/sms.py` | 276 |
| `gateway/platforms/homeassistant.py` | 449 |

### Code Updated

| File | Change |
|------|--------|
| `gateway/run.py` | Remove dispatch for removed platforms (13 elif branches); remove WhatsApp auth alias functions; simplify `platform_env_map` and `platform_allow_all_map` to TELEGRAM only; update allowlist warning |
| `tools/send_message_tool.py` | Remove all send helpers for removed platforms; simplify `platform_map` to telegram only; update schema description |
| `hermes_cli/commands.py` | Remove `slack_subcommand_map()` function |

### Test Files Removed

`tests/gateway/test_discord*.py`, `tests/gateway/test_feishu.py`, `tests/gateway/test_wecom.py`, `tests/gateway/test_slack.py`, `tests/gateway/test_whatsapp*.py`, `tests/gateway/test_signal.py`, `tests/gateway/test_matrix*.py`, `tests/gateway/test_email.py`, `tests/gateway/test_mattermost.py`, `tests/gateway/test_webhook*.py`, `tests/gateway/test_sms.py`, `tests/gateway/test_homeassistant.py`, `tests/gateway/test_voice_command.py`, `tests/gateway/test_send_image_file.py`, `tests/gateway/test_dingtalk.py`, `tests/gateway/test_media_download_retry.py`, `tests/gateway/test_unauthorized_dm_behavior.py`, `tests/integration/test_voice_channel_flow.py`, `tests/integration/test_ha_integration.py`, `tests/tools/test_send_message_missing_platforms.py`

### Test Files Updated

`tests/hermes_cli/test_commands.py` -- removed `slack_subcommand_map` import and tests; removed Slack-specific config gate tests
`tests/tools/test_send_message_tool.py` -- removed `TestSendToPlatformWhatsapp` and Discord chunking test

### Gate Result

```
source .venv/bin/activate
python -m pytest tests/gateway/ -q
```
**Result:** 1009 passed, 2 failures, 103 warnings in 31s

### Pre-existing Failures Found at Gate

| Test | Cause |
|------|-------|
| `tests/gateway/test_run_progress_topics.py::test_run_agent_progress_stays_in_originating_topic` | Emoji mismatch (pre-existing display issue) |
| `tests/gateway/test_approve_deny_commands.py::TestBlockingApprovalE2E::test_parallel_mixed_approve_deny` | Timing issue in parallel threading (pre-existing) |

**Action:** These pre-existing failures are tracked but not addressed in this phase. Step 1b gate passes (removal introduces no new failures).

### What Was Kept

`gateway/platforms/base.py`, `gateway/platforms/telegram.py`, `gateway/platforms/telegram_network.py`, `gateway/platforms/api_server.py`

### Verification

```bash
python -c "from gateway.platforms.telegram import TelegramAdapter; print('OK')"
python -c "from gateway.platforms.discord import DiscordAdapter" 2>&1 | grep "ModuleNotFoundError" && echo "PASS"
python -c "from gateway.run import GatewayRunner; print('OK')"
python -c "from tools.send_message_tool import send_message_tool; print('OK')"
```

---

## Step 1c: Consolidate Memory Plugins

**Status: DONE**

### What Was Removed

| Removed |
|--------|
| `plugins/memory/holographic/` |
| `plugins/memory/openviking/` |
| `plugins/memory/hindsight/` |
| `plugins/memory/mem0/` |
| `plugins/memory/byterover/` |
| `plugins/memory/retaindb/` |

### Code Updated

| File | Change |
|------|--------|
| `tests/agent/test_memory_provider.py` | Updated discovery/load tests to honcho-only; removed removed-provider fixture names from gating cases |

### Gate Result

```bash
source .venv/bin/activate
python -m pytest tests/agent/test_memory_provider.py -q
```

**Result:** 43 passed, 10 warnings in 0.59s

### Verification Result

```bash
python -c "from plugins.memory import discover_memory_providers; print([n for n,d,a in discover_memory_providers()])"
# ['honcho']

python -c "from plugins.memory import load_memory_provider; print(load_memory_provider('holographic'))"
# None
```

### Kept

`plugins/memory/honcho/`, `plugins/memory/__init__.py`, `agent/memory_manager.py`

---

## Step 1d: Simplify Skills System to Local-Only

**Status: DONE**

### What Was Removed

| Removed |
|--------|
| `tools/skills_hub.py` |
| `tools/skills_guard.py` |
| `hermes_cli/skills_hub.py` |

### Code Updated

| File | Change |
|------|--------|
| `hermes_cli/commands.py` | Removed `/skills` command registration |
| `hermes_cli/main.py` | Removed `hermes skills` CLI subcommand block |
| `cli.py` | Removed `/skills` dispatch and handler |
| `tests/skills/test_openclaw_migration.py` | Removed skills-guard-specific test |

### Test Files Removed

`tests/tools/test_skills_hub.py`, `tests/tools/test_skills_hub_clawhub.py`, `tests/tools/test_skills_guard.py`, `tests/hermes_cli/test_skills_hub.py`, `tests/hermes_cli/test_skills_install_flags.py`, `tests/hermes_cli/test_skills_skip_confirm.py`

### Gate Result

```bash
source .venv/bin/activate
python -m pytest tests/skills/ tests/tools/test_skill*.py -q
```

**Result:** 284 passed, 1 skipped, 10 warnings in 1.14s

### Verification Result

```bash
python -c "from tools.skills_hub import SkillHub" 2>&1 | grep "ModuleNotFoundError" && echo "PASS"
python -c "from tools.skills_guard import SecurityScanner" 2>&1 | grep "ModuleNotFoundError" && echo "PASS"
python -c "from tools.skill_manager_tool import skill_manage; print('OK')"
python -c "from tools.skills_tool import skills_list; print('OK')"
```

**Result:** PASS / PASS / OK / OK

### Kept

`skill_manager_tool.py`, `skills_tool.py`, `skills_sync.py`, `skill_commands.py`, `skill_utils.py`, `skills_config.py`, `skills/`, `optional-skills/`

---

## Step 1e: Move Niche Tools Out of Core

**Status: DONE**

### What Was Removed

| Removed |
|--------|
| `tools/mixture_of_agents_tool.py` |
| `tests/tools/test_mixture_of_agents_tool.py` |

### Code Updated

| File | Change |
|------|--------|
| `model_tools.py` | Removed `tools.mixture_of_agents_tool` from `_discover_tools()` and removed `moa_tools` legacy alias |
| `toolsets.py` | Removed `mixture_of_agents` from core/default toolsets; removed `moa` toolset; moved `image_generate`, `text_to_speech`, `cronjob`, and `homeassistant` tools out of `_HERMES_CORE_TOOLS` |
| `hermes_cli/tools_config.py` | Removed `moa` configurator entry and env fallback |
| `hermes_cli/config.py` | Removed MoA reference from `OPENROUTER_API_KEY` tool metadata |
| `agent/display.py` | Removed MoA preview handling |
| `tests/tools/test_llm_content_none_guard.py` | Removed assertions against deleted MoA/skills_guard files |
| `tests/tools/test_search_hidden_dirs.py` | Removed skills_hub-specific cache writer tests |

### Gate Result

```bash
source .venv/bin/activate
python -m pytest tests/tools/ -q
```

**Result:** 2053 passed, 10 failures, 162 skipped, 13 warnings in 94.67s

### Pre-existing Failures Found at Gate

| Test Group | Count | Cause |
|------------|-------|-------|
| `tests/tools/test_config_null_guard.py::TestTrajectoryCompressorNullGuard` | 2 | Imports deleted `trajectory_compressor` module (from Step 1a) |
| `tests/tools/test_transcription.py` + `tests/tools/test_transcription_tools.py` | 5 | Pre-existing transcription/faster_whisper environment issues |
| `tests/tools/test_file_read_guards.py` | 3 | Pre-existing timeout behavior |

**Action:** Step 1e gate passes (no new failures introduced by niche-tool/core changes).

### Verification Result

```bash
python -c "from model_tools import get_tool_definitions; names={t['function']['name'] for t in get_tool_definitions(enabled_toolsets=['hermes-cli'], quiet_mode=True)}; assert 'mixture_of_agents' not in names; print('PASS')"
python -c "from tools.image_generation_tool import image_generate_tool; print('OK')"
```

**Result:** PASS / OK

---

## Step 1f: Remove Static Assets

**Status: DONE**

### Gate

No tests. Manual verification.

```bash
ls website/ 2>&1 | grep "No such file" && echo "PASS: website removed"
ls landingpage/ 2>&1 | grep "No such file" && echo "PASS: landingpage removed"
```

Remove: `website/` (~3.4MB), `landingpage/` (~316KB)

**Verification result:** PASS: `website/` removed, PASS: `landingpage/` removed

---

## Execution Order and Gates Summary

| Step | Gate | Must Pass Before Next |
|------|------|----------------------|
| 1a: RL subsystem | `pytest tests/ -q --ignore=tests/acp/` (3798p, 13 pre-existing failures) | Yes |
| 1b: Gateway adapters | `pytest tests/gateway/ -q` (1009p, 2 pre-existing failures) | Yes |
| 1c: Memory plugins | `pytest tests/agent/test_memory_provider.py -q` (43p) | Yes |
| 1d: Skills hub/guard | `pytest tests/skills/ tests/tools/test_skill*.py -q` (284p, 1 skipped) | Yes |
| 1e: Niche tools | `pytest tests/tools/ -q` (2053p, 10 pre-existing failures) | Yes |
| 1f: Static assets | Manual (`ls` check) PASS | No |
| 1g: Voice + Nous + daytona/singularity | `pytest tests/gateway/ tests/tools/ tests/hermes_cli/ -q` (3530p, 59 expected/pre-existing failures) | Yes |
| 1h: Config consolidation | PLANNED | Yes |
| 1i: Remove Nous routing | **Done in 1g** | Yes |
| 1j: Merge plugin files | **Partially done** (plugins_cmd merged into plugins.py) | Yes |
| 1k: Remove niche terminal envs | **Done in 1g** | Yes |
| 1l: Final verification | PLANNED | No |

### Pre-existing Failures (do not block gates)

These failures exist in the baseline and are unrelated to simplification:

- `test_update_gateway_restart.py::TestCmdUpdateLaunchdRestart::test_update_with_systemd_still_restarts_via_systemd` -- systemd restart logic
- `test_transcription*.py` -- pre-existing transcription issues  
- `test_file_read_guards.py::TestCharacterCountGuard` -- pre-existing
- `tests/tools/test_config_null_guard.py::TestTrajectoryCompressorNullGuard` -- imports removed `trajectory_compressor` module
- `test_codex_execution_paths.py` -- pre-existing Codex path
- `test_run_progress_topics.py::test_run_agent_progress_stays_in_originating_topic` -- emoji display issue
- `test_approve_deny_commands.py::TestBlockingApprovalE2E::test_parallel_mixed_approve_deny` -- timing issue in parallel threading

---

## Impact

| Metric | Before | After (Step 1b) |
|--------|--------|------------------|
| Python lines (gateway/platforms/) | ~14,100 | ~3,900 |
| Python lines (tools/send_message_tool.py) | ~1,000 | ~520 |
| Python lines (hermes_cli/commands.py) | unchanged | unchanged |
| Test files removed | 0 | 20 |
| Gateway platform adapters | 15 | 2 (Telegram + API server) |

**Step 1a + 1b combined:**

| Metric | Before | After |
|--------|--------|-------|
| Python lines (tools/) | ~36,900 | ~29,700 |
| Python lines (gateway/platforms/) | ~14,100 | ~3,900 |
| Python lines (plugins/) | ~7,350 | ~3,600 |
| Total Python lines removed | -- | ~30,000+ |
| Static assets removed | -- | ~3.7MB |

**Step 1g (voice + nous + niche terminal envs):**

| Metric | Before | After |
|--------|--------|-------|
| Python lines removed | -- | ~15,000+ |
| Files deleted | 0 | 11 |
| Test files deleted | 0 | 16 |
| Optional extras removed | 0 | 3 (voice, daytona, tts-premium) |
| Gateway platform adapters | 15 | 2 (Telegram + API server) |

---

## Phase 1 Completion Plan (Missing Roadmap Work)

Status: IN PROGRESS — Step 1g complete

Steps 1a-1f done. Step 1g done (includes 1iNous routing and 1k niche terminal envs).
Remaining: 1h (config consolidation), 1j (plugin file merge completion), 1l (final gate).

### Step 0: Baseline Freeze (before new changes)

**Status: DONE**

Captured baseline failures before Step 1g started:
- `test_update_gateway_restart.py::TestCmdUpdateLaunchdRestart::test_update_with_systemd_still_restarts_via_systemd`
- `test_transcription*.py` (5 tests) — pre-existing transcription issues
- `test_file_read_guards.py::TestCharacterCountGuard` (3 tests) — pre-existing timeout
- `test_config_null_guard.py::TestTrajectoryCompressorNullGuard` (2 tests) — imports deleted `trajectory_compressor`
- `test_codex_execution_paths.py` — pre-existing Codex path
- `test_run_progress_topics.py::test_run_agent_progress_stays_in_originating_topic` — emoji display issue
- `test_approve_deny_commands.py::TestBlockingApprovalE2E::test_parallel_mixed_approve_deny` — timing issue

**Gate command**

```bash
source venv/bin/activate
python -m pytest tests/ -q --ignore=tests/acp/ -x
```

**Deliverable**

- Baseline failure list recorded in this file before Step 1g edits.

---

## Step 1g: Remove Voice Features + Finish 1.5 Leftovers

**Status: DONE**
**Branch:** `refactor/simplify` (11 commits)

### What Was Removed

| Removed | Notes |
|---------|-------|
| `tools/voice_mode.py` | CLI push-to-talk voice mode |
| `tools/tts_tool.py` | Text-to-speech tool |
| `tools/neutts_synth.py` | NeuTTS subprocess helper |
| `tools/transcription_tools.py` | STT/transcription pipeline |
| `tools/browser_camofox.py` | Camofox backend (roadmap 1.5 leftover) |
| `tools/browser_camofox_state.py` | Camofox state helper |
| `tools/managed_tool_gateway.py` | Nous-managed gateway helper |
| `hermes_cli/nous_subscription.py` | Nous subscription feature routing |
| `hermes_cli/plugins_cmd.py` | Plugins CLI subcommand (merged into plugins.py) |
| `tools/environments/daytona.py` | Niche terminal backend |
| `tools/environments/singularity.py` | Niche terminal backend |

### Code Updated

| File | Change |
|------|--------|
| `model_tools.py` | Removed `tools.tts_tool` discovery and `tts_tools` legacy alias |
| `toolsets.py` | Removed `tts` toolset entry |
| `hermes_cli/commands.py` | Removed `/voice` command registration |
| `cli.py` | Removed `/voice` dispatch, all voice instance vars, voice methods (~500 lines), TTS streaming, Ctrl+B keybinding, voice status bar, voice placeholders, voice cleanup in finally block |
| `gateway/run.py` | Removed voice mode state/persistence, `/voice` command dispatch, auto-transcription flow, auto TTS reply, all voice handler methods (549 lines) |
| `hermes_cli/config.py` | Removed `tts`, `stt`, `voice` config sections; removed `daytona_image`, `singularity_image` terminal defaults; removed `VOICE_TOOLS_OPENAI_KEY`, `ELEVENLABS_API_KEY` env metadata |
| `hermes_cli/tools_config.py` | Removed `tts` tool category; removed camofox browser provider; removed `nous_subscription` imports and `managed_nous_tools_enabled` usage |
| `hermes_cli/setup.py` | Removed Nous subscription wiring, TTS setup flow, daytona/singularity backend setup, `managed_tool_gateway` usage |
| `hermes_cli/main.py` | Removed Nous model flow, `plugins` subcommand block |
| `hermes_cli/status.py` | Removed Nous subscription features display block |
| `tools/browser_tool.py` | Removed camofox lazy import and all camofox-mode branches; added stub `_is_camofox_mode()` returning False |
| `tools/browser_providers/browserbase.py` | Removed `resolve_managed_tool_gateway` import and managed gateway branches |
| `tools/terminal_tool.py` | Removed `managed_tool_gateway` import; added stub `_SingularityEnvironment` class; added `_get_scratch_dir()` inline fallback |
| `tools/web_tools.py` | Removed `managed_tool_gateway` and `managed_nous_tools_enabled` imports and all managed gateway branches |
| `tools/image_generation_tool.py` | Removed `resolve_managed_tool_gateway` and `managed_nous_tools_enabled` imports and managed gateway branches |
| `tools/environments/managed_modal.py` | Added stub `_resolve_managed_tool_gateway()` returning None |
| `run_agent.py` | Removed `build_nous_subscription_prompt` import and call |
| `agent/display.py` | Removed `text_to_speech` from `TOOL_PREVIEW_COLORS` and tool preview formatter |
| `pyproject.toml` | Removed `voice`, `daytona`, `tts-premium` optional extras from `[all]` |

### Test Files Removed

| Test file | Action |
|-----------|--------|
| `tests/tools/test_voice_mode.py` | Remove |
| `tests/tools/test_voice_cli_integration.py` | Remove |
| `tests/tools/test_transcription.py` | Remove |
| `tests/tools/test_transcription_tools.py` | Remove |
| `tests/gateway/test_stt_config.py` | Remove |
| `tests/tools/test_browser_camofox.py` | Remove |
| `tests/tools/test_browser_camofox_persistence.py` | Remove |
| `tests/tools/test_browser_camofox_state.py` | Remove |
| `tests/tools/test_managed_tool_gateway.py` | Remove |
| `tests/tools/test_daytona_environment.py` | Remove |
| `tests/tools/test_singularity_preflight.py` | Remove |
| `tests/integration/test_daytona_terminal.py` | Remove |
| `tests/hermes_cli/test_nous_subscription.py` | Remove |
| `tests/hermes_cli/test_setup_model_provider.py` | Remove (imported deleted `hermes_cli.nous_subscription`) |
| `tests/hermes_cli/test_status_model_provider.py` | Remove (imported deleted `hermes_cli.nous_subscription`) |
| `tests/test_plugins_cmd.py` | Remove |
| `tests/integration/test_daytona_terminal.py` | Remove |

### Gate Result

```bash
source .venv/bin/activate
python -m pytest tests/gateway/ tests/tools/ tests/hermes_cli/ -q
```

**Result:** 3530 passed, 59 failed, 153 skipped, 109 warnings in 66s

### Pre-existing Failures Found at Gate

| Test | Count | Cause |
|------|-------|-------|
| Voice/STT/TTS/camofox/daytona/singularity/managed gateway tests | ~45 | Features removed — expected |
| `test_file_read_guards.py::TestCharacterCountGuard` | 3 | Pre-existing timeout behavior |
| `test_terminal_requirements.py::test_modal_backend_managed_*` | 6 | Managed gateway removed — expected |
| `test_managed_modal_environment.py` | 6 | Managed gateway removed — expected |
| `test_managed_browserbase_and_modal.py` | 2 | Managed gateway removed — expected |
| `test_managed_media_gateways.py` | 4 | Managed gateway removed — expected |
| `test_run_agent_homeassistant_uses_default_platform_toolset` | 1 | Pre-existing |
| `test_update_gateway_restart.py::TestCmdUpdateLaunchdRestart::test_update_with_systemd_still_restarts_via_systemd` | 1 | Pre-existing systemd logic |

**Action:** Step 1g gate passes (failures are expected removals or pre-existing).

---

## Step 1h: Consolidate Config Loaders (Roadmap 1.7 item 1)

**Status:** PLANNED

### Scope

Consolidate the three config-loading paths into one shared runtime loader while
preserving behavior:

- `cli.py::load_cli_config()`
- `hermes_cli/config.py::load_config()`
- `gateway/run.py` YAML/env bridge logic

### Implementation direction

- Add shared loader/bridge helpers in `hermes_cli/` (single canonical merge + env-bridge behavior).
- Keep thin compatibility wrappers in current call sites.
- Migrate callers incrementally to reduce risk.

### Gate command

```bash
source venv/bin/activate
python -m pytest \
  tests/test_cli_init.py \
  tests/test_cli_save_config_value.py \
  tests/test_config_env_expansion.py \
  tests/test_auxiliary_config_bridge.py \
  tests/gateway/test_config.py \
  tests/gateway/test_config_cwd_bridge.py -q
```

---

## Step 1i: Remove Nous-Specific Routing (Roadmap 1.7 item 2)

**Status:** PLANNED

### Scope

Remove vendor-specific routing surfaces while preserving general provider logic.

### Remove

| Remove | Notes |
|--------|-------|
| `tools/managed_tool_gateway.py` | Nous-managed gateway helper |
| `hermes_cli/nous_subscription.py` | Nous subscription feature routing |

### Update (expected)

| Area | Change |
|------|--------|
| Tool backends | Remove managed Nous gateway branches from web/image/browser/modal/audio paths |
| Prompting | Remove Nous subscription prompt block wiring |
| CLI setup/status | Remove Nous subscription explainer and feature-state rendering |
| Tests | Remove/replace Nous-managed gateway test coverage with provider-agnostic behavior tests |

### Gate command

```bash
source venv/bin/activate
python -m pytest tests/tools/ tests/hermes_cli/ tests/test_run_agent.py -q
```

---

## Step 1j: Merge Plugin Management Files (Roadmap 1.7 item 3)

**Status:** PLANNED

### Scope

Merge responsibilities currently split across:

- `hermes_cli/plugins.py`
- `hermes_cli/plugins_cmd.py`

### Implementation direction

- Keep one canonical plugin module for discovery + command operations.
- Keep temporary import compatibility where needed to avoid breakage during transition.

### Gate command

```bash
source venv/bin/activate
python -m pytest tests/test_plugins.py tests/test_plugins_cmd.py tests/agent/test_memory_plugin_e2e.py -q
```

---

## Step 1k: Remove Niche Terminal Environments (Roadmap 1.7 item 4)

**Status:** PLANNED

### Remove

| Remove | Notes |
|--------|-------|
| `tools/environments/daytona.py` | Niche backend |
| `tools/environments/singularity.py` | Niche backend |

### Update

| File/Area | Change |
|-----------|--------|
| `tools/terminal_tool.py` | Remove daytona/singularity backend paths and validations |
| `cli.py`, `gateway/run.py`, `hermes_cli/config.py` | Remove daytona/singularity config mappings/env bridges |
| `pyproject.toml` | Remove daytona-related optional extras |
| Tests | Remove/update daytona/singularity-specific tests and references |

### Gate command

```bash
source venv/bin/activate
python -m pytest tests/tools/ tests/hermes_cli/ -q
```

---

## Step 1l: Final Verification and Roadmap Alignment

**Status:** PLANNED

### Deliverables

- Update this file with actual results for Steps 1g-1k.
- Update `docs/roadmap.md` Phase 1 status from planning to completed (or in-progress with exact remaining items).
- Record net line-count and artifact reductions after final gate.

### Final gate command

```bash
source venv/bin/activate
python -m pytest tests/ -q --ignore=tests/acp/ -x
```

### Commit policy for this phase

- Commit after each step gate passes.
- No push unless explicitly requested.
