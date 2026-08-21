"""All Cypher used by the API, kept in one place and fully parameterised.

Every function returns plain Python data (lists/dicts) so the routers can hand
them straight to Pydantic/JSON. No Cypher is ever built by string concatenation
with user input — values arrive via the driver's parameter map ($name).
"""
from __future__ import annotations

from typing import Any

from .db import run_query


# ---------------------------------------------------------------------------
# Browse / search
# ---------------------------------------------------------------------------

def list_movies(search: str | None, genre: str | None, limit: int, skip: int) -> list[dict[str, Any]]:
    """Paginated movie grid with optional case-insensitive title search and
    genre filter. Genre filtering is a 1-hop pattern, trivial in a graph."""
    cypher = """
    MATCH (m:Movie)
    WHERE ($search IS NULL OR toLower(m.title) CONTAINS toLower($search))
    OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
    WITH m, collect(DISTINCT g.name) AS genres
    WHERE $genre IS NULL OR $genre IN genres
    RETURN m.id AS id, m.title AS title, m.year AS year,
           m.rating AS rating, m.tagline AS tagline, genres
    ORDER BY m.rating DESC, m.title ASC
    SKIP $skip LIMIT $limit
    """
    return run_query(cypher, {"search": search, "genre": genre, "limit": limit, "skip": skip})


def count_movies(search: str | None, genre: str | None) -> int:
    cypher = """
    MATCH (m:Movie)
    WHERE ($search IS NULL OR toLower(m.title) CONTAINS toLower($search))
    OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
    WITH m, collect(DISTINCT g.name) AS genres
    WHERE $genre IS NULL OR $genre IN genres
    RETURN count(m) AS total
    """
    rows = run_query(cypher, {"search": search, "genre": genre})
    return rows[0]["total"] if rows else 0


def list_genres() -> list[str]:
    cypher = """
    MATCH (g:Genre)<-[:IN_GENRE]-(m:Movie)
    RETURN g.name AS name, count(m) AS n
    ORDER BY n DESC, name ASC
    """
    return [r["name"] for r in run_query(cypher)]


# ---------------------------------------------------------------------------
# Movie detail
# ---------------------------------------------------------------------------

def get_movie(movie_id: str) -> dict[str, Any] | None:
    """Full detail for one movie: properties, genres, keywords, director and
    ordered cast. Assembling this from a graph is a handful of pattern matches;
    in SQL it is several joins across movie/person/role/genre tables."""
    cypher = """
    MATCH (m:Movie {id: $id})
    OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
    OPTIONAL MATCH (m)-[:HAS_KEYWORD]->(k:Keyword)
    OPTIONAL MATCH (d:Person)-[:DIRECTED]->(m)
    OPTIONAL MATCH (a:Person)-[r:ACTED_IN]->(m)
    WITH m,
         collect(DISTINCT g.name) AS genres,
         collect(DISTINCT k.name) AS keywords,
         collect(DISTINCT d.name) AS directors,
         collect(DISTINCT {name: a.name, character: r.character, order: r.order}) AS cast
    RETURN m.id AS id, m.title AS title, m.year AS year, m.runtime AS runtime,
           m.rating AS rating, m.tagline AS tagline, m.plot AS plot,
           genres, keywords, directors,
           [c IN cast WHERE c.name IS NOT NULL] AS cast
    """
    rows = run_query(cypher, {"id": movie_id})
    if not rows:
        return None
    movie = rows[0]
    movie["cast"] = sorted(movie["cast"], key=lambda c: c.get("order") or 999)
    movie["director"] = movie["directors"][0] if movie["directors"] else None
    return movie


# ---------------------------------------------------------------------------
# Recommendations (the graph's reason to exist)
# ---------------------------------------------------------------------------

def more_like_this(movie_id: str, limit: int) -> list[dict[str, Any]]:
    """Content-based recommendation.

    A 2-hop traversal out of the seed movie through shared genres, keywords,
    cast and director, scoring each neighbouring movie by how many connections
    it shares (weighted). This is the query a relational schema finds awkward:
    it would need several UNIONed self-joins across junction tables plus a
    manual GROUP BY to reproduce the weighted overlap the graph expresses
    directly as a set of patterns.
    """
    # Gather neighbours through each kind of shared attribute into its own list
    # (each `collect` collapses the row fan-out back to a single row, so the
    # OPTIONAL MATCHes chain cleanly), then build one weighted, tagged list with
    # comprehensions and aggregate per neighbour. `collect` skips nulls, so a
    # movie with no shared keywords simply contributes an empty list.
    #
    # This deliberately avoids a `UNION` inside a correlated `CALL {}` subquery:
    # CognoDB evaluates that to zero rows. The scoring is unchanged — a film
    # sharing three genres appears three times in `gs` and so scores 3x.
    cypher = """
    MATCH (m:Movie {id: $id})
    OPTIONAL MATCH (m)-[:IN_GENRE]->(:Genre)<-[:IN_GENRE]-(a:Movie)
    WHERE a <> m
    WITH m, collect(a) AS gs
    OPTIONAL MATCH (m)-[:HAS_KEYWORD]->(:Keyword)<-[:HAS_KEYWORD]-(b:Movie)
    WHERE b <> m
    WITH m, gs, collect(b) AS ks
    OPTIONAL MATCH (m)<-[:ACTED_IN]-(:Person)-[:ACTED_IN]->(c:Movie)
    WHERE c <> m
    WITH m, gs, ks, collect(c) AS cs
    OPTIONAL MATCH (m)<-[:DIRECTED]-(:Person)-[:DIRECTED]->(d:Movie)
    WHERE d <> m
    WITH gs, ks, cs, collect(d) AS ds
    WITH [x IN gs | {rec: x, w: 2, via: 'genre'}]
       + [x IN ks | {rec: x, w: 4, via: 'keyword'}]
       + [x IN cs | {rec: x, w: 3, via: 'cast'}]
       + [x IN ds | {rec: x, w: 5, via: 'director'}] AS acc
    UNWIND acc AS hit
    WITH hit.rec AS rec, hit.w AS w, hit.via AS via
    WITH rec, sum(w) AS score, collect(DISTINCT via) AS reasons
    RETURN rec.id AS id, rec.title AS title, rec.year AS year,
           rec.rating AS rating, rec.tagline AS tagline,
           score, reasons
    ORDER BY score DESC, rec.rating DESC
    LIMIT $limit
    """
    return run_query(cypher, {"id": movie_id, "limit": limit})


def fans_also_liked(movie_id: str, limit: int) -> list[dict[str, Any]]:
    """Collaborative filtering via a classic bipartite traversal.

    Movie <-[:RATED]- User -[:RATED]-> other Movie, keeping only high ratings
    on both ends. The result: 'people who loved this movie also loved these.'
    This is the textbook example of a query that is one clean pattern in Cypher
    but an expensive multi-join self-referencing aggregation in SQL.
    """
    cypher = """
    MATCH (m:Movie {id: $id})<-[r1:RATED]-(u:User)-[r2:RATED]->(rec:Movie)
    WHERE r1.stars >= 4 AND r2.stars >= 4 AND rec.id <> m.id
    WITH rec, count(DISTINCT u) AS fans, avg(r2.stars) AS avg_stars
    RETURN rec.id AS id, rec.title AS title, rec.year AS year,
           rec.rating AS rating, rec.tagline AS tagline,
           fans, round(avg_stars * 100.0) / 100.0 AS avg_stars
    ORDER BY fans DESC, avg_stars DESC
    LIMIT $limit
    """
    return run_query(cypher, {"id": movie_id, "limit": limit})


def recommend_for_user(user_id: str, limit: int) -> list[dict[str, Any]]:
    """Personalised recommendations for a user.

    Find peers who rated the same movies highly, then surface the movies those
    peers loved that the target user has not yet seen. A multi-hop
    User -> Movie <- peer -> Movie traversal with de-duplication against the
    user's own history.
    """
    cypher = """
    MATCH (me:User {id: $id})-[r:RATED]->(seen:Movie)
    WHERE r.stars >= 4
    WITH me, collect(DISTINCT seen) AS liked
    MATCH (me)-[r1:RATED]->(shared:Movie)<-[r2:RATED]-(peer:User)
    WHERE r1.stars >= 4 AND r2.stars >= 4 AND peer <> me
    MATCH (peer)-[r3:RATED]->(rec:Movie)
    WHERE r3.stars >= 4 AND NOT rec IN liked
    WITH rec, count(DISTINCT peer) AS peers, avg(r3.stars) AS avg_stars
    RETURN rec.id AS id, rec.title AS title, rec.year AS year,
           rec.rating AS rating, rec.tagline AS tagline,
           peers, round(avg_stars * 100.0) / 100.0 AS avg_stars
    ORDER BY peers DESC, avg_stars DESC
    LIMIT $limit
    """
    return run_query(cypher, {"id": user_id, "limit": limit})


# ---------------------------------------------------------------------------
# Six degrees / people
# ---------------------------------------------------------------------------

def shortest_path_between_actors(name_a: str, name_b: str, max_hops: int) -> dict[str, Any] | None:
    """The 'six degrees' feature: the shortest chain of shared films connecting
    two actors. Variable-length shortestPath is a graph-native primitive with no
    natural relational equivalent — in SQL it means recursive CTEs of unbounded
    join depth. Here it is a single pattern."""
    cypher = f"""
    MATCH (a:Person {{name: $a}}), (b:Person {{name: $b}})
    MATCH p = shortestPath((a)-[:ACTED_IN*..{max_hops * 2}]-(b))
    RETURN [n IN nodes(p) |
             CASE WHEN n:Person THEN {{type: 'person', name: n.name}}
                  ELSE {{type: 'movie', name: n.title, id: n.id}} END] AS chain,
           (length(p) / 2) AS degrees
    """
    # max_hops is a small integer we control (validated in the router), never
    # user free-text, so interpolating it into the variable-length bound is safe.
    rows = run_query(cypher, {"a": name_a, "b": name_b})
    return rows[0] if rows else None


def frequent_collaborators(person_name: str, limit: int) -> list[dict[str, Any]]:
    """People who have appeared alongside the given actor most often, with the
    shared films listed. A self-join through the Movie node."""
    cypher = """
    MATCH (p:Person {name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(co:Person)
    WHERE co <> p
    WITH co, collect(DISTINCT m.title) AS films
    RETURN co.name AS name, size(films) AS shared, films
    ORDER BY shared DESC, name ASC
    LIMIT $limit
    """
    return run_query(cypher, {"name": person_name, "limit": limit})


def get_person(person_name: str) -> dict[str, Any] | None:
    """A person's filmography split into acting and directing credits."""
    cypher = """
    MATCH (p:Person {name: $name})
    OPTIONAL MATCH (p)-[r:ACTED_IN]->(am:Movie)
    OPTIONAL MATCH (p)-[:DIRECTED]->(dm:Movie)
    WITH p,
         collect(DISTINCT {id: am.id, title: am.title, year: am.year, character: r.character}) AS acted,
         collect(DISTINCT {id: dm.id, title: dm.title, year: dm.year}) AS directed
    RETURN p.name AS name,
           [a IN acted WHERE a.id IS NOT NULL] AS acted_in,
           [d IN directed WHERE d.id IS NOT NULL] AS directed
    """
    rows = run_query(cypher, {"name": person_name})
    if not rows:
        return None
    person = rows[0]
    if not person["acted_in"] and not person["directed"]:
        return None
    person["acted_in"].sort(key=lambda m: m.get("year") or 0, reverse=True)
    person["directed"].sort(key=lambda m: m.get("year") or 0, reverse=True)
    return person


def search_people(query: str, limit: int) -> list[dict[str, Any]]:
    """Typeahead for the six-degrees picker."""
    cypher = """
    MATCH (p:Person)
    WHERE toLower(p.name) CONTAINS toLower($q)
    OPTIONAL MATCH (p)-[:ACTED_IN]->(m:Movie)
    RETURN p.name AS name, count(m) AS films
    ORDER BY films DESC, name ASC
    LIMIT $limit
    """
    return run_query(cypher, {"q": query, "limit": limit})


# ---------------------------------------------------------------------------
# Stats (landing page)
# ---------------------------------------------------------------------------

def graph_stats() -> dict[str, Any]:
    cypher = """
    MATCH (m:Movie) WITH count(m) AS movies
    MATCH (p:Person) WITH movies, count(p) AS people
    MATCH (u:User) WITH movies, people, count(u) AS users
    MATCH (:User)-[r:RATED]->(:Movie) WITH movies, people, users, count(r) AS ratings
    RETURN movies, people, users, ratings
    """
    rows = run_query(cypher)
    return rows[0] if rows else {"movies": 0, "people": 0, "users": 0, "ratings": 0}


def list_users(limit: int) -> list[dict[str, Any]]:
    """Sample users for the 'recommend for you' demo picker."""
    cypher = """
    MATCH (u:User)-[r:RATED]->(:Movie)
    RETURN u.id AS id, u.name AS name, count(r) AS ratings
    ORDER BY ratings DESC, u.name ASC
    LIMIT $limit
    """
    return run_query(cypher, {"limit": limit})
