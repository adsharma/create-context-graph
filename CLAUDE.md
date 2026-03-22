# CLAUDE.md — Create Context Graph

## Project Overview

Interactive CLI scaffolding tool that generates domain-specific context graph applications. Like `create-next-app` but for AI agents with graph memory. Invoked via `uvx create-context-graph` or `npx create-context-graph`.

Given a domain (e.g., "healthcare", "wildlife-management") and an agent framework (e.g., PydanticAI, Claude Agent SDK), it generates a complete full-stack application: FastAPI backend, Next.js + Chakra UI v3 + NVL frontend, Neo4j schema, synthetic data, and a configured AI agent with domain-specific tools.

**Status:** Phase 3 complete. 22 domains, 8 agent frameworks, NVL graph visualization, data generation pipeline, 103 passing tests.

## Quick Reference

```bash
# Setup
uv venv && uv pip install -e ".[dev]"

# Run tests
source .venv/bin/activate && pytest tests/ -v

# Test scaffold generation
create-context-graph my-app --domain financial-services --framework pydanticai --demo-data

# List available domains
create-context-graph --list-domains
```

## Architecture

```
src/create_context_graph/
├── cli.py              # Click CLI entry point (interactive + flag modes)
├── wizard.py           # 7-step Questionary interactive wizard
├── config.py           # ProjectConfig Pydantic model
├── ontology.py         # YAML domain ontology loader, validation, code generation
├── renderer.py         # Jinja2 template engine (renders project scaffold)
├── generator.py        # LLM-powered synthetic data pipeline (4 stages)
├── ingest.py           # Neo4j ingestion via neo4j-agent-memory or direct driver
├── neo4j_validator.py  # Neo4j connection testing
├── domains/            # 22 YAML ontology definitions + _base.yaml
├── fixtures/           # 22 pre-generated JSON fixture files
└── templates/          # Jinja2 templates for generated projects
    ├── base/           # .env, Makefile, docker-compose, README, .gitignore
    ├── backend/
    │   ├── shared/     # FastAPI main, config, neo4j client, GDS, vector, models, routes
    │   └── agents/     # Per-framework agent.py (8 frameworks)
    ├── frontend/       # Next.js + Chakra UI v3 + NVL components
    └── cypher/         # Schema constraints + GDS projections
```

## Key Design Decisions

### Templates are domain-agnostic, data-driven
No per-domain template directories. The ontology YAML drives all domain customization via Jinja2 context variables. Only `backend/agents/{framework}/agent.py.j2` varies by framework — everything else is shared.

### Jinja2 + JSX/Python escaping
Templates that contain JSX curly braces or Python dict literals must use `{% raw %}...{% endraw %}` blocks to avoid conflicts with Jinja2's `{{ }}` syntax. Break out of raw mode only for actual Jinja2 substitutions:
```
{% raw %}JSX code with {curly} braces{% endraw %}{{ jinja_var }}{% raw %}more JSX{% endraw %}
```

### Two-layer ontology inheritance
`_base.yaml` defines shared POLE+O entity types (Person, Organization, Location, Event, Object). Domain YAMLs declare `inherits: _base` and add domain-specific entity types. The `ontology.py` loader merges base entities/relationships into each domain.

### Dual data generation modes
- **Static fallback** (no LLM key): Generates placeholder entities with `{Label} {N}` naming. Ships pre-generated fixtures in `fixtures/` directory.
- **LLM-powered** (with `--anthropic-api-key`): Generates realistic entities, documents, and decision traces via Anthropic or OpenAI APIs.

### Dual ingestion backends
`ingest.py` tries `neo4j-agent-memory` MemoryClient first (demonstrating all three memory types), falls back to direct `neo4j` driver if the package isn't installed.

## Domain Ontology YAML Schema

Each domain YAML file must contain:
- `inherits: _base` — merge base POLE+O types
- `domain:` — id, name, description, tagline, emoji
- `entity_types:` — label, pole_type (PERSON/ORGANIZATION/LOCATION/EVENT/OBJECT), subtype, color (hex), icon, properties (name, type, required, unique, enum)
- `relationships:` — type, source, target
- `document_templates:` — id, name, description, count, prompt_template, required_entities
- `decision_traces:` — id, task, steps (thought/action), outcome_template
- `demo_scenarios:` — name, prompts list
- `agent_tools:` — name, description, cypher query, parameters
- `system_prompt:` — multi-line agent system prompt
- `visualization:` — node_colors, node_sizes, default_cypher

Property types: `string`, `integer`, `float`, `boolean`, `date`, `datetime`, `point`
YAML booleans in enum values must be quoted: `enum: ["true", "false"]` not `enum: [true, false]`

## Generated Project Structure

When a user runs the CLI, the output is:
```
my-app/
├── backend/app/          # FastAPI + chosen agent framework
│   ├── main.py, config.py, routes.py, models.py
│   ├── agent.py          # Framework-specific (8 frameworks available)
│   ├── context_graph_client.py, gds_client.py, vector_client.py
│   └── __init__.py
├── backend/scripts/generate_data.py
├── backend/pyproject.toml
├── frontend/             # Next.js + Chakra UI v3 + NVL
│   ├── app/ (layout.tsx, page.tsx, globals.css)
│   ├── components/ (ChatInterface, ContextGraphView, DecisionTracePanel, Provider)
│   ├── lib/config.ts, theme/index.ts
│   └── package.json, next.config.ts, tsconfig.json
├── cypher/ (schema.cypher, gds_projections.cypher)
├── data/ (ontology.yaml, _base.yaml, fixtures.json, documents/)
├── .env, Makefile, docker-compose.yml, README.md, .gitignore
```

## Testing

```bash
pytest tests/ -v              # All 103 tests
pytest tests/test_config.py   # Config model tests (10)
pytest tests/test_ontology.py # Ontology loading + all 22 domains validate (20)
pytest tests/test_renderer.py # Template rendering + all 8 frameworks compile check (34)
pytest tests/test_generator.py # Data generation pipeline (14)
pytest tests/test_cli.py      # CLI integration + 8 domain/framework combos (15)
```

Tests do NOT require Neo4j or any API keys. All tests use `tmp_path` fixtures for output.

## Adding a New Domain

1. Create `src/create_context_graph/domains/{domain-id}.yaml` following the schema above
2. Generate fixture data: run the CLI with `--demo-data` or use `generator.py` directly
3. Copy the fixture to `src/create_context_graph/fixtures/{domain-id}.json`
4. Verify: `pytest tests/test_ontology.py::TestLoadAllDomains -v`

## Adding a New Agent Framework

1. Create `src/create_context_graph/templates/backend/agents/{framework_key}/agent.py.j2` (use underscores for directory name; hyphens in config key are auto-converted via `fw_key = framework.replace("-", "_")`)
2. Add the framework key to `SUPPORTED_FRAMEWORKS`, `FRAMEWORK_DISPLAY_NAMES`, and `FRAMEWORK_DEPENDENCIES` in `config.py`
3. Template must export `async def handle_message(message: str, session_id: str | None = None) -> dict` returning `{"response": str, "session_id": str, "graph_data": dict | None}`
4. Use `{% raw %}...{% endraw %}` blocks for Python dict literals in the template
5. Use `{% for tool in agent_tools %}` to generate domain-specific tools from ontology
6. The template receives full ontology context: `domain`, `agent_tools`, `system_prompt`, `framework_display_name`, etc.
7. Add tests to `TestAllFrameworksRender` in `test_renderer.py` and `TestMultipleDomainScaffolds` in `test_cli.py`

### Current frameworks and their patterns
| Framework | Directory | Pattern |
|-----------|-----------|---------|
| PydanticAI | `pydanticai/` | `@agent.tool` decorator + `RunContext[AgentDeps]` |
| Claude Agent SDK | `claude_agent_sdk/` | Dict-based TOOLS list + agentic while loop |
| OpenAI Agents SDK | `openai_agents/` | `@function_tool` decorator + `Runner.run()` |
| LangGraph | `langgraph/` | `@tool` + `create_react_agent()` |
| CrewAI | `crewai/` | `Agent` + `Task` + `Crew` with `@tool` |
| Strands | `strands/` | `Agent` with `@tool`, Bedrock model |
| Google ADK | `google_adk/` | `Agent` + `FunctionTool`, Gemini model |
| MAF | `maf/` | Modular tool registry with decorator pattern |

## Dependencies

**Core:** click, questionary, rich, jinja2, pyyaml, pydantic, neo4j
**Optional:** anthropic, openai (for LLM data generation), neo4j-agent-memory (for memory-aware ingestion)
**Dev:** pytest, pytest-cov, pytest-asyncio
**Build:** hatchling (src layout, bundles YAML/JSON/Jinja2 files automatically)

## What's Not Yet Implemented

- SaaS data connectors (Gmail, Slack, Jira, GitHub, Notion, Salesforce)
- Custom domain LLM generation ("describe your domain" flow)
- npm wrapper package for `npx create-context-graph`
- CI/CD and PyPI/npm publishing workflows
