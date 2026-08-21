// The dataset ships no image assets (keeping the repo self-contained), so we
// render deterministic gradient "posters" derived from each title. Same title
// always yields the same colours, which reads as intentional design rather
// than a missing-image placeholder.

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
  return {
    background: `linear-gradient(${angle}deg, ${a}, ${b})`,
  };
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
