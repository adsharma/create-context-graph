# Create Context Graph

> **Neo4j Labs Project** — This is an experimental project under active development. APIs and features may change.

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

- **FastAPI backend** with an AI agent configured for your domain
- **Next.js + Chakra UI v3 frontend** with chat, graph visualization, and decision trace panels
- **Neo4j schema** with domain-specific constraints, indexes, and GDS projections
- **Synthetic demo data** — entities, relationships, documents, and decision traces
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
```

### 2. Start the app

```bash
cd my-app
make install       # Install backend + frontend dependencies
make docker-up     # Start Neo4j (if using Docker)
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
| **MAF** | Modular agent with pluggable tool registry |

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
│   │   └── vector_client.py       # Vector search
│   ├── scripts/generate_data.py   # Data seeding script
│   └── pyproject.toml
├── frontend/
│   ├── app/                       # Next.js pages
│   ├── components/
│   │   ├── ChatInterface.tsx      # AI chat with demo scenarios
│   │   ├── ContextGraphView.tsx   # Graph visualization (NVL)
│   │   ├── DecisionTracePanel.tsx  # Reasoning provenance viewer
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
├── docker-compose.yml             # Local Neo4j instance
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
  --framework TEXT          Agent framework (pydanticai, claude-agent-sdk, openai-agents, langgraph, crewai, strands, google-adk, maf)
  --demo-data               Generate synthetic demo data
  --ingest                  Ingest data into Neo4j after generation
  --neo4j-uri TEXT          Neo4j connection URI [env: NEO4J_URI]
  --neo4j-username TEXT     Neo4j username [env: NEO4J_USERNAME]
  --neo4j-password TEXT     Neo4j password [env: NEO4J_PASSWORD]
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

# Run tests (103 tests, no Neo4j or API keys required)
source .venv/bin/activate
pytest tests/ -v

# Test a specific scaffold
create-context-graph /tmp/test-app --domain software-engineering --framework pydanticai --demo-data
```

## License

Apache-2.0
