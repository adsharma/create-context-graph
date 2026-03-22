"""LLM-powered synthetic document generation pipeline.

Five-stage pipeline:
1. Entity seeding — Generate base entities from ontology
2. Relationship weaving — Connect entities with domain relationships
3. Document generation — LLM generates realistic business documents
4. Decision trace injection — Generate reasoning traces
5. Output — Write everything to fixtures JSON
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from create_context_graph.ontology import DomainOntology

console = Console()

# ---------------------------------------------------------------------------
# LLM client abstraction
# ---------------------------------------------------------------------------


def _get_llm_client(api_key: str, provider: str = "anthropic"):
    """Get an LLM client for generation."""
    if provider == "anthropic":
        try:
            import anthropic
            return anthropic.Anthropic(api_key=api_key), "anthropic"
        except ImportError:
            pass

    if provider == "openai" or provider != "anthropic":
        try:
            import openai
            return openai.OpenAI(api_key=api_key), "openai"
        except ImportError:
            pass

    return None, None


def _llm_generate(client, provider: str, prompt: str, system: str = "") -> str:
    """Generate text using the LLM client."""
    if provider == "anthropic":
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    elif provider == "openai":
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    return ""


def _llm_generate_json(client, provider: str, prompt: str, system: str = "") -> Any:
    """Generate JSON using the LLM client."""
    full_prompt = prompt + "\n\nRespond with valid JSON only. No markdown code fences."
    text = _llm_generate(client, provider, full_prompt, system)
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# Stage 1: Entity Seeding
# ---------------------------------------------------------------------------


def _seed_entities(ontology: DomainOntology, client=None, provider: str | None = None) -> dict[str, list[dict]]:
    """Generate base entities for each type in the ontology."""
    entities: dict[str, list[dict]] = {}

    if client and provider:
        # LLM-powered entity generation
        for et in ontology.entity_types:
            props_desc = ", ".join(
                f"{p.name} ({p.type}" + (f", one of: {p.enum}" if p.enum else "") + ")"
                for p in et.properties
            )
            prompt = f"""Generate {min(8, max(3, 15 // len(ontology.entity_types)))} realistic {et.label} entities for a {ontology.domain.name} domain.

Each entity needs these properties: {props_desc}

Return a JSON array of objects. Each object must have a "name" field plus the other properties."""
            system = f"You are generating realistic sample data for a {ontology.domain.name} knowledge graph application."

            try:
                items = _llm_generate_json(client, provider, prompt, system)
                if isinstance(items, list):
                    entities[et.label] = items
                else:
                    entities[et.label] = _generate_static_entities(et)
            except Exception:
                entities[et.label] = _generate_static_entities(et)
    else:
        # Static fallback entity generation
        for et in ontology.entity_types:
            entities[et.label] = _generate_static_entities(et)

    return entities


def _generate_static_entities(et) -> list[dict]:
    """Generate simple static entities when no LLM is available."""
    entities = []
    count = 5
    for i in range(1, count + 1):
        entity = {"name": f"{et.label} {i}"}
        for prop in et.properties:
            if prop.name == "name":
                continue
            if prop.enum:
                entity[prop.name] = prop.enum[i % len(prop.enum)]
            elif prop.type in ("string", "str"):
                entity[prop.name] = f"Sample {prop.name} for {et.label} {i}"
            elif prop.type in ("integer", "int"):
                entity[prop.name] = i * 100
            elif prop.type == "float":
                entity[prop.name] = round(i * 10.5, 2)
            elif prop.type == "boolean":
                entity[prop.name] = i % 2 == 0
            elif prop.unique:
                entity[prop.name] = f"{et.label.lower()}-{i:03d}"
        entities.append(entity)
    return entities


# ---------------------------------------------------------------------------
# Stage 2: Relationship Weaving
# ---------------------------------------------------------------------------


def _weave_relationships(
    ontology: DomainOntology,
    entities: dict[str, list[dict]],
) -> list[dict]:
    """Create relationships between entities based on ontology definitions."""
    relationships = []

    for rel_def in ontology.relationships:
        source_entities = entities.get(rel_def.source, [])
        target_entities = entities.get(rel_def.target, [])

        if not source_entities or not target_entities:
            continue

        # Create relationships: each source connects to 1-2 targets
        for source in source_entities:
            targets = random.sample(
                target_entities,
                min(random.randint(1, 2), len(target_entities)),
            )
            for target in targets:
                # Avoid self-relationships
                if source.get("name") == target.get("name"):
                    continue
                relationships.append({
                    "type": rel_def.type,
                    "source_label": rel_def.source,
                    "source_name": source["name"],
                    "target_label": rel_def.target,
                    "target_name": target["name"],
                })

    return relationships


# ---------------------------------------------------------------------------
# Stage 3: Document Generation
# ---------------------------------------------------------------------------


def _generate_documents(
    ontology: DomainOntology,
    entities: dict[str, list[dict]],
    client=None,
    provider: str | None = None,
) -> list[dict]:
    """Generate synthetic documents from templates."""
    documents = []

    for template in ontology.document_templates:
        count = min(template.count, 5)  # Cap at 5 per type for speed

        for i in range(count):
            if client and provider:
                # Build context from available entities
                context_parts = []
                for req_label in template.required_entities:
                    label_entities = entities.get(req_label, [])
                    if label_entities:
                        entity = label_entities[i % len(label_entities)]
                        context_parts.append(f"{req_label}: {entity.get('name', 'Unknown')}")

                prompt = f"""Write a realistic {template.name} document for a {ontology.domain.name} context.

Document type: {template.description}
Context: {', '.join(context_parts)}

Write 200-400 words of realistic, professional content. Do not include any metadata or headers — just the document body."""
                system = f"You are generating realistic sample documents for a {ontology.domain.name} application."

                try:
                    content = _llm_generate(client, provider, prompt, system)
                except Exception:
                    content = f"Sample {template.name} document #{i + 1} for {ontology.domain.name}."
            else:
                content = (
                    f"Sample {template.name} #{i + 1}\n\n"
                    f"This is a sample {template.description.lower()} "
                    f"for the {ontology.domain.name} domain.\n\n"
                    f"Generated by create-context-graph as demo data."
                )

            documents.append({
                "template_id": template.id,
                "template_name": template.name,
                "title": f"{template.name} #{i + 1}",
                "content": content,
            })

    return documents


# ---------------------------------------------------------------------------
# Stage 4: Decision Trace Generation
# ---------------------------------------------------------------------------


def _generate_decision_traces(
    ontology: DomainOntology,
    entities: dict[str, list[dict]],
    client=None,
    provider: str | None = None,
) -> list[dict]:
    """Generate decision traces from ontology scenarios."""
    traces = []

    for trace_def in ontology.decision_traces:
        # Fill in entity references in task description
        task = trace_def.task
        for label, ents in entities.items():
            if ents:
                entity = random.choice(ents)
                task = task.replace(f"{{{{{label.lower()}.name}}}}", entity.get("name", label))

        steps = []
        for step in trace_def.steps:
            observation = step.observation or f"Results retrieved for: {step.action}"
            if client and provider:
                try:
                    observation = _llm_generate(
                        client, provider,
                        f"Generate a brief (1-2 sentence) realistic observation/result for this action in a {ontology.domain.name} context:\n\nAction: {step.action}",
                        "Respond with just the observation text, nothing else."
                    )
                except Exception:
                    pass

            steps.append({
                "thought": step.thought,
                "action": step.action,
                "observation": observation,
            })

        outcome = trace_def.outcome_template or f"Decision completed for: {task}"
        if client and provider:
            try:
                outcome = _llm_generate(
                    client, provider,
                    f"Generate a brief (1-2 sentence) realistic outcome for this decision task:\n\nTask: {task}\nSteps taken: {len(steps)}",
                    "Respond with just the outcome text, nothing else."
                )
            except Exception:
                pass

        traces.append({
            "id": trace_def.id,
            "task": task,
            "steps": steps,
            "outcome": outcome,
        })

    return traces


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def generate_fixture_data(
    ontology: DomainOntology,
    output_path: Path,
    api_key: str | None = None,
    provider: str = "anthropic",
) -> dict:
    """Run the full generation pipeline and write fixtures.json.

    Returns the generated data dict.
    """
    client, resolved_provider = None, None
    if api_key:
        client, resolved_provider = _get_llm_client(api_key, provider)
        if client:
            console.print(f"  Using {resolved_provider} for data generation")
        else:
            console.print("  [yellow]LLM client not available, using static data[/yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Stage 1: Entity seeding
        task = progress.add_task("[1/4] Seeding entities...", total=None)
        entities = _seed_entities(ontology, client, resolved_provider)
        entity_count = sum(len(v) for v in entities.values())
        progress.update(task, description=f"[1/4] Seeded {entity_count} entities")

        # Stage 2: Relationship weaving
        task = progress.add_task("[2/4] Weaving relationships...", total=None)
        relationships = _weave_relationships(ontology, entities)
        progress.update(task, description=f"[2/4] Created {len(relationships)} relationships")

        # Stage 3: Document generation
        task = progress.add_task("[3/4] Generating documents...", total=None)
        documents = _generate_documents(ontology, entities, client, resolved_provider)
        progress.update(task, description=f"[3/4] Generated {len(documents)} documents")

        # Stage 4: Decision traces
        task = progress.add_task("[4/4] Creating decision traces...", total=None)
        traces = _generate_decision_traces(ontology, entities, client, resolved_provider)
        progress.update(task, description=f"[4/4] Created {len(traces)} decision traces")

    # Write output
    data = {
        "domain": ontology.domain.id,
        "entities": entities,
        "relationships": relationships,
        "documents": documents,
        "traces": traces,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, default=str))

    console.print(
        f"\n  [green]Generated:[/green] {entity_count} entities, "
        f"{len(relationships)} relationships, {len(documents)} documents, "
        f"{len(traces)} decision traces"
    )
    console.print(f"  [green]Written to:[/green] {output_path}")

    return data
