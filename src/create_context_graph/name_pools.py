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

"""Realistic name pools and value generators for static fixture data.

Provides domain-appropriate names and property values so that the static
fallback generator produces passable demo data without an LLM.
"""

from __future__ import annotations

import random
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Name pools organized by POLE+O type
# ---------------------------------------------------------------------------

PERSON_NAMES = [
    "Sarah Chen", "James Morrison", "Maria Rodriguez", "David Park",
    "Elena Volkov", "Michael O'Brien", "Aisha Patel", "Robert Kim",
    "Lisa Nakamura", "Carlos Gutierrez", "Fatima Al-Hassan", "Thomas Weber",
    "Priya Sharma", "John Washington", "Yuki Tanaka", "Rachel Okonkwo",
    "Andreas Mueller", "Sofia Petrova", "Benjamin Adeyemi", "Grace Nguyen",
    "Marcus Thompson", "Isabelle Fournier", "Omar Rashid", "Emily Hartman",
    "Daniel Kowalski",
]

ORGANIZATION_NAMES = [
    "Meridian Consulting Group", "Pacific Northwest Industries",
    "Apex Financial Partners", "Greenleaf Technologies",
    "Summit Healthcare Systems", "Atlas Data Solutions",
    "Cornerstone Engineering", "BlueStar Analytics",
    "Ironwood Manufacturing", "Catalyst Research Labs",
    "Nexus Global Services", "Harbourview Capital",
    "Pinnacle Logistics", "Quantum Dynamics Corp",
    "Redwood Environmental", "Sterling Associates",
    "Trident Marine Solutions", "Vanguard Innovations",
    "Westfield Properties", "Zenith Aerospace",
]

LOCATION_NAMES = [
    "Downtown Medical Center", "Westside Corporate Campus",
    "Harbor View Complex", "Mountain Ridge Facility",
    "Riverside Research Park", "Lakefront Office Tower",
    "Northern District Hub", "Central Processing Center",
    "Coastal Operations Base", "Metropolitan Data Center",
    "Valley Industrial Park", "Skyline Business Center",
    "Oakwood Conference Center", "Bayshore Distribution Hub",
    "Parkside Innovation Lab",
]

EVENT_NAMES = [
    "Q4 Strategy Review", "Annual Compliance Audit",
    "Emergency Response Drill", "Product Launch Summit",
    "Board of Directors Meeting", "Technology Integration Workshop",
    "Quarterly Performance Review", "Safety Inspection Round",
    "Customer Advisory Council", "Research Symposium",
    "Budget Planning Session", "Stakeholder Town Hall",
]

OBJECT_NAMES = [
    "Primary Analysis Report", "Standard Operating Procedure",
    "Quarterly Assessment Document", "Technical Specification",
    "Compliance Certificate", "Risk Evaluation Matrix",
    "Performance Dashboard", "Quality Control Record",
    "Strategic Initiative Brief", "Operations Manual",
    "Incident Response Protocol", "Resource Allocation Plan",
]

# ---------------------------------------------------------------------------
# Property name patterns for contextual value generation
# ---------------------------------------------------------------------------

_EMAIL_PROPERTIES = {"email", "email_address", "contact_email"}
_PHONE_PROPERTIES = {"phone", "phone_number", "contact_phone", "telephone"}
_URL_PROPERTIES = {"url", "website", "homepage", "link"}
_ADDRESS_PROPERTIES = {"address", "street_address", "location_address"}
_DESCRIPTION_PROPERTIES = {"description", "summary", "notes", "details", "bio"}
_ID_PROPERTIES = {"id", "code", "number", "identifier"}

_STREETS = [
    "123 Main Street", "456 Oak Avenue", "789 Pine Boulevard",
    "321 Maple Drive", "654 Cedar Lane", "987 Elm Court",
    "147 Birch Road", "258 Willow Way", "369 Spruce Circle",
    "741 Chestnut Terrace",
]

_CITIES = [
    "San Francisco, CA 94105", "New York, NY 10001", "Chicago, IL 60601",
    "Austin, TX 78701", "Seattle, WA 98101", "Boston, MA 02101",
    "Denver, CO 80202", "Portland, OR 97201", "Miami, FL 33101",
    "Atlanta, GA 30301",
]

_ROLE_POOL = [
    "Senior Analyst", "Project Manager", "Technical Lead",
    "Research Director", "Operations Manager", "Chief Strategist",
    "Field Coordinator", "Quality Assurance Lead", "Data Scientist",
    "Solutions Architect", "Program Director", "Compliance Officer",
]

_INDUSTRY_POOL = [
    "Technology", "Healthcare", "Financial Services", "Manufacturing",
    "Energy", "Consulting", "Real Estate", "Education",
    "Environmental Services", "Logistics",
]


# ---------------------------------------------------------------------------
# Value generators
# ---------------------------------------------------------------------------


def generate_email(name: str) -> str:
    """Generate a realistic email from a person name."""
    parts = name.lower().split()
    first = parts[0].replace("'", "")
    last = parts[-1].replace("'", "")
    domains = ["example.com", "company.org", "acme.co", "corp.net"]
    return f"{first}.{last}@{random.choice(domains)}"


def generate_phone() -> str:
    """Generate a realistic US phone number."""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1-{area}-{prefix}-{line}"


def generate_date(start_year: int = 2024, end_year: int = 2026) -> str:
    """Generate a random date string in ISO format."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    random_date = start + timedelta(days=random.randint(0, delta))
    return random_date.isoformat()


def generate_datetime(start_year: int = 2024, end_year: int = 2026) -> str:
    """Generate a random datetime string in ISO format."""
    d = generate_date(start_year, end_year)
    hour = random.randint(8, 17)
    minute = random.choice([0, 15, 30, 45])
    return f"{d}T{hour:02d}:{minute:02d}:00"


def generate_id(prefix: str, index: int) -> str:
    """Generate a realistic ID string."""
    year = random.choice([2024, 2025, 2026])
    return f"{prefix.upper()}-{year}-{index:04d}"


def generate_currency(min_val: float = 100, max_val: float = 500000) -> float:
    """Generate a realistic currency amount."""
    return round(random.uniform(min_val, max_val), 2)


def generate_url(name: str) -> str:
    """Generate a URL from a name."""
    slug = name.lower().replace(" ", "-").replace("'", "")
    return f"https://www.{slug}.example.com"


def generate_address() -> str:
    """Generate a realistic address."""
    return f"{random.choice(_STREETS)}, {random.choice(_CITIES)}"


def generate_latitude() -> float:
    """Generate a realistic latitude."""
    return round(random.uniform(25.0, 48.0), 6)


def generate_longitude() -> float:
    """Generate a realistic longitude."""
    return round(random.uniform(-122.0, -71.0), 6)


# ---------------------------------------------------------------------------
# Main interface
# ---------------------------------------------------------------------------


def get_names_for_pole_type(pole_type: str, count: int) -> list[str]:
    """Get realistic names appropriate for the given POLE+O type."""
    pool = {
        "PERSON": PERSON_NAMES,
        "ORGANIZATION": ORGANIZATION_NAMES,
        "LOCATION": LOCATION_NAMES,
        "EVENT": EVENT_NAMES,
        "OBJECT": OBJECT_NAMES,
    }.get(pole_type.upper(), OBJECT_NAMES)

    # Extend pool if more names needed than available
    names = list(pool)
    while len(names) < count:
        names.extend(f"{n} {chr(65 + i)}" for i, n in enumerate(pool))
    return names[:count]


def generate_property_value(
    prop_name: str,
    prop_type: str,
    entity_name: str,
    label: str,
    index: int,
) -> str | int | float | bool | None:
    """Generate a contextually appropriate property value based on name and type."""
    name_lower = prop_name.lower()

    # Handle by property name patterns first
    if name_lower in _EMAIL_PROPERTIES:
        return generate_email(entity_name)
    if name_lower in _PHONE_PROPERTIES:
        return generate_phone()
    if name_lower in _URL_PROPERTIES:
        return generate_url(entity_name)
    if name_lower in _ADDRESS_PROPERTIES:
        return generate_address()
    if name_lower == "role" or name_lower == "title":
        return _ROLE_POOL[index % len(_ROLE_POOL)]
    if name_lower == "industry":
        return _INDUSTRY_POOL[index % len(_INDUSTRY_POOL)]
    if name_lower == "latitude" or name_lower == "lat":
        return generate_latitude()
    if name_lower == "longitude" or name_lower in ("lon", "lng"):
        return generate_longitude()

    # Handle by type
    if prop_type in ("string", "str"):
        if name_lower in _DESCRIPTION_PROPERTIES:
            return f"{label} record for {entity_name}. Created as part of the {label.lower()} management workflow."
        if any(id_word in name_lower for id_word in ("_id", "code", "number", "identifier")):
            prefix = label[:3].upper()
            return generate_id(prefix, index)
        return f"{entity_name} - {prop_name.replace('_', ' ').title()}"
    if prop_type in ("integer", "int"):
        if "count" in name_lower or "quantity" in name_lower:
            return random.randint(1, 100)
        if "year" in name_lower:
            return random.choice([2023, 2024, 2025, 2026])
        if "age" in name_lower:
            return random.randint(18, 75)
        return random.randint(10, 10000)
    if prop_type == "float":
        if "price" in name_lower or "cost" in name_lower or "amount" in name_lower or "balance" in name_lower:
            return generate_currency()
        if "weight" in name_lower:
            return round(random.uniform(0.5, 500.0), 2)
        if "rate" in name_lower or "percentage" in name_lower:
            return round(random.uniform(0.01, 0.99), 4)
        return round(random.uniform(1.0, 1000.0), 2)
    if prop_type in ("boolean", "bool"):
        return random.choice([True, False])
    if prop_type == "date":
        return generate_date()
    if prop_type == "datetime":
        return generate_datetime()
    if prop_type == "point":
        return f"POINT({generate_longitude()} {generate_latitude()})"

    return f"{entity_name} {prop_name}"
