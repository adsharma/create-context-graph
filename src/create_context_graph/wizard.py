"""Interactive CLI wizard using Questionary and Rich."""

from __future__ import annotations

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from create_context_graph.config import (
    FRAMEWORK_DISPLAY_NAMES,
    SUPPORTED_FRAMEWORKS,
    ProjectConfig,
)
from create_context_graph.ontology import list_available_domains

console = Console()


def _banner() -> None:
    console.print(
        Panel(
            "[bold cyan]Create Context Graph[/bold cyan]\n"
            "[dim]Interactive scaffolding for domain-specific context graph applications[/dim]",
            border_style="cyan",
        )
    )


def run_wizard() -> ProjectConfig:
    """Run the interactive wizard and return a ProjectConfig."""
    _banner()

    # Step 1: Project name
    project_name = questionary.text(
        "What is your project name?",
        default="my-context-graph",
    ).ask()
    if not project_name:
        raise SystemExit("Aborted.")

    # Step 2: Data source
    data_source = questionary.select(
        "How would you like to populate your context graph?",
        choices=[
            questionary.Choice("Generate demo data (synthetic documents & entities)", value="demo"),
            questionary.Choice("Connect to SaaS services (Gmail, Slack, Jira, etc.)", value="saas"),
        ],
    ).ask()
    if not data_source:
        raise SystemExit("Aborted.")

    # Step 3: Domain selection
    domains = list_available_domains()
    domain_choices = [
        questionary.Choice(d["name"], value=d["id"]) for d in domains
    ]
    domain_choices.append(questionary.Choice("Custom (describe your domain)", value="custom"))

    domain = questionary.select(
        "Select your industry domain:",
        choices=domain_choices,
    ).ask()
    if not domain:
        raise SystemExit("Aborted.")

    if domain == "custom":
        console.print("[yellow]Custom domain generation is not yet implemented. Please select a built-in domain.[/yellow]")
        raise SystemExit("Custom domains coming soon.")

    # Step 4: Agent framework
    framework_choices = [
        questionary.Choice(FRAMEWORK_DISPLAY_NAMES[fw], value=fw)
        for fw in SUPPORTED_FRAMEWORKS
    ]
    framework = questionary.select(
        "Select your agent framework:",
        choices=framework_choices,
    ).ask()
    if not framework:
        raise SystemExit("Aborted.")

    # Step 5: Neo4j connection
    neo4j_type = questionary.select(
        "How would you like to connect to Neo4j?",
        choices=[
            questionary.Choice("Neo4j AuraDS (recommended for GDS algorithms)", value="aurads"),
            questionary.Choice("Neo4j Aura Free Tier", value="aura-free"),
            questionary.Choice("Local Neo4j (Docker)", value="docker"),
            questionary.Choice("Existing Neo4j instance", value="existing"),
        ],
    ).ask()
    if not neo4j_type:
        raise SystemExit("Aborted.")

    if neo4j_type == "docker":
        neo4j_uri = "neo4j://localhost:7687"
        neo4j_username = "neo4j"
        neo4j_password = "password"
    else:
        neo4j_uri = questionary.text(
            "Neo4j URI:",
            default="neo4j+s://xxxx.databases.neo4j.io",
        ).ask()
        neo4j_username = questionary.text(
            "Neo4j Username:",
            default="neo4j",
        ).ask()
        neo4j_password = questionary.password("Neo4j Password:").ask()

    if not neo4j_uri:
        raise SystemExit("Aborted.")

    # Step 6: API Keys
    anthropic_api_key = questionary.password(
        "Anthropic API key (for AI agent):",
        default="",
    ).ask()

    openai_api_key = questionary.password(
        "OpenAI API key (for embeddings, or Enter to skip):",
        default="",
    ).ask()

    # Step 7: Confirmation
    config = ProjectConfig(
        project_name=project_name,
        domain=domain,
        framework=framework,
        data_source=data_source,
        neo4j_uri=neo4j_uri,
        neo4j_username=neo4j_username,
        neo4j_password=neo4j_password or "password",
        neo4j_type=neo4j_type,
        anthropic_api_key=anthropic_api_key or None,
        openai_api_key=openai_api_key or None,
        generate_data=data_source == "demo",
    )

    _show_summary(config)

    confirm = questionary.confirm("Proceed with these settings?", default=True).ask()
    if not confirm:
        raise SystemExit("Aborted.")

    return config


def _show_summary(config: ProjectConfig) -> None:
    """Display a summary table of the configuration."""
    table = Table(title="Project Configuration", show_header=False)
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Project", config.project_name)
    table.add_row("Domain", config.domain)
    table.add_row("Framework", config.framework_display_name)
    table.add_row("Data Source", config.data_source)
    table.add_row("Neo4j", f"{config.neo4j_type} ({config.neo4j_uri})")
    table.add_row("Anthropic Key", "***" if config.anthropic_api_key else "(not set)")
    table.add_row("OpenAI Key", "***" if config.openai_api_key else "(not set)")

    console.print()
    console.print(table)
    console.print()
