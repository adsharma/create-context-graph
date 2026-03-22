"""Domain ontology loading, validation, and code generation."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models for the ontology YAML schema
# ---------------------------------------------------------------------------


class PropertyDef(BaseModel):
    """A property on a node or relationship."""

    name: str
    type: str = "string"
    required: bool = False
    unique: bool = False
    enum: list[str] | None = None
    default: str | int | float | bool | None = None
    description: str = ""


class EntityTypeDef(BaseModel):
    """A domain entity type (maps to a Neo4j node label)."""

    label: str
    pole_type: str = Field(description="POLE+O category: PERSON, ORGANIZATION, LOCATION, EVENT, OBJECT")
    subtype: str | None = None
    color: str = "#6366f1"
    icon: str = "circle"
    properties: list[PropertyDef] = Field(default_factory=list)


class RelationshipDef(BaseModel):
    """A relationship type between entity types."""

    type: str
    source: str
    target: str
    properties: list[PropertyDef] = Field(default_factory=list)


class DocumentTemplateDef(BaseModel):
    """A template for generating synthetic documents."""

    id: str
    name: str
    description: str = ""
    count: int = 5
    prompt_template: str = ""
    required_entities: list[str] = Field(default_factory=list)


class DecisionTraceStep(BaseModel):
    """A step in a decision trace scenario."""

    thought: str
    action: str
    observation: str | None = None


class DecisionTraceDef(BaseModel):
    """A decision trace scenario for generating reasoning memory."""

    id: str
    task: str
    steps: list[DecisionTraceStep] = Field(default_factory=list)
    outcome_template: str = ""


class DemoScenario(BaseModel):
    """A pre-built demo chat scenario."""

    name: str
    prompts: list[str] = Field(default_factory=list)


class AgentToolDef(BaseModel):
    """A domain-specific agent tool with Cypher query."""

    name: str
    description: str
    cypher: str = ""
    parameters: list[PropertyDef] = Field(default_factory=list)


class VisualizationConfig(BaseModel):
    """NVL visualization configuration."""

    node_colors: dict[str, str] = Field(default_factory=dict)
    node_sizes: dict[str, int] = Field(default_factory=dict)
    default_cypher: str = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100"


class DomainInfo(BaseModel):
    """Domain metadata."""

    id: str
    name: str
    description: str = ""
    tagline: str = ""
    emoji: str = ""


class DomainOntology(BaseModel):
    """Complete domain ontology definition."""

    domain: DomainInfo
    entity_types: list[EntityTypeDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
    document_templates: list[DocumentTemplateDef] = Field(default_factory=list)
    decision_traces: list[DecisionTraceDef] = Field(default_factory=list)
    demo_scenarios: list[DemoScenario] = Field(default_factory=list)
    agent_tools: list[AgentToolDef] = Field(default_factory=list)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    system_prompt: str = ""


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def _get_domains_path() -> Path:
    """Return the path to the bundled domains directory."""
    return Path(str(files("create_context_graph") / "domains"))


def list_available_domains() -> list[dict[str, str]]:
    """Return list of available domain IDs and display names.

    Returns a list of dicts with 'id' and 'name' keys, sorted by name.
    """
    domains_dir = _get_domains_path()
    results = []
    for path in sorted(domains_dir.glob("*.yaml")):
        if path.stem.startswith("_"):
            continue
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            domain_info = data.get("domain", {})
            results.append({
                "id": domain_info.get("id", path.stem),
                "name": domain_info.get("name", path.stem.replace("-", " ").title()),
            })
        except Exception:
            results.append({"id": path.stem, "name": path.stem.replace("-", " ").title()})
    return results


def _load_base() -> dict:
    """Load the base POLE+O ontology definitions."""
    base_path = _get_domains_path() / "_base.yaml"
    if not base_path.exists():
        return {}
    with open(base_path) as f:
        return yaml.safe_load(f) or {}


def _merge_base(base: dict, domain_data: dict) -> dict:
    """Merge base entity types into domain data.

    Base entity types are prepended to the domain's entity_types list
    unless the domain already defines an entity with the same label.
    Base relationships are similarly merged.
    """
    domain_labels = {et.get("label") for et in domain_data.get("entity_types", [])}
    base_entities = base.get("base_entity_types", {})

    merged_entities = []
    for label, defn in base_entities.items():
        if label not in domain_labels:
            merged_entities.append({
                "label": label,
                "pole_type": defn.get("pole_type", "OBJECT"),
                "color": defn.get("color", "#6366f1"),
                "icon": defn.get("icon", "circle"),
                "properties": defn.get("base_properties", []),
            })
    merged_entities.extend(domain_data.get("entity_types", []))
    domain_data["entity_types"] = merged_entities

    # Merge base relationships
    domain_rel_types = {r.get("type") for r in domain_data.get("relationships", [])}
    base_rels = base.get("base_relationships", {})
    merged_rels = []
    for rel_type, defn in base_rels.items():
        if rel_type not in domain_rel_types:
            merged_rels.append({
                "type": rel_type,
                "source": defn.get("source", "*"),
                "target": defn.get("target", "*"),
                "properties": defn.get("properties", []),
            })
    merged_rels.extend(domain_data.get("relationships", []))
    domain_data["relationships"] = merged_rels

    return domain_data


def load_domain(domain_id: str) -> DomainOntology:
    """Load a domain ontology by ID, merging with base definitions."""
    domains_dir = _get_domains_path()
    domain_path = domains_dir / f"{domain_id}.yaml"

    if not domain_path.exists():
        raise FileNotFoundError(f"Domain ontology not found: {domain_id}")

    with open(domain_path) as f:
        data = yaml.safe_load(f)

    # Merge base if domain declares inheritance
    if data.get("inherits") == "_base" or data.get("domain", {}).get("inherits") == "_base":
        base = _load_base()
        data = _merge_base(base, data)

    # Remove the inherits key before parsing
    data.pop("inherits", None)
    if "domain" in data and isinstance(data["domain"], dict):
        data["domain"].pop("inherits", None)

    return DomainOntology.model_validate(data)


# ---------------------------------------------------------------------------
# Code generation helpers
# ---------------------------------------------------------------------------

_PYTHON_TYPE_MAP = {
    "string": "str",
    "str": "str",
    "integer": "int",
    "int": "int",
    "float": "float",
    "boolean": "bool",
    "bool": "bool",
    "date": "date",
    "datetime": "datetime",
    "point": "str",
}

_NEO4J_TYPE_MAP = {
    "string": "STRING",
    "str": "STRING",
    "integer": "INTEGER",
    "int": "INTEGER",
    "float": "FLOAT",
    "boolean": "BOOLEAN",
    "bool": "BOOLEAN",
    "date": "DATE",
    "datetime": "DATETIME",
    "point": "POINT",
}


def generate_cypher_schema(ontology: DomainOntology) -> str:
    """Generate Cypher constraints and indexes from the ontology."""
    lines = [
        "// Auto-generated schema for domain: " + ontology.domain.name,
        "// Generated by create-context-graph",
        "",
    ]

    for et in ontology.entity_types:
        for prop in et.properties:
            if prop.unique:
                constraint_name = f"{et.label.lower()}_{prop.name}_unique"
                lines.append(
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{et.label}) REQUIRE n.{prop.name} IS UNIQUE;"
                )

        # Create index on label for common lookups
        lines.append(
            f"CREATE INDEX {et.label.lower()}_name IF NOT EXISTS "
            f"FOR (n:{et.label}) ON (n.name);"
        )
        lines.append("")

    return "\n".join(lines)


def generate_pydantic_models(ontology: DomainOntology) -> str:
    """Generate Python Pydantic model source code from the ontology."""
    imports = [
        "from __future__ import annotations",
        "",
        "from datetime import date, datetime",
        "from enum import Enum",
        "from typing import Literal",
        "",
        "from pydantic import BaseModel, Field",
        "",
        "",
    ]

    models = []
    for et in ontology.entity_types:
        # Generate enum classes for enum properties
        enum_classes = []
        for prop in et.properties:
            if prop.enum:
                enum_name = f"{et.label}{prop.name.title().replace('_', '')}Enum"
                enum_lines = [f"class {enum_name}(str, Enum):"]
                for val in prop.enum:
                    safe_name = val.upper().replace(" ", "_").replace("-", "_")
                    enum_lines.append(f'    {safe_name} = "{val}"')
                enum_lines.append("")
                enum_classes.append("\n".join(enum_lines))

        # Generate model class
        class_lines = [f"class {et.label}(BaseModel):"]
        class_lines.append(f'    """Entity model for {et.label}."""')
        class_lines.append("")

        if not et.properties:
            class_lines.append("    pass")
        else:
            for prop in et.properties:
                py_type = _PYTHON_TYPE_MAP.get(prop.type, "str")
                if prop.enum:
                    enum_name = f"{et.label}{prop.name.title().replace('_', '')}Enum"
                    py_type = enum_name

                if not prop.required:
                    py_type = f"{py_type} | None"
                    default = "None"
                else:
                    default = "..."

                if prop.default is not None:
                    default = f'"{prop.default}"' if prop.type in ("string", "str") else prop.default

                class_lines.append(f"    {prop.name}: {py_type} = {default}")

        class_lines.append("")
        models.extend(enum_classes)
        models.append("\n".join(class_lines))

    return "\n".join(imports) + "\n".join(models)


def generate_visualization_config(ontology: DomainOntology) -> dict:
    """Generate NVL visualization config from the ontology."""
    colors = dict(ontology.visualization.node_colors)
    sizes = dict(ontology.visualization.node_sizes)

    # Fill in from entity types if not explicitly set
    for et in ontology.entity_types:
        if et.label not in colors:
            colors[et.label] = et.color
        if et.label not in sizes:
            sizes[et.label] = 20  # default

    return {
        "nodeColors": colors,
        "nodeSizes": sizes,
        "defaultCypher": ontology.visualization.default_cypher,
    }
