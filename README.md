# Create Context Graph

[![Neo4j Labs](https://img.shields.io/badge/Neo4j_Labs-blue?logo=neo4j)](https://neo4j.com/labs/)
[![Docs](https://img.shields.io/badge/docs-docusaurus-green)](https://create-context-graph.vercel.app/)

> **Neo4j Labs Project** — This project is part of [Neo4j Labs](https://neo4j.com/labs/). It is maintained by Neo4j staff and the community, but not officially supported. For help, use [GitHub Issues](https://github.com/neo4j-labs/create-context-graph/issues) or the [Neo4j Community Forum](https://community.neo4j.com/).

Interactive CLI scaffolding tool that generates fully-functional, domain-specific context graph applications. Pick your industry domain, pick your agent framework, and get a complete full-stack app in under 5 minutes.

```bash
# Python
uvx create-context-graph

# Node.js
npx create-context-graph

# Non-interactive
uvx create-context-graph my-app --domain healthcare --framework pydanticai --demo-data
```

## What It Does

Create Context Graph walks you through an interactive wizard and generates a complete project:

- **FastAPI backend** with an AI agent configured for your domain, powered by [neo4j-agent-memory](https://github.com/neo4j-labs/neo4j-agent-memory) for multi-turn conversations
- **Next.js + Chakra UI v3 frontend** with markdown-rendered chat, tool call visualization, interactive graph visualization (schema view, double-click expand, drag/zoom, property panel), entity detail panel, document browser, and decision trace viewer
- **Neo4j schema** with domain-specific constraints, indexes, and GDS projections
- **Rich demo data** — LLM-generated entities, relationships, professional documents (discharge summaries, trade confirmations, lab reports), and multi-step decision traces
- **SaaS data import** — connect GitHub, Slack, Gmail, Jira, Notion, Google Calendar, or Salesforce
- **Custom domains** — describe your domain in plain English and the LLM generates a complete ontology
- **Domain-specific agent tools** with Cypher queries tailored to your industry

```
  Creating context graph application...

  Domain:     Wildlife Management
  Framework:  PydanticAI
  Data:       Demo (synthetic)
  Neo4j:      Docker (neo4j://localhost:7687)

  [1/6] Generating domain ontology...          ✓
  [2/6] Creating project scaffold...           ✓
  [3/6] Configuring agent tools & system prompt...  ✓
  [4/6] Generating synthetic documents (25 docs)... ✓
  [5/6] Writing fixture data...                ✓
  [6/6] Bundling project...                    ✓

  Done! Your context graph app is ready.

  cd my-app
  make install && make start
```

## Quick Start

### Prerequisites

- Python 3.11+ (with [uv](https://docs.astral.sh/uv/) recommended)
- Node.js 18+ (for the frontend)
- Neo4j 5+ (Docker, Aura, or local install)

### 1. Create a project

```bash
uvx create-context-graph
```

The interactive wizard will guide you through selecting a domain, framework, and Neo4j connection.

Or skip the wizard with flags:

```bash
uvx create-context-graph my-app \
  --domain financial-services \
  --framework pydanticai \
  --demo-data

# Custom domain from description
uvx create-context-graph my-app \
  --custom-domain "veterinary clinic management" \
  --framework pydanticai \
  --anthropic-api-key $ANTHROPIC_API_KEY \
  --demo-data

# Import from SaaS services
uvx create-context-graph my-app \
  --domain personal-knowledge \
  --framework pydanticai \
  --connector github \
  --connector slack
```

### 2. Start the app

The wizard offers four Neo4j connection options:

| Option | Command | Description |
|--------|---------|-------------|
| **Neo4j Aura** (cloud) | *(no start needed)* | Free cloud database — import your `.env` from [console.neo4j.io](https://console.neo4j.io) |
| **neo4j-local** | `make neo4j-start` | Lightweight local Neo4j, no Docker required (needs Node.js) |
| **Docker** | `make docker-up` | Full Neo4j via Docker Compose |
| **Existing** | *(no start needed)* | Connect to any running Neo4j instance |

```bash
cd my-app
make install       # Install backend + frontend dependencies
make neo4j-start   # Start Neo4j (if using neo4j-local)
# OR: make docker-up  # Start Neo4j (if using Docker)
make seed          # Seed sample data into Neo4j
make start         # Start backend (port 8000) + frontend (port 3000)
```

### 3. Explore

- **Frontend:** http://localhost:3000 — Chat with the AI agent, explore the knowledge graph
- **Backend API:** http://localhost:8000/docs — FastAPI auto-generated docs
- **Neo4j Browser:** http://localhost:7474 — Query the graph directly

## Supported Domains

22 industry domains, each with a purpose-built ontology, sample data, agent tools, and demo scenarios:

| Domain | Key Entities | Domain | Key Entities |
|--------|-------------|--------|-------------|
| Financial Services | Account, Transaction, Decision, Policy | Real Estate | Property, Listing, Agent, Inspection |
| Healthcare | Patient, Provider, Diagnosis, Treatment | Vacation & Hospitality | Resort, Booking, Guest, Activity |
| Retail & E-Commerce | Customer, Product, Order, Review | Oil & Gas | Well, Reservoir, Equipment, Permit |
| Manufacturing | Machine, Part, WorkOrder, Supplier | Data Journalism | Source, Story, Claim, Investigation |
| Scientific Research | Researcher, Paper, Dataset, Grant | Trip Planning | Destination, Hotel, Activity, Itinerary |
| GenAI / LLM Ops | Model, Experiment, Prompt, Evaluation | GIS & Cartography | Feature, Layer, Survey, Boundary |
| Agent Memory | Agent, Conversation, Memory, ToolCall | Wildlife Management | Species, Sighting, Habitat, Camera |
| Gaming | Player, Character, Quest, Guild | Conservation | Site, Species, Program, Funding |
| Personal Knowledge | Note, Contact, Project, Topic | Golf & Sports Mgmt | Course, Player, Round, Tournament |
| Digital Twin | Asset, Sensor, Reading, Alert | Software Engineering | Repository, Issue, PR, Deployment |
| Product Management | Feature, Epic, UserPersona, Metric | Hospitality | Hotel, Room, Reservation, Service |

```bash
# List all available domains
create-context-graph --list-domains
```

**Custom domains:** Don't see your industry? Select "Custom (describe your domain)" in the wizard or use `--custom-domain "your description"`. The LLM generates a complete ontology with entity types, relationships, agent tools, and more.

## SaaS Data Connectors

Import real data from your existing tools instead of (or in addition to) synthetic demo data:

| Service | What's Imported | Auth |
|---------|----------------|------|
| **GitHub** | Issues, PRs, commits, contributors | Personal access token |
| **Notion** | Pages, databases, users | Integration token |
| **Jira** | Issues, sprints, users | API token |
| **Slack** | Channel messages, threads, users | Bot OAuth token |
| **Gmail** | Emails (last 30 days) | Google Workspace CLI or OAuth2 |
| **Google Calendar** | Events, attendees (last 90 days) | Google Workspace CLI or OAuth2 |
| **Salesforce** | Accounts, contacts, opportunities | Username/password |

Connectors run at scaffold time to populate initial data. They're also generated into your project so you can re-import with `make import`:

```bash
cd my-app
make import            # Re-import from connected services
make import-and-seed   # Import and seed into Neo4j
```

## Agent Frameworks

Select your preferred agent framework at project creation time:

| Framework | Description |
|-----------|-------------|
| **PydanticAI** | Structured tool definitions with Pydantic models and `RunContext` |
| **Claude Agent SDK** | Anthropic tool-use with agentic loop |
| **OpenAI Agents SDK** | `@function_tool` decorators with `Runner.run()` |
| **LangGraph** | Stateful graph-based agent workflow with `create_react_agent()` |
| **CrewAI** | Multi-agent crew with role-based tools |
| **Strands (AWS)** | Tool-use agents with AWS Bedrock |
| **Google ADK** | Gemini agents with `FunctionTool` calling |
| **Anthropic Tools** | Modular tool registry with Anthropic API agentic loop |

All frameworks share the same FastAPI HTTP layer, Neo4j client, and frontend. Only the agent implementation differs.

## Generated Project Structure

```
my-app/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── agent.py               # AI agent (framework-specific)
│   │   ├── config.py              # Settings from .env
│   │   ├── routes.py              # REST API endpoints
│   │   ├── models.py              # Pydantic models (from ontology)
│   │   ├── context_graph_client.py # Neo4j CRUD operations
│   │   ├── gds_client.py          # Graph Data Science algorithms
│   │   ├── vector_client.py       # Vector search
│   │   └── connectors/            # SaaS connectors (if selected)
│   ├── scripts/
│   │   ├── generate_data.py       # Data seeding script
│   │   └── import_data.py         # SaaS import script (if connectors selected)
│   └── pyproject.toml
├── frontend/
│   ├── app/                       # Next.js pages
│   ├── components/
│   │   ├── ChatInterface.tsx      # AI chat with demo scenarios + graph data flow
│   │   ├── ContextGraphView.tsx   # Interactive NVL graph (schema view, expand, drag/zoom, properties)
│   │   ├── DecisionTracePanel.tsx  # Reasoning trace viewer with step details
│   │   ├── DocumentBrowser.tsx    # Document browser with template filtering
│   │   └── Provider.tsx           # Chakra UI v3 provider
│   ├── lib/config.ts              # Domain configuration
│   ├── theme/index.ts             # Chakra theme with domain colors
│   └── package.json
├── cypher/
│   ├── schema.cypher              # Constraints & indexes
│   └── gds_projections.cypher     # GDS algorithm config
├── data/
│   ├── ontology.yaml              # Domain ontology definition
│   └── fixtures.json              # Pre-generated sample data
├── .env                           # Neo4j + API key configuration
├── .env.example                   # Configuration template (tracked in git)
├── docker-compose.yml             # Local Neo4j instance (Docker mode only)
├── Makefile                       # start, seed, reset, install, test, lint
└── README.md                      # Domain-specific documentation
```

## CLI Reference

```bash
create-context-graph [PROJECT_NAME] [OPTIONS]

Arguments:
  PROJECT_NAME              Project name (optional, prompted if missing)

Options:
  --domain TEXT             Domain ID (e.g., healthcare, gaming)
  --framework TEXT          Agent framework (pydanticai, claude-agent-sdk, openai-agents, langgraph, crewai, strands, google-adk, anthropic-tools)
  --demo-data               Generate synthetic demo data
  --custom-domain TEXT      Generate custom domain from description (requires --anthropic-api-key)
  --connector TEXT          SaaS connector to enable; repeatable (github, slack, jira, notion, gmail, gcal, salesforce)
  --ingest                  Ingest data into Neo4j after generation
  --neo4j-uri TEXT          Neo4j connection URI [env: NEO4J_URI]
  --neo4j-username TEXT     Neo4j username [env: NEO4J_USERNAME]
  --neo4j-password TEXT     Neo4j password [env: NEO4J_PASSWORD]
  --neo4j-aura-env PATH    Path to Neo4j Aura .env file with credentials
  --neo4j-local             Use @johnymontana/neo4j-local for local Neo4j (no Docker)
  --anthropic-api-key TEXT  Anthropic API key for LLM generation [env: ANTHROPIC_API_KEY]
  --output-dir PATH         Output directory (default: ./<project-name>)
  --list-domains            List available domains and exit
  --version                 Show version and exit
  --help                    Show help and exit
```

## Context Graph Architecture

Every generated app demonstrates the three-memory-type architecture from [neo4j-agent-memory](https://github.com/neo4j-labs/neo4j-agent-memory):

- **Short-term memory** — Conversation history and document content stored as messages
- **Long-term memory** — Entity knowledge graph built on the POLE+O model (Person, Organization, Location, Event, Object)
- **Reasoning memory** — Decision traces with full provenance: thought chains, tool calls, causal relationships

This is what makes context graphs different from simple RAG — the agent doesn't just retrieve text, it reasons over a structured knowledge graph with full decision traceability.

## Development

```bash
# Clone and install
git clone https://github.com/neo4j-labs/create-context-graph.git
cd create-context-graph
uv venv && uv pip install -e ".[dev]"

# Run tests (512 tests, no Neo4j or API keys required)
source .venv/bin/activate
pytest tests/ -v               # Fast: 314 tests
pytest tests/ -v --slow        # Full: 512 tests (includes 176-combo domain x framework matrix + 22 perf tests)

# Test a specific scaffold
create-context-graph /tmp/test-app --domain software-engineering --framework pydanticai --demo-data
```

## Publishing

### PyPI (Python)

```bash
# Build
uv build

# Publish (requires PyPI account + API token)
uv publish
# Or: twine upload dist/*
```

After publishing, users can install with:
```bash
uvx create-context-graph       # Ephemeral (recommended)
pip install create-context-graph   # Permanent install
```

### npm (Node.js wrapper)

```bash
cd npm-wrapper

# Publish (requires npm account + auth)
npm publish --access public
```

After publishing, users can run with:
```bash
npx create-context-graph
```

The npm package is a thin wrapper that delegates to the Python CLI via `uvx`, `pipx`, or `python3 -m`. It requires Python 3.11+ to be installed.

### Automated Publishing (GitHub Actions)

Both packages are published automatically when you push a version tag:

```bash
# 1. Update version in pyproject.toml and npm-wrapper/package.json
# 2. Commit the version bump
# 3. Tag and push
git tag v0.1.0
git push origin v0.1.0
```

This triggers two GitHub Actions workflows:
- **publish-pypi.yml** — Builds and publishes to PyPI (uses trusted publishing / OIDC)
- **publish-npm.yml** — Publishes the npm wrapper to npmjs.com

**Setup required:**
- **PyPI:** Configure [trusted publishing](https://docs.pypi.org/trusted-publishers/) for this repo, or set a `PYPI_API_TOKEN` secret
- **npm:** Set an `NPM_TOKEN` secret in the repository settings

### Version Bumping

Both packages must use the same version. Update in two places:

1. `pyproject.toml` → `version = "X.Y.Z"`
2. `npm-wrapper/package.json` → `"version": "X.Y.Z"`

## License

Apache-2.0
