"""Unit tests for the renderer module."""

import json
from pathlib import Path

import pytest

from create_context_graph.ontology import load_domain
from create_context_graph.renderer import (
    ProjectRenderer,
    _to_camel_case,
    _to_kebab_case,
    _to_pascal_case,
    _to_snake_case,
)


class TestFilters:
    def test_snake_case(self):
        assert _to_snake_case("MyClass") == "my_class"
        assert _to_snake_case("camelCase") == "camel_case"
        assert _to_snake_case("kebab-case") == "kebab_case"
        assert _to_snake_case("already_snake") == "already_snake"

    def test_camel_case(self):
        assert _to_camel_case("my_class") == "myClass"
        assert _to_camel_case("hello world") == "helloWorld"

    def test_pascal_case(self):
        assert _to_pascal_case("my_class") == "MyClass"
        assert _to_pascal_case("hello world") == "HelloWorld"

    def test_kebab_case(self):
        assert _to_kebab_case("MyClass") == "my-class"
        assert _to_kebab_case("camelCase") == "camel-case"


class TestProjectRenderer:
    def test_render_creates_directory_structure(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        assert (tmp_output / "backend" / "app" / "main.py").exists()
        assert (tmp_output / "backend" / "app" / "agent.py").exists()
        assert (tmp_output / "backend" / "app" / "config.py").exists()
        assert (tmp_output / "backend" / "app" / "routes.py").exists()
        assert (tmp_output / "backend" / "app" / "models.py").exists()
        assert (tmp_output / "backend" / "app" / "context_graph_client.py").exists()
        assert (tmp_output / "backend" / "app" / "gds_client.py").exists()
        assert (tmp_output / "backend" / "app" / "vector_client.py").exists()
        assert (tmp_output / "backend" / "pyproject.toml").exists()
        assert (tmp_output / "backend" / "scripts" / "generate_data.py").exists()
        assert (tmp_output / "backend" / "app" / "__init__.py").exists()

    def test_render_creates_frontend(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        assert (tmp_output / "frontend" / "package.json").exists()
        assert (tmp_output / "frontend" / "next.config.ts").exists()
        assert (tmp_output / "frontend" / "tsconfig.json").exists()
        assert (tmp_output / "frontend" / "app" / "layout.tsx").exists()
        assert (tmp_output / "frontend" / "app" / "page.tsx").exists()
        assert (tmp_output / "frontend" / "app" / "globals.css").exists()
        assert (tmp_output / "frontend" / "components" / "ChatInterface.tsx").exists()
        assert (tmp_output / "frontend" / "components" / "ContextGraphView.tsx").exists()
        assert (tmp_output / "frontend" / "components" / "DecisionTracePanel.tsx").exists()
        assert (tmp_output / "frontend" / "components" / "Provider.tsx").exists()
        assert (tmp_output / "frontend" / "lib" / "config.ts").exists()
        assert (tmp_output / "frontend" / "theme" / "index.ts").exists()

    def test_render_creates_base_files(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        assert (tmp_output / ".env").exists()
        assert (tmp_output / ".gitignore").exists()
        assert (tmp_output / "Makefile").exists()
        assert (tmp_output / "README.md").exists()
        assert (tmp_output / "docker-compose.yml").exists()  # docker type

    def test_no_docker_compose_for_aura(self, tmp_output):
        from create_context_graph.config import ProjectConfig
        config = ProjectConfig(
            project_name="Test",
            domain="financial-services",
            framework="pydanticai",
            neo4j_type="existing",
        )
        ontology = load_domain(config.domain)
        renderer = ProjectRenderer(config, ontology)
        renderer.render(tmp_output)

        assert not (tmp_output / "docker-compose.yml").exists()

    def test_render_creates_cypher(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        assert (tmp_output / "cypher" / "schema.cypher").exists()
        assert (tmp_output / "cypher" / "gds_projections.cypher").exists()

    def test_render_creates_data(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        assert (tmp_output / "data" / "ontology.yaml").exists()
        assert (tmp_output / "data" / "_base.yaml").exists()
        assert (tmp_output / "data" / "documents").is_dir()

    def test_fixtures_bundled(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        fixture_path = tmp_output / "data" / "fixtures.json"
        assert fixture_path.exists()
        data = json.loads(fixture_path.read_text())
        assert "entities" in data
        assert "relationships" in data

    def test_env_contains_credentials(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        env_content = (tmp_output / ".env").read_text()
        assert "NEO4J_URI" in env_content
        assert financial_config.neo4j_uri in env_content

    def test_readme_contains_domain(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        readme = (tmp_output / "README.md").read_text()
        assert "Financial Services" in readme
        assert "PydanticAI" in readme

    def test_agent_uses_correct_framework(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        agent = (tmp_output / "backend" / "app" / "agent.py").read_text()
        assert "PydanticAI" in agent
        assert "pydantic_ai" in agent

    def test_claude_agent_sdk_template(self, healthcare_config, tmp_output):
        ontology = load_domain(healthcare_config.domain)
        renderer = ProjectRenderer(healthcare_config, ontology)
        renderer.render(tmp_output)

        agent = (tmp_output / "backend" / "app" / "agent.py").read_text()
        assert "Claude Agent SDK" in agent
        assert "anthropic" in agent

    def test_frontend_config_has_domain_data(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        config_ts = (tmp_output / "frontend" / "lib" / "config.ts").read_text()
        assert "Financial Services" in config_ts
        assert "NODE_COLORS" in config_ts
        assert "DEMO_SCENARIOS" in config_ts

    def test_package_json_valid(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        pkg = json.loads((tmp_output / "frontend" / "package.json").read_text())
        assert "@chakra-ui/react" in pkg["dependencies"]
        assert "next" in pkg["dependencies"]

    def test_backend_pyproject_valid(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        content = (tmp_output / "backend" / "pyproject.toml").read_text()
        assert "fastapi" in content
        assert "neo4j" in content
        assert "pydantic-ai" in content  # framework dep

    def test_cypher_schema_has_constraints(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        schema = (tmp_output / "cypher" / "schema.cypher").read_text()
        assert "CREATE CONSTRAINT" in schema
        assert "CREATE INDEX" in schema

    def test_generated_python_compiles(self, financial_config, tmp_output):
        """Verify key generated Python files are syntactically valid."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        py_files = [
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
        for py_file in py_files:
            path = tmp_output / py_file
            source = path.read_text()
            try:
                compile(source, str(path), "exec")
            except SyntaxError as e:
                pytest.fail(f"{py_file} has syntax error: {e}")


class TestAllFrameworksRender:
    """Verify every agent framework template renders and compiles."""

    FRAMEWORK_MARKERS = {
        "pydanticai": "pydantic_ai",
        "claude-agent-sdk": "anthropic",
        "openai-agents": "agents",
        "langgraph": "langgraph",
        "crewai": "crewai",
        "strands": "strands",
        "google-adk": "google.adk",
        "maf": "TOOL_REGISTRY",
    }

    @pytest.mark.parametrize("framework", [
        "pydanticai",
        "claude-agent-sdk",
        "openai-agents",
        "langgraph",
        "crewai",
        "strands",
        "google-adk",
        "maf",
    ])
    def test_framework_agent_compiles(self, framework, tmp_path):
        from create_context_graph.config import ProjectConfig

        config = ProjectConfig(
            project_name="Test",
            domain="financial-services",
            framework=framework,
        )
        ontology = load_domain(config.domain)
        out = tmp_path / f"test-{framework}"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        agent_path = out / "backend" / "app" / "agent.py"
        assert agent_path.exists(), f"No agent.py for {framework}"

        source = agent_path.read_text()
        try:
            compile(source, str(agent_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"agent.py for {framework} has syntax error: {e}")

        # Check framework-specific marker is present
        marker = self.FRAMEWORK_MARKERS[framework]
        assert marker in source, (
            f"agent.py for {framework} missing expected import/marker '{marker}'"
        )

    @pytest.mark.parametrize("framework", [
        "pydanticai",
        "claude-agent-sdk",
        "openai-agents",
        "langgraph",
        "crewai",
        "strands",
        "google-adk",
        "maf",
    ])
    def test_framework_pyproject_has_deps(self, framework, tmp_path):
        from create_context_graph.config import FRAMEWORK_DEPENDENCIES, ProjectConfig

        config = ProjectConfig(
            project_name="Test",
            domain="financial-services",
            framework=framework,
        )
        ontology = load_domain(config.domain)
        out = tmp_path / f"test-{framework}"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        pyproject = (out / "backend" / "pyproject.toml").read_text()
        for dep in FRAMEWORK_DEPENDENCIES[framework]:
            # Extract package name (before >=)
            pkg_name = dep.split(">=")[0].split("[")[0].strip()
            assert pkg_name in pyproject, (
                f"pyproject.toml for {framework} missing dependency '{pkg_name}'"
            )
