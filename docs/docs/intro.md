---
sidebar_position: 1
title: Introduction
---

# Create Context Graph

**Create Context Graph** is an interactive CLI scaffolding tool that generates complete, domain-specific context graph applications. Think of it as `create-next-app`, but for AI agents backed by graph memory.

Given a domain (like healthcare, financial services, or wildlife management) and an agent framework, it generates a full-stack application: a FastAPI backend with a configured AI agent, a Next.js + Chakra UI frontend with NVL graph visualization, a Neo4j schema with synthetic data, and domain-specific tools that let the agent query and reason over your knowledge graph.

## Key Features

- **22 built-in domains** -- healthcare, financial services, real estate, manufacturing, scientific research, software engineering, and more. Each domain ships with a complete ontology, agent tools, demo scenarios, and fixture data.
- **8 agent frameworks** -- PydanticAI, Claude Agent SDK, OpenAI Agents SDK, LangGraph, CrewAI, Strands, Google ADK, and Anthropic Tools. Pick the one you know, or try something new.
- **Multi-turn conversations** -- every generated agent uses [neo4j-agent-memory](https://github.com/neo4j-labs/neo4j-agent-memory) for conversation persistence. Session history is stored in Neo4j and retrieved on each turn, so follow-up questions work naturally.
- **Graph-native AI agents** -- every generated agent comes with Cypher-powered tools for querying entities, relationships, and decision traces in Neo4j. Tool call metadata is surfaced inline in the chat.
- **Interactive graph visualization** -- the frontend includes an NVL-powered graph explorer with entity detail panel (click any node to see all properties and connections), a document browser with template filtering, and a decision trace viewer. Agent tool call results flow to the graph automatically.
- **Rich demo data** -- each domain ships with LLM-generated fixture data: 80-90 entities with realistic names, 25+ professional documents (discharge summaries, trade confirmations, lab reports), and 3-5 multi-step decision traces. All loaded into Neo4j via `make seed` and browsable in the frontend.
- **Flexible Neo4j setup** -- connect to Neo4j Aura (free cloud tier with `.env` import), run locally with `@johnymontana/neo4j-local` (no Docker needed), use Docker Compose, or connect to any existing instance.
- **SaaS data import** -- connect Gmail, Slack, Jira, GitHub, Notion, and Salesforce to populate your graph with real data.
- **Custom domains** -- describe your domain and let the tool generate a complete ontology, or write your own YAML definition from scratch.

## Quick Install

No installation required. Run directly with `uvx` (Python) or `npx` (Node.js):

```bash
# Python (recommended)
uvx create-context-graph

# Node.js
npx create-context-graph
```

## Quick Start (Non-Interactive)

Skip the wizard entirely by passing flags:

```bash
uvx create-context-graph my-app \
  --domain healthcare \
  --framework pydanticai \
  --demo-data
```

This creates a `my-app/` directory with a complete healthcare context graph application using PydanticAI as the agent framework, pre-loaded with demo data.

## See All Available Domains

```bash
uvx create-context-graph --list-domains
```

## What's Next

- **[Your First Context Graph App](./tutorials/first-context-graph-app)** -- step-by-step tutorial to create, run, and explore a generated application.
- **[Customizing Your Domain Ontology](./tutorials/customizing-domain-ontology)** -- learn how to modify entity types, relationships, and agent tools in your domain YAML.
