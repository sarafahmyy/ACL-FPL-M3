
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
load_dotenv()

# ---------- Neo4j CONNECTION ----------

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_driver():
    """
    Create a Neo4j driver using environment variables.  call get_driver() to talk to the DB.
    """
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Small helper to run a Cypher query and return a list of dictionaries.
    """
    if params is None:
        params = {}

    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, params)
        return [record.data() for record in result]

