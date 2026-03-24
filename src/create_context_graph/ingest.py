# Copyright 2026 Neo4j Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data ingestion pipeline for LadybugDB.

Ingests generated fixture data into a LadybugDB embedded database.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from create_context_graph.ontology import DomainOntology, generate_cypher_schema

console = Console()


def _execute_statements(conn, schema_text: str) -> None:
    """Execute semicolon-delimited DDL statements, ignoring comments."""
    for statement in schema_text.split(";"):
        stmt = statement.strip()
        if stmt and not stmt.startswith("//"):
            try:
                conn.execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    console.print(f"  [yellow]Warning:[/yellow] Schema: {e}")


def ingest_data(
    fixture_path: Path,
    ontology: DomainOntology,
    db_path: str,
) -> None:
    """Ingest fixture data into LadybugDB."""
    if not fixture_path.exists():
        console.print(f"[red]Fixture file not found:[/red] {fixture_path}")
        return

    fixture_data = json.loads(fixture_path.read_text())

    console.print(f"\n  Ingesting {ontology.domain.name} data into LadybugDB at {db_path}...")

    try:
        import real_ladybug as lb
    except ImportError:
        console.print("  [red]real_ladybug not installed. Run: pip install real_ladybug[/red]")
        return

    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    db = lb.Database(db_path)
    conn = lb.Connection(db)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Step 1: Apply schema
        task = progress.add_task("[1/3] Applying schema...", total=None)
        cypher_schema = generate_cypher_schema(ontology)
        _execute_statements(conn, cypher_schema)
        progress.update(task, description="[1/3] Schema applied")

        # Step 2: Ingest entities
        task = progress.add_task("[2/3] Ingesting entities...", total=None)
        entity_count = 0
        entities = fixture_data.get("entities", {})
        for label, items in entities.items():
            for item in items:
                props = ", ".join(f"{k}: ${k}" for k in item.keys())
                cypher = f"CREATE (n:{label} {{{props}}})"
                try:
                    conn.execute(cypher, item)
                    entity_count += 1
                except Exception as e:
                    console.print(f"  [yellow]Warning:[/yellow] Entity {item.get('name', '?')}: {e}")
        progress.update(task, description=f"[2/3] Ingested {entity_count} entities")

        # Step 2b: Create relationships
        relationships = fixture_data.get("relationships", [])
        rel_count = 0
        for rel in relationships:
            cypher = (
                f"MATCH (a:{rel['source_label']}), (b:{rel['target_label']}) "
                f"WHERE a.name = $source_name AND b.name = $target_name "
                f"CREATE (a)-[:{rel['type']}]->(b)"
            )
            try:
                conn.execute(cypher, {
                    "source_name": rel["source_name"],
                    "target_name": rel["target_name"],
                })
                rel_count += 1
            except Exception as e:
                console.print(f"  [yellow]Warning:[/yellow] Relationship {rel.get('type', '?')}: {e}")
        console.print(f"  Created {rel_count} relationships")

        # Step 3: Ingest documents
        task = progress.add_task("[3/3] Ingesting documents...", total=None)
        doc_count = 0
        documents = fixture_data.get("documents", [])
        for doc in documents:
            try:
                conn.execute(
                    "CREATE (d:Document {title: $title, content: $content, "
                    "template_id: $template_id, template_name: $template_name})",
                    {
                        "title": doc.get("title", ""),
                        "content": doc.get("content", ""),
                        "template_id": doc.get("template_id", ""),
                        "template_name": doc.get("template_name", ""),
                    },
                )
                doc_count += 1
            except Exception as e:
                console.print(f"  [yellow]Warning:[/yellow] Document: {e}")
        progress.update(task, description=f"[3/3] Ingested {doc_count} documents")

    console.print(
        f"\n  [green]Ingestion complete:[/green] {entity_count} entities, "
        f"{rel_count} relationships, {doc_count} documents"
    )
