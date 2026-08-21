import { useEffect, useState } from "react";
import { Routes, Route, NavLink, Link } from "react-router-dom";
import { api } from "./api";
import Home from "./pages/Home";
import MovieDetailPage from "./pages/MovieDetail";
import SixDegrees from "./pages/SixDegrees";
import ForYou from "./pages/ForYou";

function Nav() {
  return (
    <nav className="nav">
      <div className="container nav-inner">
        <Link to="/" className="brand">
          <span className="dot" />
          MovieGraph
        </Link>
        <div className="nav-links">
          <NavLink to="/" end>
            Browse
          </NavLink>
          <NavLink to="/six-degrees">Six Degrees</NavLink>
          <NavLink to="/for-you">For You</NavLink>
        </div>
      </div>
    </nav>
  );
}

// Global, dismissible banner shown when the API reports the database is
// unreachable or unconfigured — so every page degrades gracefully.
function HealthBanner() {
  const [state, setState] = useState<"ok" | "down" | "unconfigured" | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .health()
      .then((h) => {
        if (!alive) return;
        if (!h.configured) setState("unconfigured");
        else if (!h.database) setState("down");
        else setState("ok");
      })
      .catch(() => alive && setState("down"));
    return () => {
      alive = false;
    };
  }, []);

  if (state === null || state === "ok") return null;
  return (
    <div className="container">
      <div className="banner">
        <span>🔌</span>
        {state === "unconfigured"
          ? "The backend has no CognoDB credentials configured. Set NEO4J_URI and NEO4J_PASSWORD."
          : "CognoDB is currently unreachable — data may fail to load. The free-tier instance can take a moment to wake."}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Nav />
      <HealthBanner />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/movie/:id" element={<MovieDetailPage />} />
        <Route path="/six-degrees" element={<SixDegrees />} />
        <Route path="/for-you" element={<ForYou />} />
      </Routes>
      <footer className="footer">
        <div className="container">
          MovieGraph · built on{" "}
          <a href="https://console.cognodb.com" target="_blank" rel="noreferrer">
            CognoDB
          </a>{" "}
          (openCypher over Bolt) · a graph-native recommendation demo
        </div>
      </footer>
    </>
  );
}
