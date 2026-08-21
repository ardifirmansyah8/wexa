import { useState } from "react";
import { api } from "../api";
import { useAsync } from "../useAsync";
import MovieCard from "../components/MovieCard";
import { GridSkeleton, EmptyState, ErrorState, Spinner } from "../components/states";

export default function ForYou() {
  const users = useAsync(() => api.users(), []);
  const [userId, setUserId] = useState<string | null>(null);

  // Default to the first user once the list loads.
  const activeId = userId ?? users.data?.[0]?.id ?? null;
  const activeUser = users.data?.find((u) => u.id === activeId);

  const recs = useAsync(
    () => (activeId ? api.recommendations(activeId) : Promise.resolve([])),
    [activeId],
  );

  return (
    <main className="container">
      <section className="hero" style={{ paddingBottom: 8 }}>
        <h1>
          Made <span className="gradient-text">for you</span>
        </h1>
        <p className="lede">
          Pick a viewer profile. We find the people whose taste overlaps theirs, then surface
          the films those neighbours loved that this viewer hasn't seen — a multi-hop
          traversal across the ratings graph, the heart of collaborative filtering.
        </p>
      </section>

      {users.loading ? (
        <Spinner label="Loading viewers…" />
      ) : users.error ? (
        <ErrorState error={users.error} onRetry={users.reload} />
      ) : (
        <>
          <div className="toolbar">
            <label style={{ color: "var(--text-dim)", fontSize: 14, fontWeight: 600 }}>
              Viewer
            </label>
            <select
              className="select"
              value={activeId ?? ""}
              onChange={(e) => setUserId(e.target.value)}
            >
              {users.data!.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} — {u.ratings} ratings
                </option>
              ))}
            </select>
            {activeUser && (
              <span style={{ color: "var(--text-faint)", fontSize: 13 }}>
                Recommending from {activeUser.ratings} rated films
              </span>
            )}
          </div>

          <div className="section-title">
            <h2>Recommended for {activeUser?.name}</h2>
            <span className="sub">ranked by how many like-minded viewers loved each title</span>
          </div>

          {recs.loading ? (
            <GridSkeleton count={8} />
          ) : recs.error ? (
            <ErrorState error={recs.error} onRetry={recs.reload} />
          ) : !recs.data || recs.data.length === 0 ? (
            <EmptyState
              emoji="🍿"
              title="No fresh picks"
              message="This viewer's neighbours haven't rated anything new. Try another profile."
            />
          ) : (
            <div className="grid">
              {recs.data.map((m) => (
                <MovieCard key={m.id} movie={m} />
              ))}
            </div>
          )}
        </>
      )}
    </main>
  );
}
