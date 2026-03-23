---
sidebar_position: 1
title: CLI Options & Flags
---

# CLI Options & Flags

Complete reference for the `create-context-graph` command-line interface.

## Command Signature

```
create-context-graph [PROJECT_NAME] [OPTIONS]
```

`PROJECT_NAME` is optional. If omitted (and required options are not provided), the interactive wizard launches and prompts for it.

## Options

| Option | Type | Env Variable | Default | Description |
|--------|------|-------------|---------|-------------|
| `--domain` | `string` | -- | *(wizard prompt)* | Domain ID (e.g., `financial-services`, `healthcare`, `software-engineering`). Use `--list-domains` to see all available IDs. |
| `--framework` | `choice` | -- | *(wizard prompt)* | Agent framework to use. One of: `pydanticai`, `claude-agent-sdk`, `strands`, `google-adk`, `openai-agents`, `langgraph`, `crewai`, `anthropic-tools`. |
| `--demo-data` | `flag` | -- | `false` | Generate synthetic demo data and write it to `data/fixtures.json` in the output project. Uses static placeholder data by default; pass `--anthropic-api-key` for LLM-generated realistic data. |
| `--custom-domain` | `string` | -- | -- | Natural language description of a custom domain (e.g., `"veterinary clinic management"`). Requires `--anthropic-api-key`. Generates a full ontology YAML from the description. |
| `--connector` | `string` (repeatable) | -- | -- | SaaS connector to enable. Can be specified multiple times. Supported values: `github`, `slack`, `jira`, `notion`, `gmail`, `gcal`, `salesforce`. |
| `--ingest` | `flag` | -- | `false` | Ingest generated data into Neo4j after scaffolding. Requires a running Neo4j instance. |
| `--neo4j-uri` | `string` | `NEO4J_URI` | `neo4j://localhost:7687` | Neo4j Bolt connection URI. |
| `--neo4j-username` | `string` | `NEO4J_USERNAME` | `neo4j` | Neo4j authentication username. |
| `--neo4j-password` | `string` | `NEO4J_PASSWORD` | `password` | Neo4j authentication password. |
| `--neo4j-aura-env` | `path` | -- | -- | Path to a Neo4j Aura `.env` file with `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD`. Automatically sets `neo4j_type` to `aura`. |
| `--neo4j-local` | `flag` | -- | `false` | Use `@johnymontana/neo4j-local` for a lightweight local Neo4j instance (no Docker required, needs Node.js). Sets `neo4j_type` to `local`. |
| `--anthropic-api-key` | `string` | `ANTHROPIC_API_KEY` | -- | Anthropic API key. Enables LLM-powered data generation (realistic entity names, documents, decision traces) and custom domain generation. |
| `--output-dir` | `path` | -- | `./<project-slug>` | Directory where the generated project is written. Defaults to a kebab-case slug of the project name in the current working directory. |
| `--list-domains` | `flag` | -- | -- | Print all available domain IDs and names, then exit. |
| `--version` | `flag` | -- | -- | Print the installed version and exit. |
| `--help` | `flag` | -- | -- | Show the help message and exit. |

## Interactive vs. Non-Interactive Mode

The CLI operates in two modes:

- **Interactive mode:** If `PROJECT_NAME`, `--domain`, or `--framework` is missing, the 7-step interactive wizard launches. The wizard uses [Questionary](https://questionary.readthedocs.io/) prompts to collect all configuration.
- **Non-interactive mode:** If `PROJECT_NAME`, `--domain` (or `--custom-domain`), and `--framework` are all provided, the wizard is skipped entirely. This mode is suitable for CI/CD pipelines and scripting.

## Examples

### Interactive wizard

Launch the wizard, which prompts for project name, domain, framework, data source, and Neo4j configuration:

```bash
create-context-graph
```

### Fully non-interactive

Generate a financial services app with PydanticAI and demo data, no prompts:

```bash
create-context-graph my-fintech-app \
  --domain financial-services \
  --framework pydanticai \
  --demo-data
```

### LLM-powered data generation

Generate realistic synthetic data using the Anthropic API:

```bash
create-context-graph healthcare-app \
  --domain healthcare \
  --framework claude-agent-sdk \
  --demo-data \
  --anthropic-api-key sk-ant-...
```

Or using the environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
create-context-graph healthcare-app \
  --domain healthcare \
  --framework claude-agent-sdk \
  --demo-data
```

### Custom domain from natural language

Describe your domain in plain English and let the LLM generate the ontology:

```bash
create-context-graph vet-clinic \
  --custom-domain "veterinary clinic managing patients, owners, appointments, and treatments" \
  --framework pydanticai \
  --demo-data \
  --anthropic-api-key sk-ant-...
```

### With SaaS connectors

Enable GitHub and Slack data import:

```bash
create-context-graph dev-team-graph \
  --domain software-engineering \
  --framework langgraph \
  --connector github \
  --connector slack
```

### Scaffold and ingest into Neo4j

Generate the project, create demo data, and load it into a running Neo4j instance:

```bash
create-context-graph my-app \
  --domain supply-chain \
  --framework openai-agents \
  --demo-data \
  --ingest \
  --neo4j-uri neo4j://localhost:7687 \
  --neo4j-password my-secret
```

### Custom output directory

Write the generated project to a specific path:

```bash
create-context-graph my-app \
  --domain healthcare \
  --framework crewai \
  --output-dir /tmp/projects/healthcare-demo
```

### List all available domains

```bash
create-context-graph --list-domains
```

### Using uvx (no install required)

```bash
uvx create-context-graph my-app --domain healthcare --framework pydanticai --demo-data
```

## Environment Variables

The following environment variables are read as defaults for their corresponding CLI options:

| Variable | CLI Option |
|----------|-----------|
| `NEO4J_URI` | `--neo4j-uri` |
| `NEO4J_USERNAME` | `--neo4j-username` |
| `NEO4J_PASSWORD` | `--neo4j-password` |
| `ANTHROPIC_API_KEY` | `--anthropic-api-key` |

CLI flags always take precedence over environment variables.
