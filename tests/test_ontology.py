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

"""Unit tests for the ontology module."""

import pytest

from create_context_graph.ontology import (
    DomainOntology,
    EntityTypeDef,
    PropertyDef,
    RelationshipDef,
    _sanitize_enum_name,
    generate_cypher_schema,
    generate_pydantic_models,
    generate_visualization_config,
    list_available_domains,
    load_domain,
)


class TestListDomains:
    def test_returns_list(self):
        domains = list_available_domains()
        assert isinstance(domains, list)

    def test_has_at_least_22_domains(self):
        domains = list_available_domains()
        assert len(domains) >= 22

    def test_each_domain_has_id_and_name(self):
        domains = list_available_domains()
        for d in domains:
            assert "id" in d
            assert "name" in d
            assert len(d["id"]) > 0
            assert len(d["name"]) > 0

    def test_base_not_in_list(self):
        domains = list_available_domains()
        ids = [d["id"] for d in domains]
        assert "_base" not in ids

    def test_known_domains_present(self):
        domains = list_available_domains()
        ids = [d["id"] for d in domains]
        assert "financial-services" in ids
        assert "healthcare" in ids
        assert "software-engineering" in ids
        assert "wildlife-management" in ids


class TestLoadDomain:
    def test_load_financial_services(self):
        ont = load_domain("financial-services")
        assert isinstance(ont, DomainOntology)
        assert ont.domain.id == "financial-services"
        assert ont.domain.name == "Financial Services"

    def test_load_healthcare(self):
        ont = load_domain("healthcare")
        assert ont.domain.id == "healthcare"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_domain("nonexistent-domain-xyz")

    def test_entity_types_present(self):
        ont = load_domain("financial-services")
        assert len(ont.entity_types) > 0
        labels = [et.label for et in ont.entity_types]
        assert "Account" in labels
        assert "Transaction" in labels

    def test_base_entities_merged(self):
        ont = load_domain("financial-services")
        labels = [et.label for et in ont.entity_types]
        # Base POLE+O entities should be merged in
        assert "Person" in labels
        assert "Organization" in labels
        assert "Location" in labels

    def test_relationships_present(self):
        ont = load_domain("financial-services")
        assert len(ont.relationships) > 0
        rel_types = [r.type for r in ont.relationships]
        assert "OWNS" in rel_types

    def test_base_relationships_merged(self):
        ont = load_domain("financial-services")
        rel_types = [r.type for r in ont.relationships]
        assert "WORKS_FOR" in rel_types  # from base

    def test_document_templates_present(self):
        ont = load_domain("financial-services")
        assert len(ont.document_templates) > 0
        for tmpl in ont.document_templates:
            assert tmpl.id
            assert tmpl.name
            assert tmpl.count > 0

    def test_decision_traces_present(self):
        ont = load_domain("financial-services")
        assert len(ont.decision_traces) > 0
        for trace in ont.decision_traces:
            assert trace.id
            assert trace.task
            assert len(trace.steps) > 0

    def test_demo_scenarios_present(self):
        ont = load_domain("financial-services")
        assert len(ont.demo_scenarios) > 0
        for scenario in ont.demo_scenarios:
            assert scenario.name
            assert len(scenario.prompts) > 0

    def test_agent_tools_present(self):
        ont = load_domain("financial-services")
        assert len(ont.agent_tools) > 0
        for tool in ont.agent_tools:
            assert tool.name
            assert tool.description
            assert tool.cypher

    def test_system_prompt_present(self):
        ont = load_domain("financial-services")
        assert len(ont.system_prompt) > 50

    def test_visualization_config(self):
        ont = load_domain("financial-services")
        assert len(ont.visualization.node_colors) > 0
        assert len(ont.visualization.node_sizes) > 0
        assert ont.visualization.default_cypher


class TestLoadAllDomains:
    """Ensure every bundled domain YAML parses without error."""

    def test_all_domains_load(self):
        domains = list_available_domains()
        for d in domains:
            ont = load_domain(d["id"])
            assert ont.domain.id == d["id"]
            assert len(ont.entity_types) >= 4  # base POLE+O + at least 1 domain
            assert len(ont.relationships) >= 3
            assert len(ont.agent_tools) >= 1
            assert ont.system_prompt


class TestGenerateCypherSchema:
    def test_generates_node_tables(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "CREATE NODE TABLE" in schema
        assert "IF NOT EXISTS" in schema
        assert "PRIMARY KEY" in schema

    def test_generates_rel_tables(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "CREATE REL TABLE" in schema

    def test_has_header_comment(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "Financial Services" in schema

    def test_no_empty_statements(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        for line in schema.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("//"):
                assert len(line) > 1  # meaningful content (allows ");")



class TestGeneratePydanticModels:
    def test_generates_valid_python(self, financial_ontology):
        source = generate_pydantic_models(financial_ontology)
        assert "from pydantic import BaseModel" in source
        assert "class Account(BaseModel):" in source
        assert "class Transaction(BaseModel):" in source

    def test_generates_enum_classes(self, financial_ontology):
        source = generate_pydantic_models(financial_ontology)
        # Account has account_type enum
        assert "Enum" in source

    def test_source_compiles(self, financial_ontology):
        source = generate_pydantic_models(financial_ontology)
        # Should be valid Python that compiles
        compile(source, "<test>", "exec")


class TestGenerateVisualizationConfig:
    def test_has_colors_and_sizes(self, financial_ontology):
        config = generate_visualization_config(financial_ontology)
        assert "nodeColors" in config
        assert "nodeSizes" in config
        assert "defaultCypher" in config

    def test_all_entity_types_have_colors(self, financial_ontology):
        config = generate_visualization_config(financial_ontology)
        for et in financial_ontology.entity_types:
            assert et.label in config["nodeColors"]


class TestSanitizeEnumName:
    """Test _sanitize_enum_name handles special characters."""

    def test_plus_sign(self):
        assert _sanitize_enum_name("A+") == "A_PLUS"

    def test_minus_sign(self):
        assert _sanitize_enum_name("A-") == "A_MINUS"

    def test_blood_types(self):
        assert _sanitize_enum_name("AB+") == "AB_PLUS"
        assert _sanitize_enum_name("AB-") == "AB_MINUS"
        assert _sanitize_enum_name("O+") == "O_PLUS"
        assert _sanitize_enum_name("O-") == "O_MINUS"

    def test_leading_digit(self):
        assert _sanitize_enum_name("3d_model") == "_3D_MODEL"

    def test_all_digits(self):
        assert _sanitize_enum_name("123") == "_123"

    def test_normal_value(self):
        assert _sanitize_enum_name("normal_value") == "NORMAL_VALUE"

    def test_spaces(self):
        assert _sanitize_enum_name("with spaces") == "WITH_SPACES"

    def test_hyphens_as_separator(self):
        """Hyphens between words are treated as separators, not minus."""
        assert _sanitize_enum_name("some-value") == "SOME_VALUE"

    def test_trailing_minus(self):
        """Trailing minus is converted to _MINUS."""
        assert _sanitize_enum_name("B-") == "B_MINUS"

    def test_result_is_valid_identifier(self):
        """All sanitized names must be valid Python identifiers."""
        test_values = [
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
            "3d_model", "normal", "with spaces", "123numeric",
        ]
        for val in test_values:
            result = _sanitize_enum_name(val)
            assert result.isidentifier(), f"'{val}' -> '{result}' is not a valid identifier"


class TestEnumModelsCompileAllDomains:
    """Ensure models.py compiles for all domains (catches enum bugs)."""

    ALL_DOMAINS = [d["id"] for d in list_available_domains()]

    @pytest.mark.parametrize("domain_id", ALL_DOMAINS)
    def test_models_compile(self, domain_id):
        ontology = load_domain(domain_id)
        source = generate_pydantic_models(ontology)
        try:
            compile(source, f"{domain_id}/models.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"models.py syntax error for {domain_id}: {e}")
