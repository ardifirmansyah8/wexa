"""Query helpers do their post-processing correctly. The Cypher itself is
exercised against a live instance by smoke_test.py; here we mock `run_query`
and assert the Python-side shaping (sorting, defaults, null-filtering)."""
from app import queries


def test_get_movie_sorts_cast_and_picks_director(monkeypatch):
    row = {
        "id": "inception",
        "title": "Inception",
        "directors": ["Christopher Nolan"],
        "genres": ["Science Fiction"],
        "keywords": ["dreams"],
        "cast": [
            {"name": "C", "character": "c", "order": 3},
            {"name": "A", "character": "a", "order": 1},
            {"name": "B", "character": "b", "order": 2},
        ],
    }
    monkeypatch.setattr(queries, "run_query", lambda *a, **k: [row])

    movie = queries.get_movie("inception")

    assert [c["order"] for c in movie["cast"]] == [1, 2, 3]  # sorted by billing
    assert movie["director"] == "Christopher Nolan"          # first of directors


def test_get_movie_handles_missing_director(monkeypatch):
    monkeypatch.setattr(
        queries,
        "run_query",
        lambda *a, **k: [{"id": "x", "title": "X", "directors": [], "cast": []}],
    )

    assert queries.get_movie("x")["director"] is None


def test_get_movie_returns_none_when_absent(monkeypatch):
    monkeypatch.setattr(queries, "run_query", lambda *a, **k: [])

    assert queries.get_movie("nope") is None


def test_get_person_none_when_no_credits(monkeypatch):
    monkeypatch.setattr(
        queries,
        "run_query",
        lambda *a, **k: [{"name": "Nobody", "acted_in": [], "directed": []}],
    )

    assert queries.get_person("Nobody") is None


def test_graph_stats_defaults_to_zeroes(monkeypatch):
    monkeypatch.setattr(queries, "run_query", lambda *a, **k: [])

    assert queries.graph_stats() == {"movies": 0, "people": 0, "users": 0, "ratings": 0}
