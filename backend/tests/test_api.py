"""HTTP layer: input validation, error mapping and the graceful 503.

Queries are mocked, so these run offline and assert routing/validation/error
behaviour rather than database results."""
import pytest
from fastapi.testclient import TestClient

from app import main, queries
from app.db import DatabaseUnavailable

client = TestClient(main.app, raise_server_exceptions=False)


def test_movie_detail_404_when_missing(monkeypatch):
    monkeypatch.setattr(queries, "get_movie", lambda _id: None)

    assert client.get("/api/movies/ghost").status_code == 404


def test_movie_detail_ok(monkeypatch):
    monkeypatch.setattr(queries, "get_movie", lambda _id: {"id": "x", "title": "X"})

    res = client.get("/api/movies/x")
    assert res.status_code == 200
    assert res.json()["title"] == "X"


def test_six_degrees_rejects_same_actor():
    res = client.get("/api/six-degrees", params={"a": "Tom", "b": "tom"})
    assert res.status_code == 400


def test_six_degrees_not_connected(monkeypatch):
    monkeypatch.setattr(queries, "shortest_path_between_actors", lambda *a, **k: None)

    res = client.get("/api/six-degrees", params={"a": "A Person", "b": "B Person"})
    assert res.status_code == 200
    assert res.json() == {"connected": False, "chain": [], "degrees": None}


def test_limit_out_of_bounds_is_422():
    # `limit` is capped at 100 by the router's Query(..., le=100).
    assert client.get("/api/movies", params={"limit": 9999}).status_code == 422


def test_database_unavailable_maps_to_503(monkeypatch):
    def boom():
        raise DatabaseUnavailable("down")

    monkeypatch.setattr(queries, "graph_stats", boom)

    res = client.get("/api/stats")
    assert res.status_code == 503
    body = res.json()
    assert body["error"] == "database_unavailable"


class _Configured:
    is_configured = True


def test_health_reports_reachable(monkeypatch):
    monkeypatch.setattr(main, "settings", _Configured())
    monkeypatch.setattr(main, "verify_connectivity", lambda: None)

    body = client.get("/api/health").json()
    assert body == {"status": "ok", "configured": True, "database": True}


def test_health_reports_unreachable(monkeypatch):
    def boom():
        raise DatabaseUnavailable("down")

    monkeypatch.setattr(main, "settings", _Configured())
    monkeypatch.setattr(main, "verify_connectivity", boom)

    body = client.get("/api/health").json()
    assert body["database"] is False
