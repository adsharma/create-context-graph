# Roadmap — Create Context Graph

> Last updated: March 21, 2026

## Overview

Create Context Graph is being built in 5 phases over ~12 weeks. The goal is to go from an empty repository to a published CLI tool that generates domain-specific context graph applications for 22 industry verticals with 8 agent framework options.

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

## Phase 4: SaaS Import & Custom Domains — NOT STARTED

**Timeline:** Weeks 9–10
**Status:** Planned

### Goals

Enable real data import from SaaS services and LLM-powered custom domain generation.

### Planned work

#### SaaS data connectors

When the user selects "Connect to SaaS services" in the wizard, present prompts for service API keys. Each connector: fetch data, normalize to common document format, ingest via MemoryClient.

| Service | Data Imported | Auth Method |
|---------|--------------|-------------|
| Gmail | Emails (last 30 days, up to 200) | OAuth2 / App Password |
| Google Calendar | Calendar events (last 90 days) | OAuth2 |
| Slack | Channel messages (configurable channels) | Bot token |
| Jira | Issues and comments (configurable project) | API token |
| GitHub | Issues, PRs, commits (configurable repo) | Personal access token |
| Notion | Pages and databases | Integration token |
| Salesforce | Accounts, contacts, opportunities | OAuth2 / Connected App |

Implementation: `src/create_context_graph/connectors/` with one module per service. Each connector implements a `fetch()` method that returns normalized documents.

OAuth2 services require a local redirect flow: temporary HTTP server on a random port, browser-based consent, auth code capture, token exchange.

#### Custom domain generation

When the user selects "Custom (describe your domain)":
1. Prompt for natural language domain description
2. Send to LLM with `_base.yaml` + 2 reference domain YAMLs as few-shot examples
3. LLM generates complete domain YAML
4. Validate against `DomainOntology` Pydantic model (entity types have valid POLE+O types, relationships reference existing entities, at least 3 entity types, property types from allowed set, colors are valid hex)
5. If validation fails, retry with error feedback (up to 3 attempts)
6. Show generated ontology summary to user for confirmation
7. Proceed with normal scaffolding pipeline

### Tests to add

- Custom domain generation with mock LLM responses
- Connector unit tests with mock API responses
- Validation tests for malformed custom ontologies

---

## Phase 5: Polish, Testing & Launch — NOT STARTED

**Timeline:** Weeks 11–12
**Status:** Planned

### Goals

Prepare for public release: npm wrapper, comprehensive testing, documentation, and publishing.

### Planned work

#### npm wrapper package

`npm-wrapper/` — Thin Node.js shim published as `create-context-graph` on npm:
1. Try `uvx create-context-graph` (preferred — uv's ephemeral environment)
2. Fallback: `pipx run create-context-graph`
3. Fallback: `python3 -m create_context_graph`
4. If none work: print clear error with install instructions for `uv`

All `process.argv.slice(2)` forwarded to the Python process.

#### End-to-end testing

- CI matrix: all 22 domains x 2 frameworks (PydanticAI + Claude Agent SDK) minimum
- Extended matrix: spot-check remaining frameworks
- Verify: directory structure, valid Python syntax, valid TypeScript/JSX syntax, Cypher syntax
- Timed test: generation completes in < 2 minutes per domain
- Smoke test: generated app starts and responds to health check (requires Neo4j in CI)

#### Documentation (Diataxis framework)

| Type | Page | Description |
|------|------|-------------|
| Tutorial | Your First Context Graph App | Step-by-step: install, run wizard, explore the generated app |
| Tutorial | Customizing Your Domain Ontology | Modify a generated ontology and re-seed data |
| How-To | Import Data from Gmail & Slack | Connect SaaS services and import real data |
| How-To | Add a Custom Domain | Use the Custom option or write ontology YAML manually |
| How-To | Switch Agent Frameworks | Regenerate with a different framework, preserving data |
| Reference | CLI Options & Flags | Complete reference for all CLI arguments |
| Reference | Ontology YAML Schema | Schema definition for domain ontology files |
| Reference | Generated Project Structure | Every file and directory in the output, explained |
| Explanation | How Domain Ontologies Work | Conceptual guide to the ontology-driven generation system |
| Explanation | Why Context Graphs Need All Three Memory Types | Short-term + long-term + reasoning = context graph |

#### Neo4j Labs compliance

- Labs badge in README and all generated READMEs
- Community-support disclaimer
- Apache-2.0 license headers in all source files
- Contribution guidelines (CONTRIBUTING.md)

#### Publishing

- **PyPI:** GitHub Actions workflow triggered on version tags, publishes to PyPI
- **npm:** GitHub Actions workflow publishes npm-wrapper on the same tag
- **Versioning:** Both packages use the same version, bumped together

### Success metrics

| Metric | Target |
|--------|--------|
| Time to running app | < 5 minutes (excluding Neo4j provisioning) |
| Domain coverage | 22 domains at launch |
| Framework coverage | 8 agent frameworks at launch |
| Generation success rate | >= 95% first-attempt success across all domain x framework combinations |
| Test suite | 100+ tests, all passing |

---

## Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| 1 | Core CLI & Template Engine | **Complete** | 103 passing |
| 2 | Domain Expansion & Data Generation | **Complete** | (included above) |
| 3 | Framework Templates & Frontend | **Complete** | (included above) |
| 4 | SaaS Import & Custom Domains | Not started | — |
| 5 | Polish, Testing & Launch | Not started | — |
