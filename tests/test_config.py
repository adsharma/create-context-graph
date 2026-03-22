"""Unit tests for the config module."""

from create_context_graph.config import (
    FRAMEWORK_DEPENDENCIES,
    FRAMEWORK_DISPLAY_NAMES,
    SUPPORTED_FRAMEWORKS,
    ProjectConfig,
)


class TestProjectConfig:
    def test_basic_creation(self):
        config = ProjectConfig(
            project_name="My App",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.project_name == "My App"
        assert config.domain == "healthcare"
        assert config.framework == "pydanticai"

    def test_project_slug_from_name(self):
        config = ProjectConfig(
            project_name="My Cool App",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.project_slug == "my-cool-app"

    def test_project_slug_special_chars(self):
        config = ProjectConfig(
            project_name="Test App!@# 123",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.project_slug == "test-app-123"

    def test_project_slug_leading_trailing(self):
        config = ProjectConfig(
            project_name="  --My App--  ",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.project_slug == "my-app"

    def test_defaults(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.neo4j_uri == "neo4j://localhost:7687"
        assert config.neo4j_username == "neo4j"
        assert config.neo4j_password == "password"
        assert config.neo4j_type == "docker"
        assert config.data_source == "demo"
        assert config.generate_data is False
        assert config.anthropic_api_key is None
        assert config.openai_api_key is None

    def test_framework_display_name(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="claude-agent-sdk",
        )
        assert config.framework_display_name == "Claude Agent SDK"

    def test_framework_deps(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="pydanticai",
        )
        assert len(config.framework_deps) > 0
        assert any("pydantic-ai" in dep for dep in config.framework_deps)

    def test_all_frameworks_have_display_names(self):
        for fw in SUPPORTED_FRAMEWORKS:
            assert fw in FRAMEWORK_DISPLAY_NAMES

    def test_all_frameworks_have_deps(self):
        for fw in SUPPORTED_FRAMEWORKS:
            assert fw in FRAMEWORK_DEPENDENCIES

    def test_aura_config(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="pydanticai",
            neo4j_type="aurads",
            neo4j_uri="neo4j+s://abc.databases.neo4j.io",
        )
        assert config.neo4j_type == "aurads"
        assert "neo4j+s" in config.neo4j_uri
