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

"""Unit tests for the config module."""

from create_context_graph.config import (
    FRAMEWORK_ALIASES,
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
        assert config.ladybug_db_path == "./data/ladybug.db"
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

    def test_custom_db_path(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="pydanticai",
            ladybug_db_path="/tmp/my-custom.db",
        )
        assert config.ladybug_db_path == "/tmp/my-custom.db"


class TestFrameworkAliases:
    def test_maf_alias_exists(self):
        assert "maf" in FRAMEWORK_ALIASES
        assert FRAMEWORK_ALIASES["maf"] == "anthropic-tools"

    def test_resolved_framework_with_alias(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="maf",
        )
        assert config.resolved_framework == "anthropic-tools"

    def test_resolved_framework_without_alias(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="pydanticai",
        )
        assert config.resolved_framework == "pydanticai"

    def test_alias_display_name(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="maf",
        )
        assert "Anthropic Tools" in config.framework_display_name

    def test_alias_deps(self):
        config = ProjectConfig(
            project_name="Test",
            domain="healthcare",
            framework="maf",
        )
        assert len(config.framework_deps) > 0
        assert any("anthropic" in dep for dep in config.framework_deps)

    def test_anthropic_tools_in_supported(self):
        assert "anthropic-tools" in SUPPORTED_FRAMEWORKS

    def test_maf_not_in_supported(self):
        assert "maf" not in SUPPORTED_FRAMEWORKS
