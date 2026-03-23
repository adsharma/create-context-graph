# CLAUDE.md — Create Context Graph

## Project Overview

Interactive CLI scaffolding tool that generates domain-specific context graph applications. Like `create-next-app` but for AI agents with graph memory. Invoked via `uvx create-context-graph` or `npx create-context-graph`.

Given a domain (e.g., "healthcare", "wildlife-management") and an agent framework (e.g., PydanticAI, Claude Agent SDK), it generates a complete full-stack application: FastAPI backend, Next.js + Chakra UI v3 + NVL frontend, Neo4j schema, synthetic data, and a configured AI agent with domain-specific tools.

**Status:** Phase 6 complete (v0.3.0). 22 domains, 8 agent frameworks, neo4j-agent-memory integration for multi-turn conversations, interactive NVL graph visualization (schema view, double-click expand, drag/zoom, property panel, agent-driven graph updates), LLM-generated demo data (80-90 entities, 25+ documents, 3-5 decision traces per domain), markdown rendering in chat, tool call visualization, document browser, entity detail panel, 7 SaaS connectors, custom domain generation, Neo4j Aura .env import + neo4j-local support, Docusaurus documentation site, 314 passing tests.

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
├── custom_domain.py    # LLM-powered custom domain YAML generation
├── renderer.py         # Jinja2 template engine (renders project scaffold)
├── generator.py        # LLM-powered synthetic data pipeline (4 stages)
├── name_pools.py       # Realistic name pools and value generators for static fallback
├── ingest.py           # Neo4j ingestion via neo4j-agent-memory or direct driver
├── neo4j_validator.py  # Neo4j connection testing
├── connectors/         # SaaS data connectors (7 services)
│   ├── __init__.py     # BaseConnector ABC, NormalizedData model, registry
│   ├── github_connector.py
│   ├── notion_connector.py
│   ├── jira_connector.py
│   ├── slack_connector.py
│   ├── gmail_connector.py   # Prefers gws CLI, falls back to Python OAuth2
│   ├── gcal_connector.py    # Prefers gws CLI, falls back to Python OAuth2
│   ├── salesforce_connector.py
│   └── oauth.py        # Shared OAuth2 flow + gws CLI helpers
├── domains/            # 22 YAML ontology definitions + _base.yaml
├── fixtures/           # 22 pre-generated JSON fixture files
└── templates/          # Jinja2 templates for generated projects
    ├── base/           # .env, .env.example, Makefile, docker-compose, README, .gitignore
    ├── backend/
    │   ├── shared/     # FastAPI main, config, neo4j client, GDS, vector, models, routes
    │   ├── agents/     # Per-framework agent.py (8 frameworks)
    │   └── connectors/ # Generated connector modules + import_data.py
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

### Rich fixture data pipeline
- **Pre-generated fixtures** (shipped): All 22 domains ship with high-quality LLM-generated fixture data (80-90 entities, 160-280 relationships, 25+ documents at 200-1600 words, 3-5 decision traces with multi-step reasoning). Generated via `scripts/regenerate_fixtures.py` using Claude API.
- **Static fallback** (no LLM key at runtime): Uses realistic name pools (`name_pools.py`) organized by POLE+O type, contextual property generators (emails from names, realistic IDs, domain-appropriate ranges), and structured document templates.
- **LLM-powered** (with `--anthropic-api-key` at runtime): Generates realistic entities, documents, and decision traces via Anthropic or OpenAI APIs.
- **Data seeding** (`make seed`): Loads all four data types into Neo4j — entities, relationships, documents (as `:Document` nodes with `:MENTIONS` links to entities), and decision traces (as `:DecisionTrace` → `:HAS_STEP` → `:TraceStep` chains).

### Dual ingestion backends
`ingest.py` tries `neo4j-agent-memory` MemoryClient first (demonstrating all three memory types), falls back to direct `neo4j` driver if the package isn't installed.

### Custom domain generation
`custom_domain.py` generates complete domain ontology YAMLs from natural language descriptions using LLM (Anthropic/OpenAI). Uses `_base.yaml` + 2 reference domain YAMLs as few-shot examples. Validates output against `DomainOntology` Pydantic model with retry loop (up to 3 attempts). Generated domains can be saved to `~/.create-context-graph/custom-domains/` for reuse.

### Interactive graph visualization with agent integration
The frontend `ContextGraphView` starts in **schema view** (calls `db.schema.visualization()` via `GET /schema/visualization`) showing entity types as nodes and relationship types as edges. When the user interacts with the agent chat, tool call results flow to the graph automatically via a `CypherResultCollector` in `context_graph_client.py` — the `/chat` endpoint drains collected Cypher results and attaches them as `graph_data` in the response, without modifying any agent template. The `ChatInterface` passes `graph_data` to the parent `page.tsx` via an `onGraphUpdate` callback, which flows down to `ContextGraphView` as `externalGraphData`. Double-clicking a schema node loads instances of that label; double-clicking a data node calls `POST /expand` to fetch neighbors (deduplicated merge). NVL uses d3Force layout with drag/zoom/pan, click for property details, and canvas click to deselect.

### neo4j-agent-memory integration
Generated projects use `MemoryClient` from `neo4j-agent-memory` for multi-turn conversation persistence. The `context_graph_client.py.j2` template initializes the MemoryClient alongside the Neo4j driver (with ImportError fallback) and exposes `get_conversation_history()` and `store_message()`. All 8 agent frameworks call these to retrieve history before each LLM call and store messages after. The frontend `ChatInterface` captures `session_id` from the first response and sends it in all subsequent requests.

### Neo4j driver serialization
`context_graph_client.py.j2` uses a custom `_serialize()` function instead of the driver's `.data()` method. This preserves Neo4j Node metadata (`elementId`, `labels`), Relationship metadata (`elementId`, `type`, `startNodeElementId`, `endNodeElementId`), and Path expansion. Without this, the frontend graph visualization and agent tools receive flat property dicts with no type information.

### SaaS connectors
`connectors/` package with 7 service connectors (GitHub, Notion, Jira, Slack, Gmail, Google Calendar, Salesforce). Each connector implements `BaseConnector` ABC with `authenticate()`, `fetch()`, and `get_credential_prompts()` methods. Returns `NormalizedData` matching the fixture schema so `ingest.py` works unchanged. Gmail/Google Calendar prefer the Google Workspace CLI (`gws`) if available, with Python OAuth2 fallback. Connectors run at scaffold time AND are generated into the project with `make import` / `make import-and-seed` targets.

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
│   ├── connectors/       # Only if SaaS connectors selected
│   │   ├── __init__.py
│   │   └── {service}_connector.py  # One per selected service
│   └── __init__.py
├── backend/tests/
│   ├── __init__.py
│   └── test_routes.py    # Generated test scaffold (health, scenarios)
├── backend/scripts/
│   ├── generate_data.py
│   └── import_data.py    # Only if SaaS connectors selected
├── backend/pyproject.toml
├── frontend/             # Next.js + Chakra UI v3 + NVL
│   ├── app/ (layout.tsx, page.tsx, globals.css)
│   ├── components/ (ChatInterface, ContextGraphView, DecisionTracePanel, DocumentBrowser, Provider)
│   ├── lib/config.ts, theme/index.ts
│   └── package.json, next.config.ts, tsconfig.json
├── cypher/ (schema.cypher, gds_projections.cypher)
├── data/ (ontology.yaml, _base.yaml, fixtures.json, documents/)
├── .env, .env.example, Makefile, docker-compose.yml, README.md, .gitignore
```

## Testing

```bash
pytest tests/ -v                    # All 314 tests (512 with slow matrix)
pytest tests/test_config.py         # Config model + framework alias tests (19)
pytest tests/test_ontology.py       # Ontology loading + all 22 domains validate (20)
pytest tests/test_renderer.py       # Template rendering + all 8 frameworks + v0.3.0 features (52)
pytest tests/test_generator.py      # Data generation pipeline (14)
pytest tests/test_cli.py            # CLI integration + 8 domain/framework combos + neo4j types (18)
pytest tests/test_custom_domain.py  # Custom domain generation with mocked LLM (17)
pytest tests/test_connectors.py     # SaaS connectors with mocked APIs (23)
pytest tests/test_generated_project.py # Deep validation: Python/TS/Cypher syntax, memory, neo4j types (49+)
pytest tests/test_performance.py    # Timed generation tests (slow, 22 domains)
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
4. Import `get_conversation_history, store_message` from `context_graph_client` and call them in `handle_message()` for multi-turn conversation support
5. Pass `tool_name=` kwarg to `execute_cypher()` calls for tool call visualization
6. Use `{% raw %}...{% endraw %}` blocks for Python dict literals in the template
7. Use `{% for tool in agent_tools %}` to generate domain-specific tools from ontology
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
| Anthropic Tools | `anthropic_tools/` | Modular `@register_tool` registry + Anthropic API agentic loop |

## Adding a New SaaS Connector

1. Create `src/create_context_graph/connectors/{service}_connector.py` implementing `BaseConnector`
2. Use `@register_connector("service-id")` decorator to register it
3. Implement `authenticate(credentials)`, `fetch(**kwargs) -> NormalizedData`, and `get_credential_prompts()`
4. Add the import to `connectors/__init__.py`
5. Create `src/create_context_graph/templates/backend/connectors/{service}_connector.py.j2` (standalone version for generated projects)
6. Update `import_data.py.j2` to handle the new connector
7. Add tests to `test_connectors.py`

### Current connectors
| Service | Connector ID | Auth | Dependencies |
|---------|-------------|------|-------------|
| GitHub | `github` | Personal access token | PyGithub |
| Notion | `notion` | Integration token | notion-client |
| Jira | `jira` | API token | atlassian-python-api |
| Slack | `slack` | Bot OAuth token | slack-sdk |
| Gmail | `gmail` | gws CLI or OAuth2 | google-api-python-client, google-auth-oauthlib |
| Google Calendar | `gcal` | gws CLI or OAuth2 | google-api-python-client, google-auth-oauthlib |
| Salesforce | `salesforce` | Username/password | simple-salesforce |

## Dependencies

**Core:** click, questionary, rich, jinja2, pyyaml, pydantic, neo4j
**Optional:** anthropic, openai (for LLM data generation), neo4j-agent-memory (for memory-aware ingestion)
**Connectors (optional):** PyGithub, notion-client, atlassian-python-api, slack-sdk, google-api-python-client, google-auth-oauthlib, simple-salesforce
**Dev:** pytest, pytest-cov, pytest-asyncio
**Build:** hatchling (src layout, bundles YAML/JSON/Jinja2 files automatically)

## What's Not Yet Implemented

- End-to-end smoke tests with Neo4j in CI (generated app starts and responds to health check)
- TypeScript compilation validation in CI (requires Node.js in test environment)
