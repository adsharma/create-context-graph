"""Data ingestion pipeline via neo4j-agent-memory.

Ingests generated fixture data into Neo4j through the MemoryClient,
demonstrating all three memory types:
- Long-term: Entity knowledge graph (POLE+O)
- Short-term: Document storage as conversation messages
- Reasoning: Decision traces with provenance
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from create_context_graph.ontology import DomainOntology, generate_cypher_schema

console = Console()


async def _ingest_with_memory_client(
    fixture_data: dict,
    ontology: DomainOntology,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
) -> None:
    """Ingest data using neo4j-agent-memory MemoryClient."""
    from pydantic import SecretStr
    from neo4j_agent_memory import MemoryClient, MemorySettings

    settings = MemorySettings(
        neo4j={
            "uri": neo4j_uri,
            "username": neo4j_username,
            "password": SecretStr(neo4j_password),
        }
    )

    async with MemoryClient(settings) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Step 1: Apply schema
            task = progress.add_task("[1/4] Applying schema...", total=None)
            cypher_schema = generate_cypher_schema(ontology)
            for statement in cypher_schema.split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("//"):
                    try:
                        await client.graph.execute_write(stmt)
                    except Exception:
                        pass  # Constraints may already exist
            progress.update(task, description="[1/4] Schema applied")

            # Step 2: Ingest entities (Long-term memory)
            task = progress.add_task("[2/4] Ingesting entities...", total=None)
            entity_count = 0
            entities = fixture_data.get("entities", {})
            for label, items in entities.items():
                # Map label to POLE+O type
                pole_type = _get_pole_type(label, ontology)
                for item in items:
                    name = item.get("name", f"{label}-{entity_count}")
                    try:
                        await client.long_term.add_entity(
                            name=name,
                            entity_type=pole_type,
                            description=item.get("description", f"{label}: {name}"),
                            attributes=item,
                        )
                        entity_count += 1
                    except Exception as e:
                        console.print(f"  [yellow]Warning:[/yellow] Entity {name}: {e}")
            progress.update(task, description=f"[2/4] Ingested {entity_count} entities")

            # Step 2b: Create relationships
            relationships = fixture_data.get("relationships", [])
            rel_count = 0
            for rel in relationships:
                try:
                    # Use direct Cypher for relationship creation
                    cypher = f"""
                    MATCH (a {{name: $source_name}})
                    MATCH (b {{name: $target_name}})
                    MERGE (a)-[r:{rel['type']}]->(b)
                    RETURN type(r)
                    """
                    await client.graph.execute_write(
                        cypher,
                        {
                            "source_name": rel["source_name"],
                            "target_name": rel["target_name"],
                        },
                    )
                    rel_count += 1
                except Exception:
                    pass
            console.print(f"  Created {rel_count} relationships")

            # Step 3: Ingest documents (Short-term memory)
            task = progress.add_task("[3/4] Ingesting documents...", total=None)
            doc_count = 0
            documents = fixture_data.get("documents", [])
            session_id = f"demo-{ontology.domain.id}"
            for doc in documents:
                try:
                    await client.short_term.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=doc["content"],
                        metadata={
                            "document_type": doc.get("template_id", "unknown"),
                            "title": doc.get("title", ""),
                            "domain": ontology.domain.id,
                        },
                    )
                    doc_count += 1
                except Exception as e:
                    console.print(f"  [yellow]Warning:[/yellow] Document: {e}")
            progress.update(task, description=f"[3/4] Ingested {doc_count} documents")

            # Step 4: Ingest decision traces (Reasoning memory)
            task = progress.add_task("[4/4] Ingesting decision traces...", total=None)
            trace_count = 0
            traces = fixture_data.get("traces", [])
            for trace_data in traces:
                try:
                    trace = await client.reasoning.start_trace(
                        session_id=session_id,
                        task=trace_data["task"],
                    )
                    for i, step in enumerate(trace_data.get("steps", [])):
                        await client.reasoning.add_step(
                            trace_id=trace.id,
                            step_number=i + 1,
                            thought=step.get("thought", ""),
                            action=step.get("action", ""),
                            observation=step.get("observation", ""),
                        )
                    await client.reasoning.complete_trace(
                        trace_id=trace.id,
                        outcome=trace_data.get("outcome", "Completed"),
                        success=True,
                    )
                    trace_count += 1
                except Exception as e:
                    console.print(f"  [yellow]Warning:[/yellow] Trace: {e}")
            progress.update(task, description=f"[4/4] Ingested {trace_count} decision traces")

    console.print(
        f"\n  [green]Ingestion complete:[/green] {entity_count} entities, "
        f"{rel_count} relationships, {doc_count} documents, {trace_count} traces"
    )


async def _ingest_with_driver(
    fixture_data: dict,
    ontology: DomainOntology,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
) -> None:
    """Fallback: ingest using neo4j driver directly (no neo4j-agent-memory)."""
    from neo4j import AsyncGraphDatabase

    driver = AsyncGraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_username, neo4j_password),
    )

    try:
        await driver.verify_connectivity()
    except Exception as e:
        console.print(f"  [red]Cannot connect to Neo4j:[/red] {e}")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Apply schema
        task = progress.add_task("[1/3] Applying schema...", total=None)
        cypher_schema = generate_cypher_schema(ontology)
        async with driver.session() as session:
            for statement in cypher_schema.split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("//"):
                    try:
                        await session.run(stmt)
                    except Exception:
                        pass
        progress.update(task, description="[1/3] Schema applied")

        # Create entities
        task = progress.add_task("[2/3] Creating entities...", total=None)
        entity_count = 0
        entities = fixture_data.get("entities", {})
        async with driver.session() as session:
            for label, items in entities.items():
                for item in items:
                    props = ", ".join(f"{k}: ${k}" for k in item.keys())
                    cypher = f"MERGE (n:{label} {{{props}}})"
                    try:
                        await session.run(cypher, item)
                        entity_count += 1
                    except Exception:
                        pass
        progress.update(task, description=f"[2/3] Created {entity_count} entities")

        # Create relationships
        task = progress.add_task("[3/3] Creating relationships...", total=None)
        rel_count = 0
        relationships = fixture_data.get("relationships", [])
        async with driver.session() as session:
            for rel in relationships:
                cypher = f"""
                MATCH (a:{rel['source_label']} {{name: $source_name}})
                MATCH (b:{rel['target_label']} {{name: $target_name}})
                MERGE (a)-[r:{rel['type']}]->(b)
                """
                try:
                    await session.run(cypher, {
                        "source_name": rel["source_name"],
                        "target_name": rel["target_name"],
                    })
                    rel_count += 1
                except Exception:
                    pass
        progress.update(task, description=f"[3/3] Created {rel_count} relationships")

    await driver.close()
    console.print(
        f"\n  [green]Ingestion complete:[/green] {entity_count} entities, {rel_count} relationships"
    )


def _get_pole_type(label: str, ontology: DomainOntology) -> str:
    """Map an entity label to its POLE+O type."""
    for et in ontology.entity_types:
        if et.label == label:
            return et.pole_type
    return "OBJECT"


def ingest_data(
    fixture_path: Path,
    ontology: DomainOntology,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
) -> None:
    """Ingest fixture data into Neo4j.

    Tries neo4j-agent-memory first, falls back to direct driver.
    """
    if not fixture_path.exists():
        console.print(f"[red]Fixture file not found:[/red] {fixture_path}")
        return

    fixture_data = json.loads(fixture_path.read_text())

    console.print(f"\n  Ingesting {ontology.domain.name} data into Neo4j...")

    try:
        import neo4j_agent_memory  # noqa: F401
        asyncio.run(
            _ingest_with_memory_client(
                fixture_data, ontology,
                neo4j_uri, neo4j_username, neo4j_password,
            )
        )
    except ImportError:
        console.print("  [yellow]neo4j-agent-memory not installed, using direct driver[/yellow]")
        asyncio.run(
            _ingest_with_driver(
                fixture_data, ontology,
                neo4j_uri, neo4j_username, neo4j_password,
            )
        )
