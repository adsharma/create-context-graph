"""Unit tests for the ontology module."""

import pytest

from create_context_graph.ontology import (
    DomainOntology,
    EntityTypeDef,
    PropertyDef,
    RelationshipDef,
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
    def test_generates_constraints(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "CREATE CONSTRAINT" in schema
        assert "IF NOT EXISTS" in schema
        assert "account_id" in schema.lower()

    def test_generates_indexes(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "CREATE INDEX" in schema

    def test_has_header_comment(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        assert "Financial Services" in schema

    def test_no_empty_statements(self, financial_ontology):
        schema = generate_cypher_schema(financial_ontology)
        for line in schema.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("//"):
                assert len(line) > 5  # meaningful statement


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
