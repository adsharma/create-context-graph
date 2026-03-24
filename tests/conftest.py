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

"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from create_context_graph.config import ProjectConfig
from create_context_graph.ontology import load_domain


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", default=False, help="Run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="Use --slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Provide a clean temporary output directory."""
    out = tmp_path / "test-project"
    out.mkdir()
    return out


@pytest.fixture
def financial_config() -> ProjectConfig:
    """A minimal config for the financial-services domain."""
    return ProjectConfig(
        project_name="Test Financial App",
        domain="financial-services",
        framework="pydanticai",
        ladybug_db_path="./data/ladybug.db",
    )


@pytest.fixture
def healthcare_config() -> ProjectConfig:
    """A config for the healthcare domain with Claude Agent SDK."""
    return ProjectConfig(
        project_name="Test Health App",
        domain="healthcare",
        framework="claude-agent-sdk",
        ladybug_db_path="./data/ladybug.db",
    )


@pytest.fixture
def financial_ontology():
    """Load the financial-services ontology."""
    return load_domain("financial-services")


@pytest.fixture
def healthcare_ontology():
    """Load the healthcare ontology."""
    return load_domain("healthcare")
