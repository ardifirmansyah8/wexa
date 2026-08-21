// Typed client for the MovieGraph API.
//
// In dev, requests go to /api and Vite proxies them to the FastAPI backend.
// In production, set VITE_API_BASE to the deployed backend origin.

const BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api${path}`);
  } catch {
    // Network-level failure (backend down, DNS, CORS preflight).
    throw new ApiError("Could not reach the server.", 0);
  }
  if (!res.ok) {
    let code: string | undefined;
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      code = body.error;
      message = body.message ?? body.detail ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, res.status, code);
  }
  return res.json() as Promise<T>;
}

// ---- Types -----------------------------------------------------------------

export interface MovieSummary {
  id: string;
  title: string;
  year: number;
  rating: number;
  tagline: string;
  genres?: string[];
}

export interface CastMember {
  name: string;
  character: string;
  order: number;
}

export interface MovieDetail extends MovieSummary {
  runtime: number;
  plot: string;
  keywords: string[];
  director: string | null;
  cast: CastMember[];
}

export interface SimilarMovie extends MovieSummary {
  score: number;
  reasons: string[];
}

export interface FanMovie extends MovieSummary {
  fans: number;
  avg_stars: number;
}

export interface RecMovie extends MovieSummary {
  peers: number;
  avg_stars: number;
}

export interface Stats {
  movies: number;
  people: number;
  users: number;
  ratings: number;
}

export interface UserSummary {
  id: string;
  name: string;
  ratings: number;
}

export interface PersonHit {
  name: string;
  films: number;
}

export interface Collaborator {
  name: string;
  shared: number;
  films: string[];
}

export interface PathNode {
  type: "person" | "movie";
  name: string;
  id?: string;
}

export interface SixDegreesResult {
  connected: boolean;
  chain: PathNode[];
  degrees: number | null;
}

export interface MoviePage {
  total: number;
  items: MovieSummary[];
  limit: number;
  skip: number;
}

// ---- Endpoints -------------------------------------------------------------

export const api = {
  health: () => get<{ status: string; configured: boolean; database: boolean }>("/health"),
  stats: () => get<Stats>("/stats"),
  genres: () => get<string[]>("/genres"),
  movies: (params: { search?: string; genre?: string; limit?: number; skip?: number }) => {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    if (params.genre) q.set("genre", params.genre);
    if (params.limit != null) q.set("limit", String(params.limit));
    if (params.skip != null) q.set("skip", String(params.skip));
    return get<MoviePage>(`/movies?${q.toString()}`);
  },
  movie: (id: string) => get<MovieDetail>(`/movies/${encodeURIComponent(id)}`),
  similar: (id: string) => get<SimilarMovie[]>(`/movies/${encodeURIComponent(id)}/similar`),
  fansAlsoLiked: (id: string) => get<FanMovie[]>(`/movies/${encodeURIComponent(id)}/fans-also-liked`),
  users: () => get<UserSummary[]>("/users"),
  recommendations: (userId: string) =>
    get<RecMovie[]>(`/users/${encodeURIComponent(userId)}/recommendations`),
  searchPeople: (q: string) =>
    get<PersonHit[]>(`/people/search?q=${encodeURIComponent(q)}`),
  person: (name: string) => get<{ name: string; acted_in: any[]; directed: any[] }>(
    `/people/${encodeURIComponent(name)}`,
  ),
  collaborators: (name: string) =>
    get<Collaborator[]>(`/people/${encodeURIComponent(name)}/collaborators`),
  sixDegrees: (a: string, b: string) =>
    get<SixDegreesResult>(`/six-degrees?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
};
