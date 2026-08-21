import { useNavigate } from "react-router-dom";
import { MovieSummary } from "../api";
import { Poster } from "./Poster";

interface Props {
  movie: MovieSummary;
  reasons?: string[];
}

// A single clickable movie tile. Optional `reasons` render the "why is this
// recommended" tags used on the detail page's recommendation rows.
export default function MovieCard({ movie, reasons }: Props) {
  const navigate = useNavigate();
  return (
    <div
      className="card"
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/movie/${movie.id}`)}
      onKeyDown={(e) => e.key === "Enter" && navigate(`/movie/${movie.id}`)}
    >
      <Poster title={movie.title} posterUrl={movie.poster_url} className="poster">
        <span className="rating-badge">★ {movie.rating?.toFixed(1)}</span>
        <span className="yr">{movie.year}</span>
      </Poster>
      <div className="card-body">
        <div className="title">{movie.title}</div>
        <div className="meta">{movie.genres?.slice(0, 2).join(" · ") || movie.tagline}</div>
        {reasons && reasons.length > 0 && (
          <div className="reason-tags">
            {reasons.map((r) => (
              <span key={r} className={`reason-tag ${r}`}>
                {r === "cast" ? "shared cast" : r}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
