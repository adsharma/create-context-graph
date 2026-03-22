"""Deep validation tests for generated project files.

Verifies that scaffolded projects have correct structure,
valid syntax, and expected content.
"""

from __future__ import annotations

import json

import pytest
import yaml

from create_context_graph.config import ProjectConfig
from create_context_graph.ontology import load_domain
from create_context_graph.renderer import ProjectRenderer


@pytest.fixture
def generated_project(tmp_path):
    """Scaffold a full project and return its path."""
    config = ProjectConfig(
        project_name="Deep Validation App",
        domain="financial-services",
        framework="pydanticai",
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="testpass123",
        neo4j_type="docker",
        anthropic_api_key="sk-ant-test-key",
        openai_api_key="sk-test-openai",
    )
    ontology = load_domain(config.domain)
    out = tmp_path / "test-project"
    renderer = ProjectRenderer(config, ontology)
    renderer.render(out)
    return out, config


class TestGeneratedPythonFiles:
    """All generated Python files must be syntactically valid."""

    PYTHON_FILES = [
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/agent.py",
        "backend/app/routes.py",
        "backend/app/models.py",
        "backend/app/context_graph_client.py",
        "backend/app/gds_client.py",
        "backend/app/vector_client.py",
        "backend/scripts/generate_data.py",
    ]

    @pytest.mark.parametrize("py_file", PYTHON_FILES)
    def test_python_file_compiles(self, generated_project, py_file):
        out, _ = generated_project
        path = out / py_file
        assert path.exists(), f"Missing: {py_file}"
        source = path.read_text()
        try:
            compile(source, str(path), "exec")
        except SyntaxError as e:
            pytest.fail(f"{py_file} syntax error: {e}")

    def test_init_py_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "backend" / "app" / "__init__.py").exists()


class TestGeneratedFrontendFiles:
    """Frontend files must exist and be valid."""

    def test_package_json_valid(self, generated_project):
        out, _ = generated_project
        pkg = json.loads((out / "frontend" / "package.json").read_text())
        assert "dependencies" in pkg
        assert "@chakra-ui/react" in pkg["dependencies"]
        assert "next" in pkg["dependencies"]
        assert "react" in pkg["dependencies"]
        assert "@neo4j-nvl/react" in pkg["dependencies"]

    def test_tsconfig_valid(self, generated_project):
        out, _ = generated_project
        tsconfig = json.loads((out / "frontend" / "tsconfig.json").read_text())
        assert "compilerOptions" in tsconfig

    def test_config_ts_has_domain_data(self, generated_project):
        out, _ = generated_project
        config_ts = (out / "frontend" / "lib" / "config.ts").read_text()
        assert "DOMAIN" in config_ts
        assert "NODE_COLORS" in config_ts
        assert "NODE_SIZES" in config_ts
        assert "DEMO_SCENARIOS" in config_ts
        assert "API_BASE" in config_ts

    def test_all_components_exist(self, generated_project):
        out, _ = generated_project
        components = [
            "ChatInterface.tsx",
            "ContextGraphView.tsx",
            "DecisionTracePanel.tsx",
            "Provider.tsx",
        ]
        for comp in components:
            assert (out / "frontend" / "components" / comp).exists(), f"Missing: {comp}"

    def test_layout_and_page_exist(self, generated_project):
        out, _ = generated_project
        assert (out / "frontend" / "app" / "layout.tsx").exists()
        assert (out / "frontend" / "app" / "page.tsx").exists()
        assert (out / "frontend" / "app" / "globals.css").exists()

    def test_theme_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "frontend" / "theme" / "index.ts").exists()


class TestGeneratedEnvFile:
    """The .env file must contain all expected keys."""

    def test_env_has_neo4j_config(self, generated_project):
        out, config = generated_project
        env = (out / ".env").read_text()
        assert "NEO4J_URI=" in env
        assert config.neo4j_uri in env
        assert "NEO4J_USERNAME=" in env
        assert "NEO4J_PASSWORD=" in env

    def test_env_has_api_keys(self, generated_project):
        out, _ = generated_project
        env = (out / ".env").read_text()
        assert "ANTHROPIC_API_KEY=" in env
        assert "OPENAI_API_KEY=" in env

    def test_env_has_ports(self, generated_project):
        out, _ = generated_project
        env = (out / ".env").read_text()
        assert "BACKEND_PORT=" in env
        assert "FRONTEND_PORT=" in env


class TestGeneratedMakefile:
    """Makefile must have all expected targets."""

    EXPECTED_TARGETS = ["start", "dev", "install", "seed", "reset", "clean", "test", "lint"]

    def test_makefile_has_targets(self, generated_project):
        out, _ = generated_project
        makefile = (out / "Makefile").read_text()
        for target in self.EXPECTED_TARGETS:
            assert f"{target}:" in makefile or f"{target} " in makefile, (
                f"Makefile missing target: {target}"
            )

    def test_makefile_has_phony(self, generated_project):
        out, _ = generated_project
        makefile = (out / "Makefile").read_text()
        assert ".PHONY" in makefile


class TestGeneratedDockerCompose:
    """docker-compose.yml must be valid YAML when neo4j_type=docker."""

    def test_docker_compose_valid_yaml(self, generated_project):
        out, _ = generated_project
        dc_path = out / "docker-compose.yml"
        assert dc_path.exists()
        data = yaml.safe_load(dc_path.read_text())
        assert "services" in data
        assert "neo4j" in data["services"]

    def test_no_docker_compose_for_aura(self, tmp_path):
        config = ProjectConfig(
            project_name="Aura Test",
            domain="healthcare",
            framework="pydanticai",
            neo4j_type="aurads",
        )
        ontology = load_domain(config.domain)
        out = tmp_path / "aura-project"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)
        assert not (out / "docker-compose.yml").exists()


class TestGeneratedCypher:
    """Cypher files must have expected content."""

    def test_schema_has_constraints_and_indexes(self, generated_project):
        out, _ = generated_project
        schema = (out / "cypher" / "schema.cypher").read_text()
        assert "CREATE CONSTRAINT" in schema
        assert "CREATE INDEX" in schema
        assert "IF NOT EXISTS" in schema

    def test_gds_projections_exist(self, generated_project):
        out, _ = generated_project
        gds = (out / "cypher" / "gds_projections.cypher").read_text()
        assert "gds.graph.project" in gds


class TestGeneratedBackendPyproject:
    """Backend pyproject.toml must have correct structure."""

    def test_has_project_section(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "pyproject.toml").read_text()
        assert "[project]" in content
        assert "fastapi" in content
        assert "neo4j" in content

    def test_has_hatch_packages(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "pyproject.toml").read_text()
        assert 'packages = ["app"]' in content

    def test_has_framework_dep(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "pyproject.toml").read_text()
        assert "pydantic-ai" in content


class TestGeneratedReadme:
    """README must contain domain and framework info."""

    def test_readme_has_domain(self, generated_project):
        out, _ = generated_project
        readme = (out / "README.md").read_text()
        assert "Financial Services" in readme

    def test_readme_has_framework(self, generated_project):
        out, _ = generated_project
        readme = (out / "README.md").read_text()
        assert "PydanticAI" in readme

    def test_readme_has_quick_start(self, generated_project):
        out, _ = generated_project
        readme = (out / "README.md").read_text()
        assert "make install" in readme
        assert "make start" in readme


class TestGeneratedDataFiles:
    """Data directory must have ontology and fixtures."""

    def test_ontology_yaml_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "data" / "ontology.yaml").exists()

    def test_base_yaml_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "data" / "_base.yaml").exists()

    def test_fixtures_json_valid(self, generated_project):
        out, _ = generated_project
        fixture_path = out / "data" / "fixtures.json"
        assert fixture_path.exists()
        data = json.loads(fixture_path.read_text())
        assert "entities" in data
        assert "relationships" in data
        assert "documents" in data
        assert "traces" in data

    def test_documents_dir_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "data" / "documents").is_dir()
