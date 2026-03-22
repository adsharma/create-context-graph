"""Integration tests for the CLI module."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from create_context_graph.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestListDomains:
    def test_list_domains(self, runner):
        result = runner.invoke(main, ["--list-domains"])
        assert result.exit_code == 0
        assert "financial-services" in result.output
        assert "healthcare" in result.output
        assert "software-engineering" in result.output

    def test_list_shows_22_domains(self, runner):
        result = runner.invoke(main, ["--list-domains"])
        assert result.exit_code == 0
        # Count non-empty lines that look like domain entries
        lines = [l for l in result.output.strip().split("\n") if l.strip() and not l.startswith("Available")]
        assert len(lines) >= 22


class TestVersion:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestScaffoldGeneration:
    def test_basic_scaffold(self, runner, tmp_path):
        out = tmp_path / "my-app"
        result = runner.invoke(main, [
            "my-app",
            "--domain", "financial-services",
            "--framework", "pydanticai",
            "--output-dir", str(out),
        ])
        assert result.exit_code == 0, result.output
        assert (out / "backend" / "app" / "main.py").exists()
        assert (out / "frontend" / "package.json").exists()

    def test_scaffold_with_demo_data(self, runner, tmp_path):
        out = tmp_path / "my-app"
        result = runner.invoke(main, [
            "my-app",
            "--domain", "healthcare",
            "--framework", "claude-agent-sdk",
            "--demo-data",
            "--output-dir", str(out),
        ])
        assert result.exit_code == 0, result.output
        fixture = out / "data" / "fixtures.json"
        assert fixture.exists()
        data = json.loads(fixture.read_text())
        assert len(data["entities"]) > 0

    def test_invalid_domain(self, runner, tmp_path):
        out = tmp_path / "my-app"
        result = runner.invoke(main, [
            "my-app",
            "--domain", "nonexistent-domain",
            "--framework", "pydanticai",
            "--output-dir", str(out),
        ])
        assert result.exit_code == 1

    def test_existing_nonempty_dir_fails(self, runner, tmp_path):
        out = tmp_path / "my-app"
        out.mkdir()
        (out / "existing-file.txt").write_text("hello")

        result = runner.invoke(main, [
            "my-app",
            "--domain", "financial-services",
            "--framework", "pydanticai",
            "--output-dir", str(out),
        ])
        assert result.exit_code == 1
        assert "already exists" in result.output


class TestMultipleDomainScaffolds:
    """Integration test: scaffold generation works for multiple domains."""

    @pytest.mark.parametrize("domain_id,framework", [
        ("financial-services", "pydanticai"),
        ("healthcare", "claude-agent-sdk"),
        ("software-engineering", "openai-agents"),
        ("wildlife-management", "langgraph"),
        ("gaming", "crewai"),
        ("manufacturing", "strands"),
        ("digital-twin", "google-adk"),
        ("retail-ecommerce", "maf"),
    ])
    def test_domain_framework_combo(self, runner, tmp_path, domain_id, framework):
        out = tmp_path / f"test-{domain_id}"
        result = runner.invoke(main, [
            f"test-{domain_id}",
            "--domain", domain_id,
            "--framework", framework,
            "--output-dir", str(out),
        ])
        assert result.exit_code == 0, f"{domain_id}/{framework} failed: {result.output}"

        # Check key files
        assert (out / "backend" / "app" / "agent.py").exists()
        assert (out / "frontend" / "lib" / "config.ts").exists()
        assert (out / "cypher" / "schema.cypher").exists()
        assert (out / "data" / "fixtures.json").exists()

        # Verify agent template matches framework
        agent = (out / "backend" / "app" / "agent.py").read_text()
        framework_markers = {
            "pydanticai": "PydanticAI",
            "claude-agent-sdk": "Claude Agent SDK",
            "openai-agents": "OpenAI Agents SDK",
            "langgraph": "LangGraph",
            "crewai": "CrewAI",
            "strands": "Strands",
            "google-adk": "Google ADK",
            "maf": "MAF",
        }
        marker = framework_markers.get(framework)
        if marker:
            assert marker in agent, f"Agent file missing '{marker}' for framework {framework}"
