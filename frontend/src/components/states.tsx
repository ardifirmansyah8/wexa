import { ApiError } from "../api";

// Loading skeleton for a movie grid — mirrors the real card layout so the
// page doesn't jump when data arrives.
export function GridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="skeleton-grid" aria-hidden>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>
          <div className="skel poster-skel" />
          <div className="skel line" style={{ width: "80%" }} />
          <div className="skel line" style={{ width: "45%" }} />
        </div>
      ))}
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="state">
      <div className="emoji">🎬</div>
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({
  emoji = "🔍",
  title,
  message,
}: {
  emoji?: string;
  title: string;
  message: string;
}) {
  return (
    <div className="state">
      <div className="emoji">{emoji}</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

// Distinguishes an unreachable database (503 / network) from other errors so
// we can show the friendly, actionable message the assignment asks for.
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const isDbDown =
    error instanceof ApiError && (error.status === 503 || error.status === 0 || error.code === "database_unavailable");
  return (
    <div className="state">
      <div className="emoji">{isDbDown ? "🔌" : "⚠️"}</div>
      <h3>{isDbDown ? "The movie graph is offline" : "Something went wrong"}</h3>
      <p>
        {isDbDown
          ? "We couldn't reach CognoDB right now. The free-tier instance may be waking up — give it a moment and retry."
          : error instanceof Error
            ? error.message
            : "An unexpected error occurred."}
      </p>
      {onRetry && (
        <button className="btn ghost" style={{ marginTop: 18 }} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
