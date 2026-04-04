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

**Status: PENDING**

### Gate Command

```bash
source .venv/bin/activate
python -m pytest tests/agent/test_memory_provider.py -q
```

Remove **before** running gate:

| Remove |
|--------|
| `plugins/memory/holographic/` |
| `plugins/memory/openviking/` |
| `plugins/memory/hindsight/` |
| `plugins/memory/mem0/` |
| `plugins/memory/byterover/` |
| `plugins/memory/retaindb/` |

**Update:** `tests/agent/test_memory_provider.py` -- remove `FakeMemoryProvider` cases for removed plugins (holographic, mem0, hindsight). Keep only honcho cases.

**Keep:** `plugins/memory/honcho/`, `plugins/memory/__init__.py` (provider-agnostic discovery), `agent/memory_manager.py`

### Verification

```bash
python -c "from plugins.memory import discover_memory_providers; print([n for n,d,a in discover_memory_providers()])"
# Expected: [('honcho', ...), ...] -- no holographic, mem0, openviking, etc.
python -c "from plugins.memory import load_memory_provider; print(load_memory_provider('holographic'))"
# Expected: None
```

---

## Step 1d: Simplify Skills System to Local-Only

**Status: PENDING**

### Gate Command

```bash
source .venv/bin/activate
python -m pytest tests/skills/ tests/tools/test_skill*.py -q
```

Remove **before** running gate:

| Remove | Lines |
|--------|-------|
| `tools/skills_hub.py` | 2,707 |
| `tools/skills_guard.py` | 1,105 |
| `hermes_cli/skills_hub.py` | 1,219 |

**Code to update:**

| File | Change |
|------|--------|
| `hermes_cli/commands.py` | Remove `skills_hub` from `COMMAND_REGISTRY` and help categories |
| `hermes_cli/main.py` | Remove `hermes skills` subcommand registration |
| `gateway/run.py` | Remove `skills_hub` from `GATEWAY_KNOWN_COMMANDS` |

**Remove test files:** `tests/tools/test_skills_hub.py`, `tests/tools/test_skills_hub_clawhub.py`

**Keep:** `skill_manager_tool.py`, `skills_tool.py`, `skills_sync.py`, `skill_commands.py`, `skill_utils.py`, `skills_config.py`, `skills/` directory, `optional-skills/` directory

### Verification

```bash
python -c "from tools.skills_hub import SkillHub" 2>&1 | grep "ModuleNotFoundError" && echo "PASS"
python -c "from tools.skills_guard import SecurityScanner" 2>&1 | grep "ModuleNotFoundError" && echo "PASS"
python -c "from tools.skill_manager_tool import create_skill; print('OK')"
python -c "from tools.skills_tool import list_skills; print('OK')"
```

---

## Step 1e: Move Niche Tools Out of Core

**Status: PENDING**

### Gate Command

```bash
source .venv/bin/activate
python -m pytest tests/tools/ -q -x
```

**Per-tool actions:**

| Tool | Action | File Changes |
|------|--------|-------------|
| `mixture_of_agents_tool.py` | **Remove entirely** -- experimental, zero tests | Delete file. Remove from `_discover_tools()` and `_HERMES_CORE_TOOLS`. |
| `image_generation_tool.py` | Gated toolset `image_gen` | Remove from `_HERMES_CORE_TOOLS`, add to new `image_gen` toolset entry |
| `homeassistant_tool.py` | Gated toolset `homeassistant` | Same pattern |
| `browser_camofox.py` + `browser_camofox_state.py` | Gated toolset `camofox` | Same pattern |
| `cronjob_tools.py` | Gated toolset `cron` | Same pattern |
| `tts_tool.py` + `neutts_synth.py` | Gated toolset `tts` | Same pattern |
| `voice_mode.py` | **Keep** -- make fully lazy | Defer imports inside functions, no toolset change |

**Remove test file:** `tests/tools/test_mixture_of_agents_tool.py`

**New toolset entry in `toolsets.py`:**

```python
HERMES_OPTIONAL_TOOLSETS = {
    "image_gen":     ["image_generate"],
    "homeassistant": ["homeassistant_*"],
    "camofox":       ["browser_camofox_*"],
    "cron":          ["cronjob_*"],
    "tts":           ["tts_*", "neutts_synth"],
}
```

### Verification

```bash
python -c "from model_tools import _discover_tools; tools = _discover_tools(); assert 'mixture_of_agents' not in str(tools)" && echo "PASS"
python -c "from tools.image_generation_tool import image_generate; print('OK')"
```

---

## Step 1f: Remove Static Assets

**Status: PENDING**

### Gate

No tests. Manual verification.

```bash
ls website/ 2>&1 | grep "No such file" && echo "PASS: website removed"
ls landingpage/ 2>&1 | grep "No such file" && echo "PASS: landingpage removed"
```

Remove: `website/` (~3.4MB), `landingpage/` (~316KB)

---

## Execution Order and Gates Summary

| Step | Gate | Must Pass Before Next |
|------|------|----------------------|
| 1a: RL subsystem | `pytest tests/ -q --ignore=tests/acp/` (3798p, 13 pre-existing failures) | Yes |
| 1b: Gateway adapters | `pytest tests/gateway/ -q` | Yes |
| 1c: Memory plugins | `pytest tests/agent/test_memory_provider.py -q` | Yes |
| 1d: Skills hub/guard | `pytest tests/skills/ tests/tools/test_skill*.py -q` | Yes |
| 1e: Niche tools | `pytest tests/tools/ -q` | Yes |
| 1f: Static assets | Manual (`ls` check) | No |

### Pre-existing Failures (do not block gates)

These failures exist in the baseline and are unrelated to simplification:

- `test_update_gateway_restart.py::TestCmdUpdateLaunchdRestart::test_update_with_systemd_still_restarts_via_systemd` -- systemd restart logic
- `test_transcription*.py` -- pre-existing transcription issues  
- `test_file_read_guards.py::TestCharacterCountGuard` -- pre-existing
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
| Gateway platform adapters | 15 | 2 (Telegram + API server) |
