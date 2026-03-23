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

"""CLI entry point for create-context-graph."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from create_context_graph.config import SUPPORTED_FRAMEWORKS, FRAMEWORK_ALIASES, ProjectConfig
from create_context_graph.ontology import list_available_domains, load_domain
from create_context_graph.renderer import ProjectRenderer

console = Console()


@click.command()
@click.argument("project_name", required=False)
@click.option(
    "--domain",
    type=str,
    help="Domain ID (e.g., financial-services, healthcare, software-engineering)",
)
@click.option(
    "--framework",
    type=click.Choice(SUPPORTED_FRAMEWORKS + list(FRAMEWORK_ALIASES.keys()), case_sensitive=False),
    help="Agent framework to use",
)
@click.option("--demo-data", is_flag=True, help="Generate synthetic demo data")
@click.option("--ingest", is_flag=True, help="Ingest generated data into Neo4j")
@click.option("--neo4j-uri", envvar="NEO4J_URI", help="Neo4j connection URI")
@click.option("--neo4j-username", envvar="NEO4J_USERNAME", default="neo4j")
@click.option("--neo4j-password", envvar="NEO4J_PASSWORD", default="password")
@click.option("--neo4j-aura-env", type=click.Path(exists=True), help="Path to Neo4j Aura .env file with credentials")
@click.option("--neo4j-local", is_flag=True, help="Use @johnymontana/neo4j-local for local Neo4j (no Docker)")
@click.option("--anthropic-api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key for LLM generation")
@click.option("--custom-domain", type=str, help="Natural language description for custom domain generation (requires --anthropic-api-key)")
@click.option("--connector", multiple=True, help="SaaS connector to enable (github, slack, jira, notion, gmail, gcal, salesforce)")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: ./<project-name>)")
@click.option("--list-domains", is_flag=True, help="List available domains and exit")
@click.version_option(package_name="create-context-graph")
def main(
    project_name: str | None,
    domain: str | None,
    framework: str | None,
    demo_data: bool,
    ingest: bool,
    neo4j_uri: str | None,
    neo4j_username: str,
    neo4j_password: str,
    neo4j_aura_env: str | None,
    neo4j_local: bool,
    anthropic_api_key: str | None,
    custom_domain: str | None,
    connector: tuple[str, ...],
    output_dir: str | None,
    list_domains: bool,
) -> None:
    """Create a domain-specific context graph application.

    Generates a full-stack application with a FastAPI backend,
    Next.js frontend, Neo4j knowledge graph, and AI agent—
    all customized for your industry domain.
    """
    # List domains mode
    if list_domains:
        domains = list_available_domains()
        console.print("\n[bold]Available domains:[/bold]\n")
        for d in domains:
            console.print(f"  {d['id']:30s} {d['name']}")
        console.print()
        return

    # Handle custom domain generation (non-interactive)
    custom_domain_yaml = None
    custom_ontology = None
    if custom_domain:
        if not anthropic_api_key:
            console.print("[red]Error:[/red] --anthropic-api-key is required for custom domain generation.")
            raise SystemExit(1)
        from create_context_graph.custom_domain import (
            display_ontology_summary,
            generate_custom_domain,
        )

        console.print("[bold]Generating custom domain ontology...[/bold]")
        try:
            custom_ontology, custom_domain_yaml = generate_custom_domain(
                custom_domain, anthropic_api_key
            )
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

        display_ontology_summary(custom_ontology, console)
        domain = custom_ontology.domain.id

    # Resolve deprecated framework aliases
    if framework:
        framework = FRAMEWORK_ALIASES.get(framework, framework)

    # Handle Neo4j Aura .env import
    if neo4j_aura_env:
        from create_context_graph.wizard import _parse_aura_env
        neo4j_uri, neo4j_username, neo4j_password = _parse_aura_env(neo4j_aura_env)

    # Determine neo4j_type from flags
    if neo4j_aura_env:
        neo4j_type_resolved = "aura"
    elif neo4j_local:
        neo4j_type_resolved = "local"
    elif neo4j_uri and "aura" in (neo4j_uri or ""):
        neo4j_type_resolved = "aura"
    else:
        neo4j_type_resolved = "docker"

    # If all required args are provided, skip wizard
    if project_name and (domain or custom_domain) and framework:
        config = ProjectConfig(
            project_name=project_name,
            domain=domain or "custom",
            framework=framework,
            data_source="saas" if connector else ("demo" if demo_data else "none"),
            neo4j_uri=neo4j_uri or "neo4j://localhost:7687",
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            neo4j_type=neo4j_type_resolved,
            anthropic_api_key=anthropic_api_key,
            generate_data=demo_data,
            custom_domain_yaml=custom_domain_yaml,
            saas_connectors=list(connector),
        )
    else:
        # Launch interactive wizard
        from create_context_graph.wizard import run_wizard

        config = run_wizard()

    # Resolve output directory
    out = Path(output_dir) if output_dir else Path.cwd() / config.project_slug
    if out.exists() and any(out.iterdir()):
        console.print(f"[red]Error:[/red] Directory {out} already exists and is not empty.")
        raise SystemExit(1)

    # Load domain ontology
    if custom_ontology:
        ontology = custom_ontology
    elif config.custom_domain_yaml:
        from create_context_graph.ontology import load_domain_from_yaml_string
        ontology = load_domain_from_yaml_string(config.custom_domain_yaml)
    else:
        try:
            ontology = load_domain(config.domain)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Domain '{config.domain}' not found.")
            available = list_available_domains()
            console.print("Available domains: " + ", ".join(d["id"] for d in available))
            raise SystemExit(1)

    # Generate project
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project scaffold...", total=None)

        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        progress.update(task, description="Project generated!")

    # Generate demo data if requested
    fixture_path = out / "data" / "fixtures.json"
    if config.generate_data or demo_data:
        console.print("\n[bold]Generating demo data...[/bold]")
        from create_context_graph.generator import generate_fixture_data

        generate_fixture_data(
            ontology,
            fixture_path,
            api_key=config.anthropic_api_key or anthropic_api_key,
        )

    # Import data from SaaS connectors if configured
    if config.saas_connectors:
        import json

        from create_context_graph.connectors import get_connector, merge_connector_results, NormalizedData

        console.print("\n[bold]Importing data from connected services...[/bold]")
        results: list[NormalizedData] = []
        for conn_id in config.saas_connectors:
            try:
                conn = get_connector(conn_id)
                creds = config.saas_credentials.get(conn_id, {})
                console.print(f"  Connecting to {conn.service_name}...")
                conn.authenticate(creds)
                console.print(f"  Fetching data from {conn.service_name}...")
                data = conn.fetch()
                results.append(data)
                entity_count = sum(len(v) for v in data.entities.values())
                console.print(f"  [green]✓[/green] {conn.service_name}: {entity_count} entities, {len(data.documents)} documents")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] {conn_id}: {e}")

        if results:
            merged = merge_connector_results(results)
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_text(json.dumps(merged.model_dump(), indent=2, default=str))
            console.print(f"\n[green]Imported data written to {fixture_path}[/green]")

    # Ingest into Neo4j if requested
    if ingest and fixture_path.exists():
        console.print("\n[bold]Ingesting data into Neo4j...[/bold]")
        from create_context_graph.ingest import ingest_data

        ingest_data(
            fixture_path,
            ontology,
            config.neo4j_uri,
            config.neo4j_username,
            config.neo4j_password,
        )

    # Success message
    console.print()
    console.print(f"[bold green]Done![/bold green] Your {ontology.domain.name} context graph app is ready.")
    console.print()
    try:
        display_path = out.relative_to(Path.cwd())
    except ValueError:
        display_path = out
    console.print(f"  [bold]cd {display_path}[/bold]")
    console.print(f"  [bold]make install[/bold]       # Install dependencies")
    if config.neo4j_type == "docker":
        console.print(f"  [bold]make docker-up[/bold]    # Start Neo4j")
    elif config.neo4j_type == "local":
        console.print(f"  [bold]make neo4j-start[/bold]  # Start Neo4j (requires Node.js)")
    console.print(f"  [bold]make seed[/bold]          # Seed sample data")
    if config.saas_connectors:
        console.print(f"  [bold]make import[/bold]         # Re-import from connected services")
    console.print(f"  [bold]make start[/bold]         # Start backend + frontend")
    console.print()
    console.print(f"  Backend:  http://localhost:8000")
    console.print(f"  Frontend: http://localhost:3000")
    console.print()
