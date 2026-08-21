"""HTTP routes. Thin layer: validate inputs, delegate to `queries`, shape JSON.

Query parameters are validated by FastAPI (types + bounds) before ever reaching
Cypher, and are then passed as driver parameters — so nothing user-supplied is
ever concatenated into a query string.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import queries

router = APIRouter()


@router.get("/stats")
def stats() -> dict[str, object]:
    return queries.graph_stats()


@router.get("/genres")
def genres() -> list[str]:
    return queries.list_genres()


@router.get("/movies")
def movies(
    search: str | None = Query(None, max_length=100),
    genre: str | None = Query(None, max_length=50),
    limit: int = Query(24, ge=1, le=100),
    skip: int = Query(0, ge=0),
) -> dict[str, object]:
    return {
        "total": queries.count_movies(search, genre),
        "items": queries.list_movies(search, genre, limit, skip),
        "limit": limit,
        "skip": skip,
    }


@router.get("/movies/{movie_id}")
def movie_detail(movie_id: str) -> dict[str, object]:
    movie = queries.get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/movies/{movie_id}/similar")
def similar(movie_id: str, limit: int = Query(8, ge=1, le=24)) -> list[dict[str, object]]:
    return queries.more_like_this(movie_id, limit)


@router.get("/movies/{movie_id}/fans-also-liked")
def fans(movie_id: str, limit: int = Query(8, ge=1, le=24)) -> list[dict[str, object]]:
    return queries.fans_also_liked(movie_id, limit)


@router.get("/users")
def users(limit: int = Query(12, ge=1, le=50)) -> list[dict[str, object]]:
    return queries.list_users(limit)


@router.get("/users/{user_id}/recommendations")
def user_recs(user_id: str, limit: int = Query(10, ge=1, le=24)) -> list[dict[str, object]]:
    return queries.recommend_for_user(user_id, limit)


@router.get("/people/search")
def people_search(q: str = Query(..., min_length=1, max_length=60), limit: int = Query(8, ge=1, le=20)) -> list[dict[str, object]]:
    return queries.search_people(q, limit)


@router.get("/people/{name}")
def person_detail(name: str) -> dict[str, object]:
    person = queries.get_person(name)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/people/{name}/collaborators")
def collaborators(name: str, limit: int = Query(10, ge=1, le=25)) -> list[dict[str, object]]:
    return queries.frequent_collaborators(name, limit)


@router.get("/six-degrees")
def six_degrees(
    a: str = Query(..., min_length=1, max_length=60),
    b: str = Query(..., min_length=1, max_length=60),
    max_hops: int = Query(6, ge=1, le=8),
) -> dict[str, object]:
    if a.strip().lower() == b.strip().lower():
        raise HTTPException(status_code=400, detail="Pick two different actors.")
    path = queries.shortest_path_between_actors(a, b, max_hops)
    if path is None:
        return {"connected": False, "chain": [], "degrees": None}
    return {"connected": True, **path}
