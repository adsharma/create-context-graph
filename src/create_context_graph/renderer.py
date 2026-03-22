"""Jinja2 template engine for project scaffolding."""

from __future__ import annotations

import re
import shutil
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from create_context_graph.config import ProjectConfig
from create_context_graph.ontology import (
    DomainOntology,
    generate_cypher_schema,
    generate_pydantic_models,
    generate_visualization_config,
)


# ---------------------------------------------------------------------------
# Custom Jinja2 filters
# ---------------------------------------------------------------------------


def _to_snake_case(value: str) -> str:
    s = re.sub(r"[\s\-]+", "_", value)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def _to_camel_case(value: str) -> str:
    parts = re.split(r"[\s_\-]+", value)
    return parts[0].lower() + "".join(p.title() for p in parts[1:])


def _to_pascal_case(value: str) -> str:
    parts = re.split(r"[\s_\-]+", value)
    return "".join(p.title() for p in parts)


def _to_kebab_case(value: str) -> str:
    return _to_snake_case(value).replace("_", "-")


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class ProjectRenderer:
    """Renders Jinja2 templates to produce a scaffolded project directory."""

    def __init__(self, config: ProjectConfig, ontology: DomainOntology):
        self.config = config
        self.ontology = ontology
        self.env = Environment(
            loader=PackageLoader("create_context_graph", "templates"),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        self.env.filters["snake_case"] = _to_snake_case
        self.env.filters["camel_case"] = _to_camel_case
        self.env.filters["pascal_case"] = _to_pascal_case
        self.env.filters["kebab_case"] = _to_kebab_case

    def _context(self) -> dict:
        """Build the template context dictionary."""
        return {
            "project": self.config.model_dump(),
            "project_name": self.config.project_name,
            "project_slug": self.config.project_slug,
            "domain": self.ontology.domain.model_dump(),
            "ontology": self.ontology.model_dump(),
            "entity_types": [et.model_dump() for et in self.ontology.entity_types],
            "relationships": [r.model_dump() for r in self.ontology.relationships],
            "demo_scenarios": [s.model_dump() for s in self.ontology.demo_scenarios],
            "agent_tools": [t.model_dump() for t in self.ontology.agent_tools],
            "framework": self.config.framework,
            "framework_display_name": self.config.framework_display_name,
            "framework_deps": self.config.framework_deps,
            "neo4j_uri": self.config.neo4j_uri,
            "neo4j_username": self.config.neo4j_username,
            "neo4j_password": self.config.neo4j_password,
            "neo4j_type": self.config.neo4j_type,
            "anthropic_api_key": self.config.anthropic_api_key or "",
            "openai_api_key": self.config.openai_api_key or "",
            "system_prompt": self.ontology.system_prompt,
            "cypher_schema": generate_cypher_schema(self.ontology),
            "pydantic_models": generate_pydantic_models(self.ontology),
            "visualization": generate_visualization_config(self.ontology),
        }

    def _render_template(self, template_name: str, output_path: Path, ctx: dict) -> None:
        """Render a single template to the output path."""
        template = self.env.get_template(template_name)
        content = template.render(**ctx)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

    def render(self, output_dir: Path) -> None:
        """Render the complete project to output_dir."""
        output_dir.mkdir(parents=True, exist_ok=True)
        ctx = self._context()

        self._render_base(output_dir, ctx)
        self._render_backend(output_dir / "backend", ctx)
        self._render_frontend(output_dir / "frontend", ctx)
        self._render_cypher(output_dir / "cypher", ctx)
        self._render_data(output_dir / "data", ctx)

    def _render_base(self, output_dir: Path, ctx: dict) -> None:
        """Render root-level project files."""
        base_templates = {
            "base/dot_env.j2": ".env",
            "base/Makefile.j2": "Makefile",
            "base/README.md.j2": "README.md",
            "base/gitignore.j2": ".gitignore",
        }
        for template_name, output_name in base_templates.items():
            self._render_template(template_name, output_dir / output_name, ctx)

        # Docker compose only if docker selected
        if self.config.neo4j_type == "docker":
            self._render_template(
                "base/docker-compose.yml.j2",
                output_dir / "docker-compose.yml",
                ctx,
            )

    def _render_backend(self, backend_dir: Path, ctx: dict) -> None:
        """Render the FastAPI backend."""
        shared_templates = {
            "backend/shared/main.py.j2": "app/main.py",
            "backend/shared/config.py.j2": "app/config.py",
            "backend/shared/context_graph_client.py.j2": "app/context_graph_client.py",
            "backend/shared/gds_client.py.j2": "app/gds_client.py",
            "backend/shared/vector_client.py.j2": "app/vector_client.py",
            "backend/shared/models.py.j2": "app/models.py",
            "backend/shared/routes.py.j2": "app/routes.py",
            "backend/shared/pyproject.toml.j2": "pyproject.toml",
        }
        for template_name, output_name in shared_templates.items():
            self._render_template(template_name, backend_dir / output_name, ctx)

        # __init__.py for app package
        (backend_dir / "app").mkdir(parents=True, exist_ok=True)
        (backend_dir / "app" / "__init__.py").write_text("")

        # Framework-specific agent template
        fw_key = self.config.framework.replace("-", "_")
        agent_template = f"backend/agents/{fw_key}/agent.py.j2"
        try:
            self._render_template(agent_template, backend_dir / "app" / "agent.py", ctx)
        except Exception:
            # Fallback: render a minimal agent stub
            self._render_template(
                "backend/shared/agent_stub.py.j2",
                backend_dir / "app" / "agent.py",
                ctx,
            )

        # Data generation script
        self._render_template(
            "backend/shared/generate_data.py.j2",
            backend_dir / "scripts" / "generate_data.py",
            ctx,
        )

    def _render_frontend(self, frontend_dir: Path, ctx: dict) -> None:
        """Render the Next.js + Chakra UI v3 + NVL frontend."""
        templates = {
            "frontend/package.json.j2": "package.json",
            "frontend/next.config.ts.j2": "next.config.ts",
            "frontend/tsconfig.json.j2": "tsconfig.json",
            "frontend/app/layout.tsx.j2": "app/layout.tsx",
            "frontend/app/page.tsx.j2": "app/page.tsx",
            "frontend/app/globals.css.j2": "app/globals.css",
            "frontend/components/ChatInterface.tsx.j2": "components/ChatInterface.tsx",
            "frontend/components/ContextGraphView.tsx.j2": "components/ContextGraphView.tsx",
            "frontend/components/DecisionTracePanel.tsx.j2": "components/DecisionTracePanel.tsx",
            "frontend/components/Provider.tsx.j2": "components/Provider.tsx",
            "frontend/lib/config.ts.j2": "lib/config.ts",
            "frontend/theme/index.ts.j2": "theme/index.ts",
        }
        for template_name, output_name in templates.items():
            self._render_template(template_name, frontend_dir / output_name, ctx)

    def _render_cypher(self, cypher_dir: Path, ctx: dict) -> None:
        """Render Cypher schema files."""
        self._render_template("cypher/schema.cypher.j2", cypher_dir / "schema.cypher", ctx)
        self._render_template(
            "cypher/gds_projections.cypher.j2",
            cypher_dir / "gds_projections.cypher",
            ctx,
        )

    def _render_data(self, data_dir: Path, ctx: dict) -> None:
        """Copy ontology and create data directory structure."""
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "documents").mkdir(exist_ok=True)

        # Copy the domain ontology YAML
        from create_context_graph.ontology import _get_domains_path

        domain_yaml = _get_domains_path() / f"{self.config.domain}.yaml"
        if domain_yaml.exists():
            shutil.copy2(domain_yaml, data_dir / "ontology.yaml")

        # Also copy base
        base_yaml = _get_domains_path() / "_base.yaml"
        if base_yaml.exists():
            shutil.copy2(base_yaml, data_dir / "_base.yaml")

        # Copy pre-generated fixtures if available
        fixtures_dir = Path(str(files("create_context_graph") / "fixtures"))
        fixture_file = fixtures_dir / f"{self.config.domain}.json"
        if fixture_file.exists():
            shutil.copy2(fixture_file, data_dir / "fixtures.json")
