# Deep Research Tool - Implementation Plan

**Branch:** `feat/deep-research`
**Scope:** Deep Research tool only, ship fast
**Approach:** Tool-only (Python)

---

## Goal

Add a `deep_research` tool to Hermes Agent that orchestrates multi-step research with a built-in source trust hierarchy. Accessible via CLI and Telegram (as a registered tool the agent can invoke).

## Source Trust Hierarchy

| Tier | Sources | Fetch Method |
|------|---------|-------------|
| Tier 1 | arXiv API, Semantic Scholar API, Wikipedia API | Direct API calls (no API keys needed) |
| Tier 2 | Web search filtered to known domains (nature.com, ieee.org, acm.org, etc.) | `web_search` with domain hints |
| Tier 3 | General web search | `web_search` default |

## New File: `tools/deep_research.py`

### Schema

```json
{
  "name": "deep_research",
  "description": "Conduct deep research on a topic using a source trust hierarchy...",
  "parameters": {
    "type": "object",
    "properties": {
      "topic": {"type": "string", "description": "Research topic"},
      "depth": {"type": "string", "enum": ["quick", "standard", "comprehensive"]},
      "focus_domains": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["topic"]
  }
}
```

### Execution Flow

```
1. Parse topic + depth
2. Parallel fetch:
   a. arXiv API (search + top N papers)
   b. Semantic Scholar API (search + citations)
   c. Wikipedia API (summary + references)
   d. web_search (Tier 2 domains if depth > quick)
   e. web_search (general, if depth == comprehensive)
3. For each result: extract content via web_extract or direct API
4. Rank by tier, recency, citation count (for academic)
5. Synthesize report with:
   - Executive summary
   - Key findings per tier
   - Full citations with URLs
   - Confidence assessment
6. Return JSON string
```

### Registration Pattern

```python
from tools.registry import registry

def check_requirements() -> bool:
    return True  # No special API keys needed (arXiv + Semantic Scholar are free)

registry.register(
    name="deep_research",
    toolset="web",
    schema={...},
    handler=lambda args, **kw: deep_research_tool(
        topic=args.get("topic", ""),
        depth=args.get("depth", "standard"),
        focus_domains=args.get("focus_domains"),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_requirements,
    requires_env=[],
)
```

## Integration Points

1. **`model_tools.py`** -- add `import tools.deep_research` to `_discover_tools()`
2. **`toolsets.py`** -- add `deep_research` to the `web` toolset
3. **Telegram** -- works automatically (registered tool the agent can invoke)

## Dependencies

Only existing ones: `httpx`, existing `web_tools` functions, arXiv/Semantic Scholar/Wikipedia APIs (all free, no API keys).

## Depth Levels

| Depth | arXiv | Semantic Scholar | Wikipedia | Tier 2 Web | General Web | Max Sources |
|-------|-------|-----------------|-----------|------------|-------------|-------------|
| quick | top 3 | top 3 | yes | no | no | ~8 |
| standard | top 5 | top 5 | yes | yes | no | ~15 |
| comprehensive | top 10 | top 10 | yes | yes | yes | ~25 |

## Test Plan

- [ ] Unit tests for source tier ranking logic
- [ ] Unit tests for arXiv/Semantic Scholar API response parsing
- [ ] Integration test with mocked web_search/web_extract
- [ ] Manual test via CLI
- [ ] Manual test via Telegram

## Phases

1. **Skeleton** -- tool registration, schema, handler stub, integration in model_tools + toolsets
2. **Tier 1 fetchers** -- arXiv API client, Semantic Scholar API client, Wikipedia API client
3. **Tier 2/3 fetchers** -- web_search integration with domain filtering
4. **Ranking + synthesis** -- tier ranking, recency scoring, citation weighting, report generation
5. **Tests** -- unit + integration tests
6. **Manual verification** -- CLI test, then Telegram test
