"""CLI entry point for create-context-graph."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from create_context_graph.config import SUPPORTED_FRAMEWORKS, ProjectConfig
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
    type=click.Choice(SUPPORTED_FRAMEWORKS, case_sensitive=False),
    help="Agent framework to use",
)
@click.option("--demo-data", is_flag=True, help="Generate synthetic demo data")
@click.option("--ingest", is_flag=True, help="Ingest generated data into Neo4j")
@click.option("--neo4j-uri", envvar="NEO4J_URI", help="Neo4j connection URI")
@click.option("--neo4j-username", envvar="NEO4J_USERNAME", default="neo4j")
@click.option("--neo4j-password", envvar="NEO4J_PASSWORD", default="password")
@click.option("--anthropic-api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key for LLM generation")
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
    anthropic_api_key: str | None,
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

    # If all required args are provided, skip wizard
    if project_name and domain and framework:
        config = ProjectConfig(
            project_name=project_name,
            domain=domain,
            framework=framework,
            data_source="demo" if demo_data else "demo",
            neo4j_uri=neo4j_uri or "neo4j://localhost:7687",
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            neo4j_type="docker",
            anthropic_api_key=anthropic_api_key,
            generate_data=demo_data,
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
    console.print(f"  [bold]make seed[/bold]          # Seed sample data")
    console.print(f"  [bold]make start[/bold]         # Start backend + frontend")
    console.print()
    console.print(f"  Backend:  http://localhost:8000")
    console.print(f"  Frontend: http://localhost:3000")
    console.print()
