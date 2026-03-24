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

    def test_env_contains_db_path(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        env_content = (tmp_output / ".env").read_text()
        assert "LADYBUG_DB_PATH" in env_content

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
        assert "real_ladybug" in content
        assert "pydantic-ai" in content  # framework dep

    def test_cypher_schema_has_ddl(self, financial_config, tmp_output):
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        schema = (tmp_output / "cypher" / "schema.cypher").read_text()
        assert "CREATE NODE TABLE" in schema
        assert "PRIMARY KEY" in schema

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

    def test_env_example_generated(self, financial_config, tmp_output):
        """Verify .env.example is generated alongside .env."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        env_example = tmp_output / ".env.example"
        assert env_example.exists()
        content = env_example.read_text()
        assert "LADYBUG_DB_PATH=" in content
        assert "ANTHROPIC_API_KEY=" in content
        assert "BACKEND_PORT=" in content
        # .env.example must differ from .env (placeholders vs real values)
        env_content = (tmp_output / ".env").read_text()
        assert content != env_content

    def test_chat_interface_has_session_id(self, financial_config, tmp_output):
        """Verify ChatInterface sends session_id to backend."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        chat = (tmp_output / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "session_id" in chat
        assert "sessionId" in chat
        assert "setSessionId" in chat

    def test_chat_interface_has_markdown_rendering(self, financial_config, tmp_output):
        """Verify ChatInterface uses ReactMarkdown for assistant messages."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        chat = (tmp_output / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "ReactMarkdown" in chat
        assert "remarkGfm" in chat

    def test_package_json_has_markdown_deps(self, financial_config, tmp_output):
        """Verify package.json includes react-markdown and remark-gfm."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        pkg = json.loads((tmp_output / "frontend" / "package.json").read_text())
        assert "react-markdown" in pkg["dependencies"]
        assert "remark-gfm" in pkg["dependencies"]

    def test_context_graph_client_has_memory_functions(self, financial_config, tmp_output):
        """Verify context_graph_client.py has conversation memory functions."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        client = (tmp_output / "backend" / "app" / "context_graph_client.py").read_text()
        assert "get_conversation_history" in client
        assert "store_message" in client
        assert "drain_tool_calls" in client

    def test_agent_imports_memory_functions(self, financial_config, tmp_output):
        """Verify generated agent imports conversation memory functions."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        agent = (tmp_output / "backend" / "app" / "agent.py").read_text()
        assert "get_conversation_history" in agent
        assert "store_message" in agent

    def test_routes_has_tool_calls_in_response(self, financial_config, tmp_output):
        """Verify routes.py includes tool_calls in ChatResponse."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        routes = (tmp_output / "backend" / "app" / "routes.py").read_text()
        assert "tool_calls" in routes
        assert "drain_tool_calls" in routes

    def test_readme_has_entity_type_sections(self, financial_config, tmp_output):
        """Verify README splits entity types into base and domain-specific."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        readme = (tmp_output / "README.md").read_text()
        assert "Base POLE+O Entities" in readme
        assert "Domain-Specific Entities" in readme

    def test_main_py_cors_uses_settings(self, financial_config, tmp_output):
        """Verify main.py reads CORS origin from settings instead of hardcoding."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        main = (tmp_output / "backend" / "app" / "main.py").read_text()
        assert "settings.frontend_port" in main
        assert '"http://localhost:3000"' not in main

    def test_main_py_has_db_status(self, financial_config, tmp_output):
        """Verify main.py has LadybugDB status tracking."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        main = (tmp_output / "backend" / "app" / "main.py").read_text()
        assert "get_db_status" in main or "_db_available" in main

    def test_makefile_has_trap_cleanup(self, financial_config, tmp_output):
        """Verify Makefile uses trap for process cleanup."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        makefile = (tmp_output / "Makefile").read_text()
        assert "trap" in makefile

    def test_globals_css_has_markdown_styles(self, financial_config, tmp_output):
        """Verify globals.css includes markdown content styles."""
        ontology = load_domain(financial_config.domain)
        renderer = ProjectRenderer(financial_config, ontology)
        renderer.render(tmp_output)

        css = (tmp_output / "frontend" / "app" / "globals.css").read_text()
        assert ".markdown-content" in css


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
        "anthropic-tools": "TOOL_REGISTRY",
    }

    @pytest.mark.parametrize("framework", [
        "pydanticai",
        "claude-agent-sdk",
        "openai-agents",
        "langgraph",
        "crewai",
        "strands",
        "google-adk",
        "anthropic-tools",
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
        "anthropic-tools",
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
