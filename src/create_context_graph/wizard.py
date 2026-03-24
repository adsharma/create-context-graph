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

    # Step 2b: SaaS connector selection (if SaaS data source)
    selected_connectors: list[str] = []
    saas_credentials: dict[str, dict[str, str]] = {}
    if data_source == "saas":
        from create_context_graph.connectors import list_connectors, get_connector
        from create_context_graph.connectors.oauth import check_gws_cli, install_gws_cli

        available = list_connectors()
        connector_choices = [
            questionary.Choice(f"{c['name']} — {c['description']}", value=c["id"])
            for c in available
        ]

        selected_connectors = questionary.checkbox(
            "Select services to connect:",
            choices=connector_choices,
        ).ask()
        if not selected_connectors:
            raise SystemExit("Aborted. Select at least one connector.")

        # Check for Google Workspace CLI for Gmail/GCal
        google_connectors = {"gmail", "gcal"}
        if google_connectors & set(selected_connectors):
            if not check_gws_cli():
                console.print("[yellow]Google Workspace CLI (gws) not found.[/yellow]")
                install = questionary.confirm(
                    "Install it via npm? (recommended for Gmail/Calendar)", default=True
                ).ask()
                if install:
                    with console.status("[bold cyan]Installing @googleworkspace/cli..."):
                        if install_gws_cli():
                            console.print("[green]Google Workspace CLI installed successfully.[/green]")
                        else:
                            console.print("[yellow]Installation failed. Will use Python OAuth2 fallback.[/yellow]")

        # Collect credentials for each connector
        for conn_id in selected_connectors:
            connector = get_connector(conn_id)
            prompts = connector.get_credential_prompts()
            if not prompts:
                continue  # e.g. gws handles auth itself

            console.print(f"\n[bold]{connector.service_name} credentials:[/bold]")
            creds: dict[str, str] = {}
            for p in prompts:
                if p.get("secret"):
                    value = questionary.password(p["prompt"]).ask()
                else:
                    value = questionary.text(p["prompt"]).ask()
                if not value:
                    raise SystemExit("Aborted.")
                creds[p["name"]] = value
            saas_credentials[conn_id] = creds

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

    custom_domain_yaml = None
    custom_ontology = None
    anthropic_api_key = None
    if domain == "custom":
        # Collect domain description
        domain_description = questionary.text(
            "Describe your domain (industry, key concepts, what the agent should help with):",
        ).ask()
        if not domain_description:
            raise SystemExit("Aborted.")

        # Need an API key for LLM generation
        custom_api_key = questionary.password(
            "Anthropic API key (required for custom domain generation):",
        ).ask()
        if not custom_api_key:
            console.print("[red]An API key is required for custom domain generation.[/red]")
            raise SystemExit("API key required.")

        # Generate the domain
        from create_context_graph.custom_domain import (
            display_ontology_summary,
            generate_custom_domain,
            save_custom_domain,
        )

        while True:
            with console.status("[bold cyan]Generating custom domain ontology..."):
                try:
                    custom_ontology, custom_domain_yaml = generate_custom_domain(
                        domain_description, custom_api_key
                    )
                except ValueError as e:
                    console.print(f"[red]Generation failed: {e}[/red]")
                    raise SystemExit("Custom domain generation failed.")

            display_ontology_summary(custom_ontology, console)

            action = questionary.select(
                "How would you like to proceed?",
                choices=[
                    questionary.Choice("Accept this ontology", value="accept"),
                    questionary.Choice("Regenerate with same description", value="regenerate"),
                    questionary.Choice("Edit description and regenerate", value="edit"),
                    questionary.Choice("Cancel", value="cancel"),
                ],
            ).ask()

            if action == "accept":
                break
            elif action == "regenerate":
                continue
            elif action == "edit":
                domain_description = questionary.text(
                    "Updated domain description:",
                    default=domain_description,
                ).ask()
                if not domain_description:
                    raise SystemExit("Aborted.")
                continue
            else:
                raise SystemExit("Aborted.")

        domain = custom_ontology.domain.id

        # Offer to save for future use
        save = questionary.confirm("Save this domain for future use?", default=True).ask()
        if save:
            save_custom_domain(custom_ontology, custom_domain_yaml)

        # Store the API key for later use
        anthropic_api_key = custom_api_key

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

    # Step 5: LadybugDB path
    ladybug_db_path = questionary.text(
        "LadybugDB database path:",
        default="./data/ladybug.db",
    ).ask()
    if not ladybug_db_path:
        raise SystemExit("Aborted.")

    # Step 6: API Keys (skip Anthropic if already collected for custom domain)
    if custom_domain_yaml is None:
        anthropic_api_key = questionary.password(
            "Anthropic API key (for AI agent):",
            default="",
        ).ask()
    # anthropic_api_key already set from custom domain flow otherwise

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
        ladybug_db_path=ladybug_db_path,
        anthropic_api_key=anthropic_api_key or None,
        openai_api_key=openai_api_key or None,
        generate_data=data_source == "demo",
        custom_domain_yaml=custom_domain_yaml,
        saas_connectors=selected_connectors,
        saas_credentials=saas_credentials,
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
    if config.saas_connectors:
        table.add_row("Connectors", ", ".join(config.saas_connectors))
    table.add_row("LadybugDB", config.ladybug_db_path)
    table.add_row("Anthropic Key", "***" if config.anthropic_api_key else "(not set)")
    table.add_row("OpenAI Key", "***" if config.openai_api_key else "(not set)")

    console.print()
    console.print(table)
    console.print()
