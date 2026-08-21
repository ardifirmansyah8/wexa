import { useState, ReactNode } from "react";

// Posters render a real image when a `posterUrl` is available and gracefully
// fall back to a deterministic gradient + initials otherwise (missing data, a
// broken URL, or a slow network). Same title always yields the same gradient,
// so the fallback reads as intentional design rather than a missing asset.

const PALETTES: [string, string][] = [
  ["#7c5cff", "#3a2a8c"],
  ["#ffb703", "#b25900"],
  ["#38bdf8", "#0e5a8a"],
  ["#f472b6", "#83235f"],
  ["#34d399", "#0f6a4d"],
  ["#f97316", "#9a3412"],
  ["#a78bfa", "#5b3aa8"],
  ["#22d3ee", "#0e6b7a"],
];

function hash(str: string): number {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function posterStyle(title: string): React.CSSProperties {
  const [a, b] = PALETTES[hash(title) % PALETTES.length];
  const angle = 120 + (hash(title) % 90);
  return { background: `linear-gradient(${angle}deg, ${a}, ${b})` };
}

export function initials(title: string): string {
  return title
    .replace(/[^a-zA-Z0-9 ]/g, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
}

interface PosterProps {
  title: string;
  posterUrl?: string | null;
  className?: string;
  /** Overlays (rating badge, year, …) rendered on top of the poster. */
  children?: ReactNode;
}

export function Poster({ title, posterUrl, className, children }: PosterProps) {
  const [failed, setFailed] = useState(false);
  const showImage = Boolean(posterUrl) && !failed;

  return (
    <div className={className} style={showImage ? undefined : posterStyle(title)}>
      {showImage ? (
        <img
          className="poster-img"
          src={posterUrl as string}
          alt={`${title} poster`}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="poster-initials" aria-hidden>
          {initials(title)}
        </span>
      )}
      {children}
    </div>
  );
}
