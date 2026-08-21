import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../useAsync";
import MovieCard from "../components/MovieCard";
import { Spinner, ErrorState, EmptyState } from "../components/states";
import { Poster } from "../components/Poster";

export default function MovieDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();

  const detail = useAsync(() => api.movie(id), [id]);
  const similar = useAsync(() => api.similar(id), [id]);
  const fans = useAsync(() => api.fansAlsoLiked(id), [id]);

  if (detail.loading) return <Spinner label="Loading movie…" />;
  if (detail.error) return (
    <main className="container">
      <ErrorState error={detail.error} onRetry={detail.reload} />
    </main>
  );

  const m = detail.data!;

  return (
    <main className="container">
      <Link to="/" className="back-link">
        ← Back to browse
      </Link>

      <section className="detail-hero">
        <Poster title={m.title} posterUrl={m.poster_url} className="detail-poster" />
        <div>
          <div className="meta-row" style={{ marginBottom: 6 }}>
            {m.genres?.map((g) => (
              <span key={g} className="pill">
                {g}
              </span>
            ))}
          </div>
          <h1>{m.title}</h1>
          {m.tagline && <div className="tagline">“{m.tagline}”</div>}
          <div className="meta-row">
            <span className="pill rating">★ {m.rating?.toFixed(1)}</span>
            <span>{m.year}</span>
            <span>·</span>
            <span>{m.runtime} min</span>
            {m.director && (
              <>
                <span>·</span>
                <span>
                  Directed by{" "}
                  <Link to="/six-degrees" style={{ color: "var(--accent-3)" }}>
                    {m.director}
                  </Link>
                </span>
              </>
            )}
          </div>
          <p className="plot">{m.plot}</p>
        </div>
      </section>

      {m.cast?.length > 0 && (
        <>
          <div className="section-title">
            <h2>Cast</h2>
            <span className="sub">click an actor to explore Six Degrees</span>
          </div>
          <div className="cast-strip">
            {m.cast.map((c) => (
              <div
                key={c.name}
                className="cast-item"
                role="button"
                tabIndex={0}
                onClick={() => navigate(`/six-degrees?a=${encodeURIComponent(c.name)}`)}
                onKeyDown={(e) => e.key === "Enter" && navigate(`/six-degrees?a=${encodeURIComponent(c.name)}`)}
              >
                <div className="name">{c.name}</div>
                <div className="role">{c.character}</div>
              </div>
            ))}
          </div>
        </>
      )}

      <RecoRow
        title="More like this"
        sub="scored by shared genres, keywords, cast & director — a 2-hop graph traversal"
        state={similar}
        withReasons
      />

      <RecoRow
        title="Fans also liked"
        sub="viewers who rated this 4★+ also loved these (collaborative filtering)"
        state={fans}
      />
    </main>
  );
}

function RecoRow({
  title,
  sub,
  state,
  withReasons,
}: {
  title: string;
  sub: string;
  state: ReturnType<typeof useAsync<any[]>>;
  withReasons?: boolean;
}) {
  return (
    <>
      <div className="section-title">
        <h2>{title}</h2>
        <span className="sub">{sub}</span>
      </div>
      {state.loading ? (
        <Spinner label="Finding connections…" />
      ) : state.error ? (
        <ErrorState error={state.error} onRetry={state.reload} />
      ) : !state.data || state.data.length === 0 ? (
        <EmptyState
          emoji="🎞️"
          title="Nothing to show yet"
          message="Not enough connected data for this title."
        />
      ) : (
        <div className="row-scroll">
          {state.data.map((m: any) => (
            <MovieCard key={m.id} movie={m} reasons={withReasons ? m.reasons : undefined} />
          ))}
        </div>
      )}
    </>
  );
}
