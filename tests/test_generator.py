"""Unit tests for the generator module."""

import json
from pathlib import Path

import pytest

from create_context_graph.generator import generate_fixture_data
from create_context_graph.ontology import load_domain


class TestGenerateFixtureData:
    def test_generates_fixture_file(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert output.exists()
        assert isinstance(data, dict)

    def test_fixture_has_entities(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert "entities" in data
        assert len(data["entities"]) > 0
        # Should have entities for domain-specific types
        assert "Account" in data["entities"]
        assert "Transaction" in data["entities"]
        # Should also have base POLE+O types
        assert "Person" in data["entities"]

    def test_fixture_has_relationships(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert "relationships" in data
        assert len(data["relationships"]) > 0
        rel = data["relationships"][0]
        assert "type" in rel
        assert "source_label" in rel
        assert "source_name" in rel
        assert "target_label" in rel
        assert "target_name" in rel

    def test_fixture_has_documents(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert "documents" in data
        assert len(data["documents"]) > 0
        doc = data["documents"][0]
        assert "template_id" in doc
        assert "title" in doc
        assert "content" in doc

    def test_fixture_has_traces(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert "traces" in data
        assert len(data["traces"]) > 0
        trace = data["traces"][0]
        assert "task" in trace
        assert "steps" in trace
        assert len(trace["steps"]) > 0
        step = trace["steps"][0]
        assert "thought" in step
        assert "action" in step

    def test_fixture_is_valid_json(self, tmp_path):
        ontology = load_domain("financial-services")
        output = tmp_path / "fixtures.json"
        generate_fixture_data(ontology, output)

        parsed = json.loads(output.read_text())
        assert parsed["domain"] == "financial-services"

    def test_entities_have_names(self, tmp_path):
        ontology = load_domain("healthcare")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        for label, items in data["entities"].items():
            for item in items:
                assert "name" in item, f"{label} entity missing 'name'"

    def test_no_self_relationships(self, tmp_path):
        ontology = load_domain("software-engineering")
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        for rel in data["relationships"]:
            if rel["source_label"] == rel["target_label"]:
                assert rel["source_name"] != rel["target_name"], (
                    f"Self-relationship found: {rel}"
                )


class TestGenerateMultipleDomains:
    """Test that fixture generation works for a sample of domains."""

    @pytest.mark.parametrize("domain_id", [
        "financial-services",
        "healthcare",
        "software-engineering",
        "wildlife-management",
        "gaming",
        "manufacturing",
    ])
    def test_domain_generates(self, domain_id, tmp_path):
        ontology = load_domain(domain_id)
        output = tmp_path / "fixtures.json"
        data = generate_fixture_data(ontology, output)

        assert output.exists()
        assert len(data["entities"]) > 0
        assert len(data["relationships"]) > 0
        assert len(data["documents"]) > 0
        assert len(data["traces"]) > 0
