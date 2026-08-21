"""Run every query against the live CognoDB instance and report pass/fail.

Use this immediately after seeding to confirm the whole data layer works
against your instance (it exercises the Neo4j-extension features — CALL{}
subqueries and shortestPath — so you find any incompatibility in seconds):

    cd backend
    python smoke_test.py
"""
from __future__ import annotations

import sys

from app import queries
from app.config import settings
from app.db import DatabaseUnavailable, close_driver, verify_connectivity

GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def check(name: str, fn) -> bool:
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        print(f"{RED}✗ {name}{RESET}\n  {DIM}{type(exc).__name__}: {exc}{RESET}")
        return False
    n = len(result) if isinstance(result, list) else (0 if result is None else 1)
    print(f"{GREEN}✓ {name}{RESET} {DIM}({n} row{'s' if n != 1 else ''}){RESET}")
    return True


def main() -> None:
    if not settings.is_configured:
        sys.exit("Not configured — set NEO4J_URI and NEO4J_PASSWORD in .env first.")
    try:
        verify_connectivity()
    except DatabaseUnavailable as exc:
        sys.exit(f"Cannot reach CognoDB: {exc}")

    print(f"Connected to {settings.neo4j_uri}\nRunning query smoke tests…\n")

    # A movie id and person that exist in the seed data.
    mid = "inception"
    ok = []
    ok.append(check("stats", queries.graph_stats))
    ok.append(check("list_genres", queries.list_genres))
    ok.append(check("list_movies", lambda: queries.list_movies(None, None, 24, 0)))
    ok.append(check("search movies ('dark')", lambda: queries.list_movies("dark", None, 10, 0)))
    ok.append(check("filter by genre ('Drama')", lambda: queries.list_movies(None, "Drama", 10, 0)))
    ok.append(check("get_movie(inception)", lambda: queries.get_movie(mid)))
    ok.append(check("more_like_this [CALL{} subquery]", lambda: queries.more_like_this(mid, 8)))
    ok.append(check("fans_also_liked [collaborative]", lambda: queries.fans_also_liked(mid, 8)))
    ok.append(check("list_users", lambda: queries.list_users(12)))
    users = queries.list_users(1)
    uid = users[0]["id"] if users else "u001"
    ok.append(check(f"recommend_for_user({uid})", lambda: queries.recommend_for_user(uid, 10)))
    ok.append(
        check(
            "six_degrees(DiCaprio↔Hardy) [shortestPath]",
            lambda: queries.shortest_path_between_actors("Leonardo DiCaprio", "Tom Hardy", 6),
        )
    )
    ok.append(
        check(
            "frequent_collaborators(DiCaprio)",
            lambda: queries.frequent_collaborators("Leonardo DiCaprio", 10),
        )
    )
    ok.append(check("get_person(Michael Caine)", lambda: queries.get_person("Michael Caine")))
    ok.append(check("search_people('tom')", lambda: queries.search_people("tom", 8)))

    close_driver()
    passed, total = sum(ok), len(ok)
    print(f"\n{'—' * 40}")
    if passed == total:
        print(f"{GREEN}All {total} checks passed. The data layer is good.{RESET}")
    else:
        print(f"{RED}{total - passed} of {total} checks failed (see above).{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
