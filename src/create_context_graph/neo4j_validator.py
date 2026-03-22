"""Neo4j connection validation."""

from __future__ import annotations

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError


def validate_connection(uri: str, username: str, password: str) -> tuple[bool, str]:
    """Test Neo4j connection and return (success, message)."""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        # Quick test query
        with driver.session() as session:
            result = session.run("RETURN 1 AS n")
            result.single()
        driver.close()
        return True, "Connected successfully"
    except AuthError:
        return False, "Authentication failed. Check username and password."
    except ServiceUnavailable:
        return False, f"Cannot connect to Neo4j at {uri}. Is it running?"
    except Exception as e:
        return False, f"Connection error: {e}"
