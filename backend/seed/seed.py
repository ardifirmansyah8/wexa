"""Seed the CognoDB graph from `data/movies.json`.

Run once after provisioning your instance:

    cd backend
    python -m seed.seed

The script is idempotent: it uses MERGE so re-running will not create
duplicates. It also generates synthetic Users with taste-clustered RATED
relationships so the collaborative-filtering queries have signal to work with.

Randomness is seeded deterministically so everyone gets the same demo graph.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

# Allow `python -m seed.seed` from the backend dir and `python seed/seed.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.db import DatabaseUnavailable, close_driver, verify_connectivity, write_session  # noqa: E402

DATA_FILE = Path(__file__).with_name("data") / "movies.json"
RANDOM_SEED = 42

# Named taste profiles -> the genres those viewers gravitate to. Users are
# assigned a profile, then rate movies whose genres overlap their taste highly
# and everything else lower, which produces realistic collaborative signal.
TASTE_PROFILES = {
    "Nolan-head": ["Science Fiction", "Thriller", "Mystery"],
    "Comic-book fan": ["Action", "Adventure"],
    "Awards-season buff": ["Drama", "History", "Biography"],
    "Crime & mob lover": ["Crime", "Drama"],
    "Rom-com & musical": ["Romance", "Comedy", "Music"],
    "Sci-fi explorer": ["Science Fiction", "Adventure"],
}

FIRST_NAMES = [
    "Ava", "Liam", "Noah", "Maya", "Kai", "Zoe", "Omar", "Nina", "Leo", "Isla",
    "Ravi", "Mila", "Theo", "Aisha", "Ben", "Sofia", "Diego", "Yuki", "Lena", "Sam",
    "Priya", "Marcus", "Elena", "Jonas", "Amara", "Felix", "Nadia", "Ivan", "Chloe", "Hugo",
]


def load_movies() -> list[dict]:
    with DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def create_schema(session) -> None:
    """Uniqueness constraints double as indexes and guard against dupes."""
    statements = [
        "CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
        "CREATE CONSTRAINT keyword_name IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
        "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    ]
    for stmt in statements:
        session.run(stmt)


def load_movie(session, movie: dict) -> None:
    """Idempotently MERGE one movie and all of its relationships.

    Everything is parameterised: the movie dict, cast list, genres and keywords
    are passed as $params and UNWOUND inside Cypher — no string building.
    """
    session.run(
        """
        MERGE (m:Movie {id: $id})
        SET m.title = $title, m.year = $year, m.runtime = $runtime,
            m.rating = $rating, m.tagline = $tagline, m.plot = $plot,
            m.poster_url = $poster_url

        MERGE (d:Person {name: $director})
        MERGE (d)-[:DIRECTED]->(m)

        WITH m
        UNWIND $genres AS gname
          MERGE (g:Genre {name: gname})
          MERGE (m)-[:IN_GENRE]->(g)

        WITH DISTINCT m
        UNWIND $keywords AS kname
          MERGE (k:Keyword {name: kname})
          MERGE (m)-[:HAS_KEYWORD]->(k)

        WITH DISTINCT m
        UNWIND $cast AS c
          MERGE (a:Person {name: c.name})
          MERGE (a)-[r:ACTED_IN]->(m)
          SET r.character = c.character, r.order = c.order
        """,
        {
            "id": movie["id"],
            "title": movie["title"],
            "year": movie["year"],
            "runtime": movie["runtime"],
            "rating": movie["rating"],
            "tagline": movie["tagline"],
            "plot": movie["plot"],
            "poster_url": movie.get("poster_url"),
            "director": movie["director"],
            "genres": movie["genres"],
            "keywords": movie["keywords"],
            "cast": movie["cast"],
        },
    )


def genres_of(movie: dict) -> set[str]:
    return set(movie["genres"])


def generate_users_and_ratings(session, movies: list[dict], n_users: int = 30) -> None:
    """Create N users, each with a taste profile, and RATED edges.

    A user rates a random subset of movies. Movies matching their taste get
    4-5 stars; off-taste movies get 2-4. This clustering is what makes
    'fans also liked' and 'recommend for you' return sensible results.
    """
    rng = random.Random(RANDOM_SEED)
    profile_names = list(TASTE_PROFILES.keys())

    users = []
    for i in range(n_users):
        name = FIRST_NAMES[i % len(FIRST_NAMES)]
        suffix = "" if i < len(FIRST_NAMES) else f" {i // len(FIRST_NAMES) + 1}"
        users.append(
            {
                "id": f"u{i + 1:03d}",
                "name": f"{name}{suffix}",
                "profile": profile_names[i % len(profile_names)],
            }
        )

    ratings_payload = []
    for user in users:
        liked_genres = set(TASTE_PROFILES[user["profile"]])
        # Each user rates between 40% and 70% of the catalogue.
        k = rng.randint(int(len(movies) * 0.4), int(len(movies) * 0.7))
        for movie in rng.sample(movies, k):
            overlap = liked_genres & genres_of(movie)
            if overlap:
                stars = rng.choice([4, 5, 5])
            else:
                stars = rng.choice([2, 3, 3, 4])
            ratings_payload.append(
                {"uid": user["id"], "mid": movie["id"], "stars": stars}
            )

    # Create users.
    session.run(
        """
        UNWIND $users AS u
        MERGE (x:User {id: u.id})
        SET x.name = u.name, x.taste = u.profile
        """,
        {"users": users},
    )

    # Create ratings in one parameterised UNWIND.
    session.run(
        """
        UNWIND $ratings AS row
        MATCH (u:User {id: row.uid})
        MATCH (m:Movie {id: row.mid})
        MERGE (u)-[r:RATED]->(m)
        SET r.stars = row.stars
        """,
        {"ratings": ratings_payload},
    )
    print(f"  · {len(users)} users, {len(ratings_payload)} ratings")


def main() -> None:
    if not settings.is_configured:
        sys.exit(
            "CognoDB is not configured. Copy .env.example to .env and set "
            "NEO4J_URI and NEO4J_PASSWORD first."
        )

    print(f"Connecting to {settings.neo4j_uri} ...")
    try:
        verify_connectivity()
    except DatabaseUnavailable as exc:
        sys.exit(f"Could not reach CognoDB: {exc}")

    movies = load_movies()
    print(f"Loaded {len(movies)} movies from {DATA_FILE.name}")

    with write_session() as session:
        print("Creating constraints / indexes ...")
        create_schema(session)

        print("Loading movies, people, genres, keywords ...")
        for movie in movies:
            load_movie(session, movie)

        print("Generating users and ratings ...")
        generate_users_and_ratings(session, movies)

    close_driver()
    print("Done. The graph is ready to explore.")


if __name__ == "__main__":
    main()
