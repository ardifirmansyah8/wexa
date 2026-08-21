"""`run_query` returns plain dicts and translates driver failures into a
typed `DatabaseUnavailable` the API layer can turn into a clean 503."""
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from neo4j.exceptions import ServiceUnavailable

from app import db


class _Record:
    def __init__(self, data):
        self._data = data

    def data(self):
        return self._data


def _fake_driver(records=None, raise_exc=None):
    """A driver whose session().run() yields the given records or raises."""
    session = MagicMock()
    if raise_exc is not None:
        session.run.side_effect = raise_exc
    else:
        session.run.return_value = [_Record(r) for r in (records or [])]

    @contextmanager
    def _session(**_kwargs):
        yield session

    driver = MagicMock()
    driver.session = _session
    return driver


def test_run_query_returns_dicts(monkeypatch):
    monkeypatch.setattr(db, "get_driver", lambda: _fake_driver(records=[{"n": 1}, {"n": 2}]))

    assert db.run_query("RETURN 1") == [{"n": 1}, {"n": 2}]


def test_run_query_translates_connection_failure(monkeypatch):
    monkeypatch.setattr(
        db, "get_driver", lambda: _fake_driver(raise_exc=ServiceUnavailable("down"))
    )

    with pytest.raises(db.DatabaseUnavailable):
        db.run_query("RETURN 1")


def test_get_driver_raises_when_unconfigured(monkeypatch):
    class _Unconfigured:
        is_configured = False

    monkeypatch.setattr(db, "_driver", None)
    monkeypatch.setattr(db, "settings", _Unconfigured())

    with pytest.raises(db.DatabaseUnavailable):
        db.get_driver()
