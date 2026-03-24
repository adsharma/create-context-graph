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
        ladybug_db_path="./data/ladybug.db",
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
        "backend/app/constants.py",
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


class TestGeneratedEnvExample:
    """The .env.example file must exist with placeholder values."""

    def test_env_example_exists(self, generated_project):
        out, _ = generated_project
        assert (out / ".env.example").exists()

    def test_env_example_has_placeholders(self, generated_project):
        out, _ = generated_project
        content = (out / ".env.example").read_text()
        assert "your-anthropic-key-here" in content
        assert "LADYBUG_DB_PATH=" in content

    def test_env_example_no_real_credentials(self, generated_project):
        out, config = generated_project
        content = (out / ".env.example").read_text()
        assert "sk-ant-test-key" not in content


class TestGeneratedEnvFile:
    """The .env file must contain all expected keys."""

    def test_env_has_db_config(self, generated_project):
        out, config = generated_project
        env = (out / ".env").read_text()
        assert "LADYBUG_DB_PATH=" in env

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


class TestGeneratedCypher:
    """Cypher schema files must have expected DDL content."""

    def test_schema_has_ddl(self, generated_project):
        out, _ = generated_project
        schema = (out / "cypher" / "schema.cypher").read_text()
        assert "CREATE NODE TABLE" in schema
        assert "PRIMARY KEY" in schema

    def test_schema_has_rel_tables(self, generated_project):
        out, _ = generated_project
        schema = (out / "cypher" / "schema.cypher").read_text()
        assert "CREATE REL TABLE" in schema

    def test_gds_projections_exist(self, generated_project):
        out, _ = generated_project
        gds = (out / "cypher" / "gds_projections.cypher").read_text()
        assert len(gds) > 0


class TestGeneratedChatInterface:
    """ChatInterface must have session management and markdown rendering."""

    def test_chat_sends_session_id(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "session_id" in chat

    def test_chat_captures_session_id(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "setSessionId" in chat

    def test_chat_uses_react_markdown(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "ReactMarkdown" in chat

    def test_chat_shows_tool_calls(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "toolCalls" in chat or "tool_calls" in chat

    def test_package_json_has_markdown_deps(self, generated_project):
        out, _ = generated_project
        pkg = json.loads((out / "frontend" / "package.json").read_text())
        assert "react-markdown" in pkg["dependencies"]
        assert "remark-gfm" in pkg["dependencies"]


class TestGeneratedMemoryIntegration:
    """Backend must have conversation persistence."""

    def test_context_graph_client_has_memory(self, generated_project):
        out, _ = generated_project
        client = (out / "backend" / "app" / "context_graph_client.py").read_text()
        assert "get_conversation_history" in client
        assert "store_message" in client

    def test_agent_uses_conversation_history(self, generated_project):
        out, _ = generated_project
        agent = (out / "backend" / "app" / "agent.py").read_text()
        assert "get_conversation_history" in agent
        assert "store_message" in agent

    def test_routes_returns_tool_calls(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert "tool_calls" in routes
        assert "drain_tool_calls" in routes


class TestGeneratedFrontendSyntax:
    """Frontend files must have valid structure."""

    TSX_FILES = [
        "frontend/components/ChatInterface.tsx",
        "frontend/components/ContextGraphView.tsx",
        "frontend/components/DecisionTracePanel.tsx",
        "frontend/components/Provider.tsx",
        "frontend/app/layout.tsx",
        "frontend/app/page.tsx",
    ]

    @pytest.mark.parametrize("tsx_file", TSX_FILES)
    def test_tsx_has_valid_imports(self, generated_project, tsx_file):
        out, _ = generated_project
        path = out / tsx_file
        assert path.exists(), f"Missing: {tsx_file}"
        content = path.read_text()
        assert "import" in content, f"{tsx_file} missing imports"

    @pytest.mark.parametrize("tsx_file", TSX_FILES)
    def test_tsx_has_export(self, generated_project, tsx_file):
        out, _ = generated_project
        path = out / tsx_file
        content = path.read_text()
        assert "export" in content, f"{tsx_file} missing export"

    def test_config_ts_has_required_exports(self, generated_project):
        out, _ = generated_project
        config = (out / "frontend" / "lib" / "config.ts").read_text()
        for name in ["DOMAIN", "NODE_COLORS", "NODE_SIZES", "DEMO_SCENARIOS", "API_BASE"]:
            assert name in config, f"config.ts missing {name}"


class TestGeneratedTestScaffold:
    """Backend must include a test scaffold."""

    def test_test_file_exists(self, generated_project):
        out, _ = generated_project
        assert (out / "backend" / "tests" / "test_routes.py").exists()
        assert (out / "backend" / "tests" / "__init__.py").exists()

    def test_test_file_compiles(self, generated_project):
        out, _ = generated_project
        source = (out / "backend" / "tests" / "test_routes.py").read_text()
        try:
            compile(source, "test_routes.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"test_routes.py syntax error: {e}")

    def test_test_file_has_health_test(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "tests" / "test_routes.py").read_text()
        assert "def test_health" in content

    def test_test_file_has_domain_assertion(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "tests" / "test_routes.py").read_text()
        assert "financial-services" in content


class TestGeneratedBackendPyproject:
    """Backend pyproject.toml must have correct structure."""

    def test_has_project_section(self, generated_project):
        out, _ = generated_project
        content = (out / "backend" / "pyproject.toml").read_text()
        assert "[project]" in content
        assert "fastapi" in content
        assert "real_ladybug" in content

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


class TestV040Features:
    """Tests for v0.4.0 improvements."""

    def test_constants_py_generated(self, generated_project):
        out, _ = generated_project
        constants = out / "backend" / "app" / "constants.py"
        assert constants.exists()

    def test_health_endpoint_in_main(self, generated_project):
        out, _ = generated_project
        main = (out / "backend" / "app" / "main.py").read_text()
        assert "get_db_status" in main or "_db_available" in main
        assert "/health" in main
        assert "degraded" in main

    def test_graceful_db_degradation(self, generated_project):
        out, _ = generated_project
        main = (out / "backend" / "app" / "main.py").read_text()
        assert "unavailable" in main.lower() or "degraded mode" in main

    def test_is_connected_helper(self, generated_project):
        out, _ = generated_project
        client = (out / "backend" / "app" / "context_graph_client.py").read_text()
        assert "def is_connected()" in client

    def test_routes_input_validation(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert "max_length" in routes
        assert "Field(" in routes

    def test_routes_db_check_on_chat(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert "is_connected()" in routes
        assert "503" in routes

    def test_cors_configurable(self, generated_project):
        out, _ = generated_project
        main = (out / "backend" / "app" / "main.py").read_text()
        assert "CORS_ORIGINS" in main

    def test_vector_client_has_logging(self, generated_project):
        out, _ = generated_project
        vc = (out / "backend" / "app" / "vector_client.py").read_text()
        assert "logger" in vc

    def test_frontend_semantic_html(self, generated_project):
        """Frontend uses semantic HTML landmarks."""
        out, _ = generated_project
        page = (out / "frontend" / "app" / "page.tsx").read_text()
        assert 'as="main"' in page or 'as="section"' in page
        assert 'aria-label' in page

    def test_document_browser_has_pagination(self, generated_project):
        out, _ = generated_project
        doc_browser = (out / "frontend" / "components" / "DocumentBrowser.tsx").read_text()
        assert "PAGE_SIZE" in doc_browser
        assert "page" in doc_browser.lower()


class TestHealthcareEnumCompilation:
    """Verify healthcare models.py with blood type enums compiles."""

    def test_healthcare_models_compile(self, tmp_path):
        config = ProjectConfig(
            project_name="Healthcare Test",
            domain="healthcare",
            framework="pydanticai",
        )
        ontology = load_domain("healthcare")
        out = tmp_path / "healthcare-test"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        models_path = out / "backend" / "app" / "models.py"
        assert models_path.exists()
        source = models_path.read_text()
        compile(source, "models.py", "exec")
        assert "A_PLUS" in source
        assert "A_MINUS" in source


class TestGISCartographyEnumCompilation:
    """Verify gis-cartography models.py with 3d_model enum compiles."""

    def test_gis_models_compile(self, tmp_path):
        config = ProjectConfig(
            project_name="GIS Test",
            domain="gis-cartography",
            framework="pydanticai",
        )
        ontology = load_domain("gis-cartography")
        out = tmp_path / "gis-test"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        models_path = out / "backend" / "app" / "models.py"
        assert models_path.exists()
        source = models_path.read_text()
        compile(source, "models.py", "exec")
        assert "_3D_MODEL" in source


# ---------------------------------------------------------------------------
# Streaming SSE support tests
# ---------------------------------------------------------------------------

STREAMING_FRAMEWORKS = ["pydanticai", "anthropic-tools", "claude-agent-sdk", "openai-agents", "langgraph"]
NON_STREAMING_FRAMEWORKS = ["crewai", "strands", "google-adk"]


class TestStreamingEndpoint:
    """Verify /chat/stream SSE endpoint is generated in routes.py."""

    def test_routes_has_stream_endpoint(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert "/chat/stream" in routes
        assert "StreamingResponse" in routes
        assert "text/event-stream" in routes

    def test_routes_has_event_generator(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert "event_generator" in routes
        assert "event_queue" in routes

    def test_original_chat_endpoint_preserved(self, generated_project):
        out, _ = generated_project
        routes = (out / "backend" / "app" / "routes.py").read_text()
        assert '@router.post("/chat", response_model=ChatResponse)' in routes


class TestCollectorEventQueue:
    """Verify CypherResultCollector has event queue support."""

    def test_collector_has_event_queue_methods(self, generated_project):
        out, _ = generated_project
        client = (out / "backend" / "app" / "context_graph_client.py").read_text()
        assert "set_event_queue" in client
        assert "clear_event_queue" in client
        assert "emit_tool_start" in client
        assert "emit_text_delta" in client
        assert "emit_done" in client

    def test_collector_imports_asyncio(self, generated_project):
        out, _ = generated_project
        client = (out / "backend" / "app" / "context_graph_client.py").read_text()
        assert "import asyncio" in client


class TestStreamingAgentTemplates:
    """Verify streaming handler is exported for Tier 1/2 frameworks."""

    @pytest.mark.parametrize("framework", STREAMING_FRAMEWORKS)
    def test_streaming_handler_exported(self, tmp_path, framework):
        config = ProjectConfig(
            project_name="Stream Test",
            domain="financial-services",
            framework=framework,
        )
        ontology = load_domain("financial-services")
        out = tmp_path / "stream-test"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        agent_source = (out / "backend" / "app" / "agent.py").read_text()
        assert "handle_message_stream" in agent_source
        compile(agent_source, "agent.py", "exec")

    @pytest.mark.parametrize("framework", NON_STREAMING_FRAMEWORKS)
    def test_non_streaming_frameworks_no_stream_handler(self, tmp_path, framework):
        config = ProjectConfig(
            project_name="No Stream Test",
            domain="financial-services",
            framework=framework,
        )
        ontology = load_domain("financial-services")
        out = tmp_path / "no-stream-test"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        agent_source = (out / "backend" / "app" / "agent.py").read_text()
        assert "handle_message_stream" not in agent_source

    @pytest.mark.parametrize("framework", STREAMING_FRAMEWORKS)
    def test_streaming_handler_uses_collector(self, tmp_path, framework):
        config = ProjectConfig(
            project_name="Collector Test",
            domain="financial-services",
            framework=framework,
        )
        ontology = load_domain("financial-services")
        out = tmp_path / "collector-test"
        renderer = ProjectRenderer(config, ontology)
        renderer.render(out)

        agent_source = (out / "backend" / "app" / "agent.py").read_text()
        assert "get_collector" in agent_source
        assert "emit_text_delta" in agent_source
        assert "emit_done" in agent_source


class TestStreamingFrontend:
    """Verify ChatInterface has streaming support."""

    def test_chat_interface_uses_streaming(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "/chat/stream" in chat
        assert "text_delta" in chat
        assert "tool_start" in chat
        assert "tool_end" in chat

    def test_chat_interface_has_timeline(self, generated_project):
        out, _ = generated_project
        chat = (out / "frontend" / "components" / "ChatInterface.tsx").read_text()
        assert "Timeline" in chat
