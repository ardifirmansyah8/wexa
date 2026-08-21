"""Config is read entirely from the environment, with sensible defaults."""
from app.config import load_settings


def test_reads_values_from_env(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt+s://example.databases.cognodb.com")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com, http://b.com")

    s = load_settings()

    assert s.neo4j_uri == "bolt+s://example.databases.cognodb.com"
    assert s.neo4j_password == "secret"
    assert s.neo4j_user == "cognodb"          # default
    assert s.neo4j_database == "neo4j"        # default
    assert s.cors_origins == ["http://a.com", "http://b.com"]
    assert s.is_configured is True


def test_not_configured_without_uri_or_password(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "")
    monkeypatch.setenv("NEO4J_PASSWORD", "")

    assert load_settings().is_configured is False
