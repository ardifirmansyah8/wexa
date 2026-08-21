# Submission checklist — CognoDB Assignment 2

Tracks every requirement in the brief against what's done. `[x]` = complete, `[ ]` = your action.

## A. Requirements coverage (all built & verified)

### Data & queries (§5.1)
- [x] Thoughtful graph data model — labeled nodes, typed relationships, properties
- [x] Data model documented with a diagram in the README (Mermaid)
- [x] Realistic seed data loaded by a script in the repo (`backend/seed/seed.py`, 44 films)
- [x] At least one multi-hop traversal — _More like this_ (2-hop) & _Six Degrees_ (`shortestPath`)
- [x] At least one query SQL finds awkward — _Fans also liked_ (collaborative filtering)
- [x] Parameterised queries via the official Neo4j driver — no string-concatenated Cypher
- [x] All queries verified against the live CognoDB instance (`backend/smoke_test.py`, 14/14 pass)

### Application & UI/UX (§5.2)
- [x] Functional web app a non-technical person can use (React + Vite)
- [x] Clean, intentional UI/UX — layout, navigation, readable typography
- [x] Loading states (skeletons/spinners)
- [x] Empty states
- [x] Error states (incl. friendly database-offline handling)

### Engineering (§5.3)
- [x] Connection details read from env vars, never committed (`.env` git-ignored)
- [x] Clear project structure, walk-through-able codebase
- [x] Graceful error handling when the DB is unreachable (typed error → HTTP 503 → UI banner)

### Deliverables (§6)
- [x] Full source code — app, data-loading scripts, Cypher queries
- [x] README — use case, "Why a graph database?", diagram, setup/run, queries explained
- [x] README — screenshots of the UI (`docs/screenshots/`)
- [x] **Hosted application demo link** (mandatory) — https://moviegraph.vercel.app (Vercel, live)
- [x] **Short screen recording** (mandatory) — silent walkthrough at `docs/demo/demo.gif`
      (+ `demo.mp4`), embedded in the README. Optionally re-record with narration for submission.

## B. Your actions to submit

- [x] **Push to GitHub** — https://github.com/ardifirmansyah8/wexa (`.env` confirmed not tracked)
- [ ] **Deploy the backend** (Render) — follow [`DEPLOY.md`](DEPLOY.md) §1
- [ ] **Deploy the frontend** (Vercel) — [`DEPLOY.md`](DEPLOY.md) §2
- [ ] **Lock down CORS** to the real frontend URL — [`DEPLOY.md`](DEPLOY.md) §3
- [ ] **Smoke-test the hosted demo** — click Browse → movie → Six Degrees → For You
- [x] **Screen recording** — walkthrough GIF + MP4 in `docs/demo/`, embedded in README
      (optionally re-record with your narration for a more personal submission)
- [ ] **Add the live demo link** to the top of the README
- [ ] If the repo is **private**, add Wexa as a collaborator (they request access in the brief)
- [ ] **Email hr@wexa.ai** — subject: `CognoDB Assignment 2 – <Your Name>`, include repo URL + demo link
- [ ] Keep the CognoDB instance **running** until you hear back (they may test against live data)

## C. After the review
- [ ] Rotate the CognoDB password (it was shared in chat and is in the local `.env`)

## D. Interview prep (§9 — "explain and defend every part")
- [ ] Be ready to explain the data model and why a graph fits (README has the argument)
- [ ] Be ready to walk through the four signature queries in `backend/app/queries.py`
- [ ] Know the CognoDB compatibility fixes: `round()` 1-arg, no `UNION` inside `CALL {}`,
      certifi CA bundle for `bolt+s://` (all documented in code comments + commit history)
- [ ] Be able to trace one request end-to-end: React → `api.ts` → FastAPI router → `queries.py`
      → `db.py` → CognoDB → back
