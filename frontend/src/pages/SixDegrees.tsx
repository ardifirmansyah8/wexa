import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, PersonHit, SixDegreesResult } from "../api";
import { ErrorState, EmptyState } from "../components/states";

// A typeahead actor picker backed by /people/search.
function ActorPicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const [query, setQuery] = useState(value);
  const [hits, setHits] = useState<PersonHit[]>([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => setQuery(value), [value]);

  useEffect(() => {
    if (!query || query === value) {
      setHits([]);
      return;
    }
    let alive = true;
    const t = setTimeout(() => {
      api
        .searchPeople(query)
        .then((r) => alive && setHits(r))
        .catch(() => alive && setHits([]));
    }, 200);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [query, value]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <div className="actor-picker" ref={boxRef}>
      <input
        placeholder={label}
        value={query}
        aria-label={label}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
      />
      {open && hits.length > 0 && (
        <div className="suggestions">
          {hits.map((h) => (
            <button
              key={h.name}
              onClick={() => {
                onChange(h.name);
                setQuery(h.name);
                setOpen(false);
              }}
            >
              <span>{h.name}</span>
              <span className="films">{h.films} films</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SixDegrees() {
  const [params, setParams] = useSearchParams();
  const [a, setA] = useState(params.get("a") ?? "Leonardo DiCaprio");
  const [b, setB] = useState(params.get("b") ?? "Tom Hardy");
  const [result, setResult] = useState<SixDegreesResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const findPath = async (from = a, to = b) => {
    if (!from || !to) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.sixDegrees(from, to);
      setResult(res);
      setParams({ a: from, b: to });
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-run once if arrived with both actors prefilled (e.g. from a cast click).
  useEffect(() => {
    if (params.get("a") && params.get("b")) findPath(params.get("a")!, params.get("b")!);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="container">
      <section className="hero" style={{ paddingBottom: 8 }}>
        <h1>
          <span className="gradient-text">Six degrees</span> of separation
        </h1>
        <p className="lede">
          Pick any two actors and watch the graph find the shortest chain of shared films
          connecting them. This is a variable-length <code>shortestPath</code> traversal — a
          graph-native query with no clean relational equivalent.
        </p>
      </section>

      <div className="picker-row">
        <ActorPicker label="First actor" value={a} onChange={setA} />
        <div className="vs">↔</div>
        <ActorPicker label="Second actor" value={b} onChange={setB} />
      </div>

      <button className="btn" disabled={loading || !a || !b} onClick={() => findPath()}>
        {loading ? "Tracing the graph…" : "Find the connection"}
      </button>

      <div style={{ marginTop: 26 }}>
        {error ? (
          <ErrorState error={error} onRetry={() => findPath()} />
        ) : result === null ? null : !result.connected ? (
          <EmptyState
            emoji="🚫"
            title="No connection found"
            message={`We couldn't link ${a} and ${b} within the dataset. They may act in separate clusters — try another pairing.`}
          />
        ) : (
          <div>
            <div style={{ marginBottom: 14 }}>
              <span className="degrees-badge">
                {result.degrees} degree{result.degrees === 1 ? "" : "s"} of separation
              </span>
            </div>
            <div className="path">
              {result.chain.map((node, i) => (
                <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                  <span className={`path-node ${node.type}`}>
                    {node.type === "movie" ? `🎬 ${node.name}` : node.name}
                  </span>
                  {i < result.chain.length - 1 && <span className="path-arrow">→</span>}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
