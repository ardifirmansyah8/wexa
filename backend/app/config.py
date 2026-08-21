"""Application configuration, read entirely from environment variables.

Secrets (the CognoDB URI and password) are never hard-coded or committed.
Copy `.env.example` to `.env` and fill in your CognoDB connection details.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load a local .env file if present. In production (hosted), real environment
# variables take precedence and the .env file simply won't exist.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    cors_origins: list[str]

    @property
    def is_configured(self) -> bool:
        """True only when the mandatory connection secrets are present."""
        return bool(self.neo4j_uri and self.neo4j_password)


def load_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        neo4j_uri=os.getenv("NEO4J_URI", ""),
        neo4j_user=os.getenv("NEO4J_USER", "cognodb"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
        # CognoDB free tier exposes a single default database.
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
    )


settings = load_settings()
