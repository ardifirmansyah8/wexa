"""Enrich data/movies.json with real poster URLs from The Movie Database (TMDB).

Posters are looked up by title + year and written back into movies.json as a
`poster_url` field. Re-run the seed afterwards to push them into the graph:

    cd backend
    export TMDB_API_KEY=<your-tmdb-v3-api-key>   # free: themoviedb.org/settings/api
    python -m seed.enrich_posters
    python -m seed.seed

The script is safe to re-run: it only overwrites `poster_url` when TMDB returns
a match, and reports anything it couldn't resolve so you can fix it by hand.

Only stdlib is used (urllib), so there's no extra dependency. TMDB image usage
is subject to their terms; this stores the CDN URL, not the image bytes.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DATA_FILE = Path(__file__).with_name("data") / "movies.json"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def tmdb_search(title: str, year: int, api_key: str) -> str | None:
    params = urllib.parse.urlencode(
        {"api_key": api_key, "query": title, "year": year, "include_adult": "false"}
    )
    req = urllib.request.Request(f"{SEARCH_URL}?{params}", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001 - report and continue
        print(f"  ! request failed for {title!r}: {exc}")
        return None

    results = data.get("results") or []
    if not results:
        return None
    # Prefer an exact-year match, else fall back to the top result.
    best = next((r for r in results if str(r.get("release_date", "")).startswith(str(year))), results[0])
    path = best.get("poster_path")
    return f"{IMAGE_BASE}{path}" if path else None


def main() -> None:
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        sys.exit("Set TMDB_API_KEY first (free key: https://www.themoviedb.org/settings/api).")

    movies = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    resolved, missing = 0, []

    for movie in movies:
        url = tmdb_search(movie["title"], movie["year"], api_key)
        if url:
            movie["poster_url"] = url
            resolved += 1
            print(f"  ✓ {movie['title']} ({movie['year']})")
        else:
            missing.append(f"{movie['title']} ({movie['year']})")
            print(f"  ✗ no poster for {movie['title']} ({movie['year']})")

    # Write back with the same formatting style as the source file.
    DATA_FILE.write_text(json.dumps(movies, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nResolved {resolved}/{len(movies)} posters.")
    if missing:
        print("Missing (edit poster_url by hand if you like):")
        for m in missing:
            print(f"  - {m}")
    print(f"Updated {DATA_FILE}. Now run:  python -m seed.seed")


if __name__ == "__main__":
    main()
