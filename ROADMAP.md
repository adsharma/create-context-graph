# Roadmap — Create Context Graph

> Last updated: March 22, 2026

## Overview

Create Context Graph was built in 6 phases. The goal was to go from an empty repository to a published CLI tool that generates domain-specific context graph applications for 22 industry verticals with 8 agent framework options, powered by neo4j-agent-memory for multi-turn conversations.

---

## Phase 1: Core CLI & Template Engine — COMPLETE

**Timeline:** Weeks 1–3
**Status:** Done

Built the foundational scaffolding tool: Python package structure, CLI, interactive wizard, template engine, and initial templates.

### What was built

- **Python package** (`src/create_context_graph/`) with `hatchling` build, `src` layout, entry point via `create-context-graph` command
- **Click CLI** (`cli.py`) with both interactive and non-interactive (flag-based) modes
- **Interactive wizard** (`wizard.py`) — 7-step flow using Questionary + Rich: project name, data source, domain selection, agent framework, Neo4j connection, API keys, confirmation
- **ProjectConfig model** (`config.py`) — Pydantic model holding all wizard outputs, computed slug, framework display names and dependency mappings for all 8 planned frameworks
- **Domain ontology system** (`ontology.py`) — YAML loader with two-layer inheritance (`_base.yaml` + domain YAML), Pydantic validation models for all ontology sections, code generation helpers (Cypher schema, Pydantic models, NVL visualization config)
- **Jinja2 template engine** (`renderer.py`) — `PackageLoader`-based renderer with custom filters (`snake_case`, `camel_case`, `pascal_case`, `kebab_case`), renders full project directory from templates + ontology context
- **3 initial domain ontologies** — Financial Services, Healthcare, Software Engineering (complete with entity types, relationships, document templates, decision traces, demo scenarios, agent tools, system prompts, visualization config)
- **Backend templates** — FastAPI main, config, Neo4j client, GDS client, vector search client, Pydantic models, REST routes, pyproject.toml, data generation script, agent stub fallback
- **2 agent framework templates** — PydanticAI (structured tool definitions with `RunContext`) and Claude Agent SDK (Anthropic tool-use with agentic loop)
- **Frontend templates** — Next.js 15 + Chakra UI v3 + NVL: layout, page (3-panel), ChatInterface, ContextGraphView, DecisionTracePanel, Provider, domain config, theme
- **Base templates** — `.env`, `Makefile`, `docker-compose.yml`, `README.md`, `.gitignore`
- **Cypher templates** — Schema constraints/indexes from ontology, GDS graph projections
- **Neo4j connection validator** (`neo4j_validator.py`)

### Key design decisions made

- Templates are **domain-agnostic, data-driven** — no per-domain template directories; the ontology YAML drives all customization
- Only `agent.py` varies by framework; everything else is shared
- JSX/Python dict literals in templates use `{% raw %}...{% endraw %}` blocks to avoid Jinja2 conflicts
- Pre-built fixtures are bundled and copied into every generated project

---

## Phase 2: Domain Expansion & Document Generation — COMPLETE

**Timeline:** Weeks 4–6
**Status:** Done

Expanded from 3 domains to 22, built the synthetic data generation pipeline, and created the Neo4j ingestion system.

### What was built

- **19 additional domain ontology YAMLs** — All validated and scaffold-tested. Domains: Agent Memory, Conservation, Data Journalism, Digital Twin, Gaming, GenAI/LLM Ops, GIS & Cartography, Golf & Sports Mgmt, Hospitality, Manufacturing, Oil & Gas, Personal Knowledge, Product Management, Real Estate, Retail & E-Commerce, Scientific Research, Trip Planning, Vacation Industry, Wildlife Management
- **Synthetic data generation pipeline** (`generator.py`) — 4-stage pipeline:
  1. **Entity seeding** — LLM-powered or static fallback, generates 5+ entities per type with properties matching ontology schema
  2. **Relationship weaving** — Connects entities based on ontology relationship definitions, avoids self-relationships
  3. **Document generation** — Produces 25+ documents across all template types defined in the ontology (LLM-powered for realistic content, static fallback for offline use)
  4. **Decision trace injection** — Creates reasoning traces from ontology scenarios with thought/action/observation steps
- **LLM client abstraction** — Supports both Anthropic and OpenAI as generation providers, graceful fallback to static data when no API key is available
- **Data ingestion system** (`ingest.py`) — Dual-backend ingestion:
  - Primary: `neo4j-agent-memory` MemoryClient (long-term entities, short-term documents, reasoning traces — all three memory types)
  - Fallback: Direct `neo4j` driver when neo4j-agent-memory isn't installed
  - Schema application from generated Cypher
- **Pre-generated fixture files** — All 22 domains ship with static `fixtures/{domain-id}.json` files so projects work immediately without an LLM API key
- **CLI integration** — `--demo-data` flag triggers generation, `--ingest` flag triggers Neo4j ingestion, `--anthropic-api-key` enables LLM-powered generation, pre-built fixtures always copied into `data/fixtures.json`
- **Comprehensive test suite** (85 tests, all passing):
  - `test_config.py` — 10 unit tests for ProjectConfig
  - `test_ontology.py` — 20 unit tests including parametric validation of all 22 domains
  - `test_renderer.py` — 18 unit tests for rendering, file structure, framework selection, Python compile verification
  - `test_generator.py` — 14 unit tests for data generation across 6 domains
  - `test_cli.py` — 13 integration tests for CLI invocation, 6 domain/framework combinations

### Verified

- All 22 domains load and validate without errors
- 18/18 domain+framework combinations scaffold successfully (9 domains x 2 frameworks)
- Generated Python files pass `compile()` syntax check
- 85/85 tests pass in 3.4 seconds

---

## Phase 3: Framework Templates & Frontend — COMPLETE

**Timeline:** Weeks 7–8
**Status:** Done

Added all 8 agent framework templates, replaced NVL placeholder with real graph visualization, and expanded the test suite.

### What was built

- **6 new agent framework templates** — All in `templates/backend/agents/`, each generating valid Python with domain-specific tools from ontology:
  - **OpenAI Agents SDK** (`openai_agents/`) — `@function_tool` decorators + `Runner.run()`
  - **LangGraph** (`langgraph/`) — `@tool` + `create_react_agent()` with `ChatAnthropic`
  - **CrewAI** (`crewai/`) — `Agent` + `Task` + `Crew` with `@tool` decorator
  - **Strands (AWS)** (`strands/`) — `Agent` with `@tool`, Bedrock model
  - **Google ADK** (`google_adk/`) — `Agent` + `FunctionTool`, Gemini model, async runner
  - **MAF** (`maf/`) — Modular tool registry with decorator pattern
- **NVL graph visualization** — Replaced placeholder in `ContextGraphView.tsx` with real `@neo4j-nvl/react` `InteractiveNvlWrapper` component: force-directed layout, domain-colored nodes via `NODE_COLORS`/`NODE_SIZES`, node click handler, color legend
- **Makefile improvements** — Added `make test` and `make lint` targets
- **Expanded test suite** (103 tests, all passing in 3.78s):
  - `TestAllFrameworksRender` — 8 parametric tests verifying each framework's agent.py compiles and contains framework-specific imports
  - `TestAllFrameworksRender` — 8 parametric tests verifying each framework's pyproject.toml contains correct dependencies
  - `TestMultipleDomainScaffolds` — Expanded from 6 to 8 domain/framework combinations covering all frameworks

### Verified

- All 8 frameworks scaffold, render, and compile without errors
- All 8 frameworks produce correct `pyproject.toml` dependencies
- Each framework's agent.py contains the expected framework marker (import/class name)
- 103/103 tests pass in 3.78 seconds

---

## Phase 4: SaaS Import & Custom Domains — COMPLETE

**Timeline:** Weeks 9–10
**Status:** Done

Implemented SaaS data connectors for 7 services and LLM-powered custom domain generation.

### What was built

#### SaaS data connectors

- **Connectors package** (`connectors/`) — `BaseConnector` ABC, `NormalizedData` Pydantic model matching fixture schema, connector registry with `@register_connector` decorator
- **7 service connectors**, each with `authenticate()`, `fetch()`, and `get_credential_prompts()`:

| Service | Connector | Auth Method | Dependencies |
|---------|-----------|-------------|-------------|
| GitHub | `github_connector.py` | Personal access token | PyGithub |
| Notion | `notion_connector.py` | Integration token | notion-client |
| Jira | `jira_connector.py` | API token | atlassian-python-api |
| Slack | `slack_connector.py` | Bot OAuth token | slack-sdk |
| Gmail | `gmail_connector.py` | gws CLI or OAuth2 | google-api-python-client, google-auth-oauthlib |
| Google Calendar | `gcal_connector.py` | gws CLI or OAuth2 | google-api-python-client, google-auth-oauthlib |
| Salesforce | `salesforce_connector.py` | Username/password + security token | simple-salesforce |

- **Google Workspace CLI (`gws`) integration** — Gmail and Google Calendar connectors detect `gws` on PATH, offer to install via npm if missing, fall back to Python OAuth2
- **OAuth2 local redirect flow** (`oauth.py`) — Temporary HTTP server on random port, browser consent, auth code capture, token exchange
- **Dual-purpose connectors** — Run at scaffold time to populate initial data AND generated into the scaffolded project for ongoing `make import` / `make import-and-seed` usage
- **Connector templates** — 7 standalone connector `.py.j2` templates + `import_data.py.j2` generated into scaffolded projects (only for selected connectors)
- **Makefile targets** — `make import` and `make import-and-seed` added to generated projects when SaaS connectors are selected
- **Wizard integration** — Checkbox selection of connectors, credential prompts, gws CLI detection and install prompt
- **CLI flags** — `--connector` (multiple) for non-interactive connector selection
- **Optional dependencies** — New `[connectors]` extra in pyproject.toml

#### Custom domain generation

- **`custom_domain.py`** — LLM-powered domain YAML generation:
  1. Loads `_base.yaml` + 2 reference domain YAMLs (healthcare, wildlife-management) as few-shot examples
  2. Builds prompt with complete YAML schema specification
  3. Calls LLM (Anthropic/OpenAI) via existing `generator.py` abstraction
  4. Parses YAML, validates against `DomainOntology` Pydantic model
  5. On validation failure, retries with error feedback (up to 3 attempts)
  6. Returns `(DomainOntology, raw_yaml_string)`
- **`ontology.py` extensions** — `load_domain_from_yaml_string()`, `load_domain_from_path()`, `list_available_domains()` now scans `~/.create-context-graph/custom-domains/`
- **Wizard integration** — Description prompt → LLM generation with spinner → Rich summary table → accept/regenerate/edit → optional save for reuse
- **CLI flag** — `--custom-domain "description"` for non-interactive custom domain generation
- **Renderer support** — Custom domain YAML written directly to `data/ontology.yaml`
- **Persistence** — Custom domains saved to `~/.create-context-graph/custom-domains/` and appear in future wizard runs

### Bug fixes

- Fixed `cli.py:73` — `data_source` was always `"demo"` regardless of flags

### Tests added (40 new tests)

- `test_custom_domain.py` — 17 tests: YAML string loading, base merge, validation errors, prompt construction, mocked LLM generation (success, retry, max retries), display, save, custom domain listing
- `test_connectors.py` — 23 tests: NormalizedData model, merge, registry (7 connectors), credential prompts, mocked fetch for GitHub/Notion/Jira/Slack/Gmail/GCal/Salesforce, OAuth helpers

### Verified

- All 7 connectors register and expose credential prompts
- Mocked connector fetches return valid NormalizedData
- Custom domain generation succeeds with mocked LLM
- Custom domain retry loop works on validation failure
- 182/182 tests pass in 5.2 seconds

---

## Phase 5: Polish, Testing & Launch — COMPLETE

**Timeline:** Weeks 11–12
**Status:** Done

Prepared for public release with Docusaurus documentation, Neo4j Labs compliance, enhanced testing, and version 0.2.0.

### What was built

#### Docusaurus documentation site

- **Docusaurus 3.x** site in `docs/` with TypeScript config, Diataxis-organized sidebar
- **11 documentation pages** following the Diataxis framework:
  - **Tutorials:** Your First Context Graph App, Customizing Your Domain Ontology
  - **How-To Guides:** Import Data from SaaS Services, Add a Custom Domain, Switch Agent Frameworks
  - **Reference:** CLI Options & Flags, Ontology YAML Schema, Generated Project Structure
  - **Explanation:** How Domain Ontologies Work, Why Context Graphs Need All Three Memory Types
- **GitHub Pages deployment** via `.github/workflows/deploy-docs.yml` (triggers on `docs/` changes to main)
- Site URL: `https://neo4j-labs.github.io/create-context-graph/`

#### Neo4j Labs compliance

- **Apache-2.0 license headers** added to all 32 Python source and test files
- **Labs badge** added to `README.md` and generated project README template
- **Community support disclaimer** updated to standard Neo4j Labs language
- **CONTRIBUTING.md** — Getting started, adding domains/frameworks/connectors, testing, PR process

#### Testing improvements

- **Cypher syntax validation** in `test_generated_project.py` — validates statement keywords and semicolons
- **Frontend syntax validation** — TSX files checked for imports and exports, `config.ts` validated for required exports
- **Timed performance test** (`test_performance.py`) — all 22 domains must scaffold in < 120 seconds each (slow marker)

#### Publishing

- **Version bumped to 0.2.0** across `pyproject.toml`, `npm-wrapper/package.json`, and `__init__.py`
- Publishing workflows already in place from prior phases (PyPI + npm on version tags)

### Success metrics achieved

| Metric | Target | Actual |
|--------|--------|--------|
| Time to running app | < 5 minutes | ~2 minutes (scaffold + install + start) |
| Domain coverage | 22 domains | 22 domains |
| Framework coverage | 8 agent frameworks | 8 agent frameworks |
| Generation success rate | >= 95% | 100% (176/176 matrix combos pass) |
| Test suite | 100+ tests | 262 tests (460 with slow matrix) |

---

## Post-Launch: Data Quality & UI Enhancements — COMPLETE

**Status:** Done

### Fixture data quality overhaul

- **`name_pools.py`** — Realistic name pools (25 person names, 20 org names, etc.) and contextual value generators (emails from names, realistic IDs, domain-appropriate ranges)
- **Improved static fallback** in `generator.py` — produces passable data without an LLM (realistic names, structured documents, interpolated trace outcomes)
- **`scripts/regenerate_fixtures.py`** — One-time script to regenerate all 22 fixtures using Claude API with coherent cross-entity prompts, validation, and retry logic
- **All 22 fixtures regenerated** with LLM-quality data: 80-90 entities, 160-280 relationships, 25+ documents (200-1600 words each), 3-5 decision traces with specific observations and outcomes
- **Fixture quality tests** — 66 parametrized tests across all 22 domains verify no placeholder names, documents >= 200 chars, no uninterpolated template variables

### Full fixture data utilization in generated apps

- **`generate_data.py.j2`** updated — `make seed` now loads all 4 data types: entities, relationships, documents (as `:Document` nodes with `:MENTIONS` entity links), and decision traces (as `:DecisionTrace` → `:HAS_STEP` → `:TraceStep` chains)
- **4 new API endpoints** in `routes.py.j2`:
  - `GET /documents` — list with template filter, previews, mentioned entities
  - `GET /documents/{title}` — full document content
  - `GET /traces` — traces with full reasoning steps
  - `GET /entities/{name}` — all properties, labels, and connections
- **Document browser** (`DocumentBrowser.tsx.j2`) — template type filter badges, scrollable list with previews, full document viewer with mentioned entity badges
- **Entity detail panel** in `ContextGraphView.tsx.j2` — click any graph node to see all properties, labels, and connections with relationship types/directions
- **Fixed DecisionTracePanel** — uses new `/traces` endpoint, loads steps with observations (was previously broken: wrong node label, empty steps array)
- **Tabbed right panel** in `page.tsx.j2` — Traces and Documents tabs using Chakra UI v3 compound Tabs components
- **Schema indexes** for `Document` and `DecisionTrace` nodes added to `generate_cypher_schema()`

---

## Graph Visualization & Agent Fixes — COMPLETE

**Status:** Done

### Interactive graph visualization

- **Schema view on load** — Graph starts by calling `db.schema.visualization()` (via new `GET /schema/visualization` endpoint), showing entity type labels as nodes and relationship types as edges. No data query on initial load.
- **Agent-driven graph updates** — `CypherResultCollector` in `context_graph_client.py` captures all Cypher results from agent tool calls. The `/chat` endpoint drains collected results and attaches them as `graph_data` in the response. `ChatInterface` passes `graph_data` to `page.tsx` via `onGraphUpdate` callback, which flows to `ContextGraphView` as `externalGraphData`. Works for all 8 agent frameworks without modifying any agent template.
- **Double-click to expand** — Schema nodes load instances of that label (`MATCH (n:\`Label\`)-[r]-(m) RETURN n,r,m LIMIT 50`). Data nodes call new `POST /expand` endpoint to fetch neighbors. Expanded data is merged with deduplication.
- **NVL d3Force layout** — Replaced `InteractiveNvlWrapper` configuration: d3Force layout, zoom 0.1–5x, relationship thickness 2, dynamic import for SSR avoidance. Uses `mouseEventCallbacks` for node click, double-click, relationship click, canvas click.
- **Property details panel** — Click any node to see labels (color badges), all properties (key-value list), and metadata. Click relationships to see type and properties. Canvas click deselects.
- **UI overlays** — Color legend (top 6 node types), instructions overlay, loading spinner during expansion, back-to-schema button, schema/data mode indicator.
- **State management** — `page.tsx` lifts `graphData` state with `useState`/`useCallback`. Props flow down, callbacks flow up. No external state library.

### Neo4j driver serialization fix

- **`_serialize()` function** in `context_graph_client.py.j2` — Replaced `result.data()` (which strips metadata) with per-record iteration and custom serialization preserving Node (`elementId`, `labels`), Relationship (`elementId`, `type`, `startNodeElementId`, `endNodeElementId`), and Path objects.

### MAF agent template fix

- **Bug:** MAF agent used keyword-based tool dispatch (lines 75-114) that never called an LLM. Fallback echoed system prompt: `"I'm your {SYSTEM_PROMPT}... Available tools: ..."`.
- **Fix:** Rewrote `handle_message()` with Anthropic API tool-use loop (matching `claude_agent_sdk` pattern). Kept `TOOL_REGISTRY` + `@register_tool` decorator. Added `_build_tool_definitions()` that introspects registry via `inspect.signature` to generate Anthropic tool schemas. Added `anthropic>=0.30` to MAF framework dependencies.

### New backend endpoints

- `GET /schema/visualization` — Returns schema graph via `db.schema.visualization()` (with fallback to basic labels/types)
- `POST /expand` (body: `{element_id}`) — Returns immediate neighbors with nodes and relationships for graph expansion

### Files modified

- `config.py` — Added `anthropic>=0.30` to MAF deps
- `templates/backend/agents/maf/agent.py.j2` — Full rewrite
- `templates/backend/shared/context_graph_client.py.j2` — `_serialize()`, `CypherResultCollector`, `get_schema_visualization()`, `expand_node()`
- `templates/backend/shared/routes.py.j2` — New endpoints, collector integration in `/chat`
- `templates/frontend/components/ContextGraphView.tsx.j2` — Complete rewrite (~480 lines)
- `templates/frontend/components/ChatInterface.tsx.j2` — `onGraphUpdate` prop
- `templates/frontend/app/page.tsx.j2` — State lifting
- `templates/frontend/lib/config.ts.j2` — `GraphData` type, schema constants

---

## Phase 6: Memory Integration, Multi-Turn & DX — COMPLETE

**Status:** Done (v0.3.0)

Addressed all critical and high-priority feedback from the v0.2.0 product review. Core theme: make the generated apps actually use neo4j-agent-memory and deliver a compelling multi-turn conversation experience.

### Critical fixes

- **neo4j-agent-memory integration** — Generated `context_graph_client.py` now initializes `MemoryClient` alongside the Neo4j driver (with ImportError fallback). Exposes `get_conversation_history()` and `store_message()` functions used by all 8 agent frameworks for multi-turn conversation persistence.
- **Multi-turn conversations** — All 8 agent templates retrieve conversation history before each LLM call and store messages after. Frontend `ChatInterface` captures `session_id` from the first response and sends it in all subsequent requests. "New Conversation" button resets session state.
- **CrewAI/Strands/Google ADK async fix** — Added `nest_asyncio` to prevent `asyncio.run()` deadlocks inside FastAPI's async event loop. Added to `FRAMEWORK_DEPENDENCIES` for all three frameworks.
- **MAF → Anthropic Tools rebrand** — Renamed framework from `maf` to `anthropic-tools`. Template directory moved to `anthropic_tools/`. Old `maf` key supported as deprecated alias via `FRAMEWORK_ALIASES`. Updated all tests.

### High-priority fixes

- **GDS client** — Changed default label from hardcoded `"Entity"` to `"*"` (wildcard). Exposed `ENTITY_LABELS` list generated from domain ontology.
- **Markdown rendering** — Added `react-markdown` + `remark-gfm` to frontend. Assistant messages render through ReactMarkdown with CSS styles for headings, lists, code blocks, tables, blockquotes.
- **.env.example** — Generated alongside `.env` with placeholder values (`your-password-here`). Added to renderer and gitignore correctly.

### Neo4j setup options (new)

- **Neo4j Aura import** — New wizard option "Neo4j Aura (cloud — free tier available)" with signup instructions panel and `.env` file parser. CLI flag: `--neo4j-aura-env PATH`.
- **neo4j-local** — New wizard option "Local Neo4j via neo4j-local (no Docker required)". Generates `make neo4j-start/stop/status` targets using `npx @johnymontana/neo4j-local`. CLI flag: `--neo4j-local`.
- **`neo4j_type` expanded** — Config Literal from `"docker" | "existing"` to `"docker" | "existing" | "aura" | "local"`. Makefile, README, docker-compose all render conditionally based on type.

### Medium-priority fixes

- **Port configurability** — CORS reads from `settings.frontend_port`. Makefile uses `include .env` / `export` with `$${BACKEND_PORT:-8000}` and `$${FRONTEND_PORT:-3000}` defaults.
- **Process management** — `make start` uses `trap 'kill 0' EXIT` to clean up child processes on Ctrl+C.
- **Docker version pin** — `neo4j:5` → `neo4j:5.26.0` in docker-compose template.
- **README entity types** — Split into "Base POLE+O Entities" and "Domain-Specific Entities" subsections.
- **Vector index creation** — `create_vector_index()` called in app lifespan startup (try/except for Neo4j < 5.13).

### Enhancements

- **Tool call visualization** — `CypherResultCollector` extended with `tool_calls` tracking. `ChatResponse` includes `tool_calls` field. Frontend renders inline tool call cards (badge + abbreviated inputs) above assistant messages.
- **Test scaffold** — Generated projects include `backend/tests/test_routes.py` with `test_health()` and `test_scenarios()` tests using mocked Neo4j.

### Tests added (52 new tests → 314 total)

- **test_renderer.py** (+18): .env.example, session_id, ReactMarkdown, memory functions, GDS labels, tool calls, README sections, CORS, vector index, docker pin, trap cleanup, neo4j-local/aura Makefile targets, markdown CSS
- **test_generated_project.py** (+22): .env.example, ChatInterface features, memory integration, docker pin, neo4j type variations, test scaffold
- **test_config.py** (+9): aura/local neo4j types, framework alias resolution (maf→anthropic-tools)
- **test_cli.py** (+3): --neo4j-aura-env, --neo4j-local, maf alias backward compatibility

### Files modified

- `config.py` — SUPPORTED_FRAMEWORKS, FRAMEWORK_ALIASES, FRAMEWORK_DEPENDENCIES, neo4j_type Literal, resolved_framework property
- `cli.py` — --neo4j-aura-env, --neo4j-local flags, alias resolution
- `wizard.py` — 4 Neo4j options (Aura, local, Docker, existing), _parse_aura_env helper
- `renderer.py` — .env.example rendering, base/domain entity type partition, test scaffold rendering, resolved_framework in context
- `templates/backend/shared/context_graph_client.py.j2` — MemoryClient init, get_conversation_history(), store_message(), tool call collector
- `templates/backend/shared/routes.py.j2` — tool_calls in ChatResponse
- `templates/backend/shared/main.py.j2` — CORS from settings, vector index startup
- `templates/backend/shared/gds_client.py.j2` — wildcard label, ENTITY_LABELS
- `templates/backend/agents/*/agent.py.j2` — all 8 frameworks: multi-turn history, tool_name tracking
- `templates/backend/agents/maf/` → `templates/backend/agents/anthropic_tools/` — renamed
- `templates/frontend/components/ChatInterface.tsx.j2` — session_id, ReactMarkdown, tool call cards, new conversation button
- `templates/frontend/package.json.j2` — react-markdown, remark-gfm
- `templates/frontend/app/globals.css.j2` — .markdown-content styles
- `templates/base/Makefile.j2` — env vars, trap cleanup, neo4j-local targets
- `templates/base/docker-compose.yml.j2` — neo4j:5.26.0
- `templates/base/dot_env_example.j2` — new file
- `templates/base/README.md.j2` — entity sections, neo4j-type-aware instructions, .env.example docs
- `templates/backend/tests/test_routes.py.j2` — new test scaffold template

---

## Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| 1 | Core CLI & Template Engine | **Complete** | 314 passing |
| 2 | Domain Expansion & Data Generation | **Complete** | (included above) |
| 3 | Framework Templates & Frontend | **Complete** | (included above) |
| 4 | SaaS Import & Custom Domains | **Complete** | (included above) |
| 5 | Polish, Testing & Launch | **Complete** | (included above) |
| — | Data Quality & UI Enhancements | **Complete** | (included above) |
| — | Graph Visualization & Agent Fixes | **Complete** | (included above) |
| 6 | Memory Integration, Multi-Turn & DX | **Complete** | (included above) |
