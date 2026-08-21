import { useState } from "react";
import { api } from "../api";
import { useAsync, useDebounced } from "../useAsync";
import MovieCard from "../components/MovieCard";
import { GridSkeleton, EmptyState, ErrorState } from "../components/states";

const PAGE_SIZE = 24;

export default function Home() {
  const [search, setSearch] = useState("");
  const [genre, setGenre] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const debouncedSearch = useDebounced(search, 300);

  const stats = useAsync(() => api.stats(), []);
  const genres = useAsync(() => api.genres(), []);
  const movies = useAsync(
    () =>
      api.movies({
        search: debouncedSearch || undefined,
        genre: genre || undefined,
        limit: PAGE_SIZE,
        skip: page * PAGE_SIZE,
      }),
    [debouncedSearch, genre, page],
  );

  const resetTo = (fn: () => void) => {
    fn();
    setPage(0);
  };

  const total = movies.data?.total ?? 0;
  const pageCount = Math.ceil(total / PAGE_SIZE);

  return (
    <main className="container">
      <section className="hero">
        <h1>
          Explore films through their <span className="gradient-text">connections</span>
        </h1>
        <p className="lede">
          A movie recommender that thinks in relationships, not rows. Every suggestion is a
          path through a graph of shared cast, crew, genres and the taste of other viewers —
          powered by CognoDB.
        </p>
        {stats.data && (
          <div className="stats-row">
            <Stat num={stats.data.movies} label="Movies" />
            <Stat num={stats.data.people} label="Cast & crew" />
            <Stat num={stats.data.users} label="Viewers" />
            <Stat num={stats.data.ratings} label="Ratings" />
          </div>
        )}
      </section>

      <div className="toolbar">
        <div className="search">
          <span className="icon">⌕</span>
          <input
            placeholder="Search movies by title…"
            value={search}
            onChange={(e) => resetTo(() => setSearch(e.target.value))}
            aria-label="Search movies"
          />
        </div>
        <div className="chips">
          <button
            className={`chip ${genre === null ? "active" : ""}`}
            onClick={() => resetTo(() => setGenre(null))}
          >
            All
          </button>
          {genres.data?.slice(0, 8).map((g) => (
            <button
              key={g}
              className={`chip ${genre === g ? "active" : ""}`}
              onClick={() => resetTo(() => setGenre(genre === g ? null : g))}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {movies.loading ? (
        <GridSkeleton count={12} />
      ) : movies.error ? (
        <ErrorState error={movies.error} onRetry={movies.reload} />
      ) : total === 0 ? (
        <EmptyState
          title="No movies match"
          message="Try a different title or clear the genre filter."
        />
      ) : (
        <>
          <div className="grid">
            {movies.data!.items.map((m) => (
              <MovieCard key={m.id} movie={m} />
            ))}
          </div>
          {pageCount > 1 && (
            <div style={{ display: "flex", gap: 12, justifyContent: "center", alignItems: "center", margin: "28px 0 10px" }}>
              <button className="btn ghost" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                ← Prev
              </button>
              <span style={{ color: "var(--text-faint)", fontSize: 14 }}>
                Page {page + 1} of {pageCount}
              </span>
              <button
                className="btn ghost"
                disabled={page >= pageCount - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </main>
  );
}

function Stat({ num, label }: { num: number; label: string }) {
  return (
    <div className="stat">
      <div className="num">{num.toLocaleString()}</div>
      <div className="label">{label}</div>
    </div>
  );
}
