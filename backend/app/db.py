"""Neo4j/Bolt driver lifecycle and a thin query helper.

CognoDB speaks openCypher over Bolt, so we use the official `neo4j` driver
pointed at a `bolt+s://` URI. This module owns a single shared driver
(the driver manages its own connection pool) and translates driver-level
failures into a small, typed error the API layer can turn into clean HTTP
responses.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

import certifi
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

from .config import settings

logger = logging.getLogger("moviegraph.db")

# The `bolt+s://` scheme verifies the server certificate against the system CA
# store via ssl.create_default_context(). Some Python installs (notably the
# macOS python.org build) ship without a usable CA bundle, which makes even a
# valid Let's Encrypt certificate fail to verify. Point the SSL layer at
# certifi's bundle so TLS verification works consistently across dev machines
# and deploy hosts. We only set it if the operator hasn't chosen their own.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())


class DatabaseUnavailable(RuntimeError):
    """Raised when CognoDB cannot be reached or authenticated against.

    The API layer maps this to HTTP 503 so the frontend can show a friendly
    "database unreachable" state instead of a raw stack trace.
    """


_driver: Driver | None = None


def get_driver() -> Driver:
    """Return the shared driver, creating it lazily on first use."""
    global _driver
    if _driver is None:
        if not settings.is_configured:
            raise DatabaseUnavailable(
                "CognoDB connection is not configured. Set NEO4J_URI and "
                "NEO4J_PASSWORD (see .env.example)."
            )
        try:
            _driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                # Fail fast rather than hanging the request when the free-tier
                # instance is asleep or the network is down.
                connection_acquisition_timeout=15,
                max_connection_lifetime=3600,
            )
        except Exception as exc:  # pragma: no cover - construction rarely fails
            raise DatabaseUnavailable(f"Could not initialise driver: {exc}") from exc
    return _driver


def verify_connectivity() -> None:
    """Ping CognoDB. Raises DatabaseUnavailable on any connection problem."""
    try:
        get_driver().verify_connectivity()
    except (ServiceUnavailable, AuthError, OSError) as exc:
        raise DatabaseUnavailable(str(exc)) from exc


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_query(cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Execute a parameterised read query and return a list of plain dicts.

    Parameters are always passed via the driver's `params` argument — never
    string-interpolated into the Cypher — which keeps queries safe and cacheable.
    """
    params = params or {}
    try:
        driver = get_driver()
        with driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]
    except (ServiceUnavailable, AuthError, OSError) as exc:
        logger.warning("CognoDB unreachable: %s", exc)
        raise DatabaseUnavailable(str(exc)) from exc
    except Neo4jError as exc:
        # A genuine query/logic error — surface it rather than masking it.
        logger.error("Cypher error: %s", exc)
        raise


@contextmanager
def write_session() -> Iterator[Any]:
    """Session context manager used by the seed script for write transactions."""
    driver = get_driver()
    with driver.session(database=settings.neo4j_database) as session:
        yield session
