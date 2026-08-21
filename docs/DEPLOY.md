# Deploying MovieGraph

Everything runs on **Vercel** (no credit card on the Hobby tier) plus your CognoDB instance:

```
Vercel project #1 (static frontend)  ──▶  Vercel project #2 (FastAPI, serverless)  ──▶  CognoDB
```

Two Vercel projects from the same repo — the frontend (static Vite build) and the backend
(FastAPI as a Python serverless function). Both import directly from
**https://github.com/ardifirmansyah8/wexa**.

> **The one ordering gotcha.** The frontend needs the backend's URL (`VITE_API_BASE`), and the
> backend needs the frontend's URL (`CORS_ORIGINS`). That's circular, so: **1)** deploy the
> backend, **2)** deploy the frontend pointing at it, **3)** set the backend's `CORS_ORIGINS`
> to the frontend URL and redeploy.

> **Serverless note.** Each cold start opens a fresh Bolt connection to CognoDB, so the very
> first request (or the first after the CognoDB free tier has gone idle) can be slow. The
> function is configured with `maxDuration: 30s` to absorb that, and the app degrades gracefully
> (health banner + 503 states) if it can't connect in time.

---

## 0. Prerequisites

- The repo is on GitHub: **https://github.com/ardifirmansyah8/wexa** (if private, add Wexa as a
  collaborator — see [§4](#4-after-you-deploy)).
- Your CognoDB instance is running and already seeded, **posters included**. The hosted backend
  reads the **same** instance, so you don't re-seed and the deployed app already shows posters.
- You have the CognoDB **URI** and **password** handy.
- The repo already contains what Vercel needs: `backend/api/index.py` (serverless entry),
  `backend/vercel.json` (routes every request to the FastAPI app), and `frontend/vercel.json`
  (SPA fallback).

---

## 1. Deploy the backend (Vercel · Python serverless)

1. Go to **https://vercel.com** → sign in with GitHub → **Add New… → Project** → import
   `ardifirmansyah8/wexa`.
2. Configure:
   | Field | Value |
   | --- | --- |
   | **Project Name** | `moviegraph-api` (any name) |
   | **Root Directory** | `backend` |
   | **Framework Preset** | Other |
   Leave Build/Output empty — Vercel builds the Python function from `backend/requirements.txt`
   and `backend/vercel.json` automatically.
3. Under **Environment Variables**, add (⚠️ secrets — set them here, never in git):
   | Key | Value |
   | --- | --- |
   | `NEO4J_URI` | `bolt+s://<your-instance-id>.databases.cognodb.com` |
   | `NEO4J_USER` | `cognodb` |
   | `NEO4J_PASSWORD` | _your CognoDB password_ |
   | `NEO4J_DATABASE` | `neo4j` |
   | `CORS_ORIGINS` | `*` _(temporary — tighten in step 3)_ |

   `TMDB_API_KEY` is **not** needed — it's only used by the one-off `enrich_posters` script at
   seed time, and posters are already on your instance.
4. **Deploy.** Note the URL, e.g. `https://moviegraph-api.vercel.app`.
5. Verify: open `https://<your-backend>/api/health` — you want
   `{"status":"ok","configured":true,"database":true}`. (If it's the first hit in a while, give
   it a few seconds to wake CognoDB, then refresh.)

---

## 2. Deploy the frontend (Vercel · static)

1. **Add New… → Project** → import the **same** repo again (a second project).
2. Configure:
   | Field | Value |
   | --- | --- |
   | **Project Name** | `moviegraph` (any name) |
   | **Root Directory** | `frontend` |
   | **Framework Preset** | Vite (auto-detected) |
   | **Build Command** | `npm run build` (default) |
   | **Output Directory** | `dist` (default) |
3. Under **Environment Variables**, add:
   | Key | Value |
   | --- | --- |
   | `VITE_API_BASE` | your backend URL from step 1, e.g. `https://moviegraph-api.vercel.app` |
4. **Deploy.** Note the frontend URL, e.g. `https://moviegraph.vercel.app`.

`frontend/vercel.json` is included so client-side routes (e.g. `/movie/inception`) serve
`index.html` instead of 404-ing.

> `VITE_API_BASE` is baked in at **build** time — if you change it later, redeploy the frontend.

---

## 3. Close the loop — lock down CORS

1. In the **backend** project → **Settings → Environment Variables**, change `CORS_ORIGINS`
   from `*` to your exact frontend origin (scheme + host, no trailing slash):
   ```
   CORS_ORIGINS=https://moviegraph.vercel.app
   ```
2. Redeploy the backend (Deployments → ⋯ → **Redeploy**) so the new value takes effect.
3. Open the frontend URL and click through Browse → a movie → Six Degrees → For You. Data should
   load on every page.

That's the hosted demo the assignment asks for. 🎉

---

## 4. After you deploy

1. **Put the live URL in the README.** Replace the placeholder in the top callout:
   ```
   > **▶️ Live demo:** https://moviegraph.vercel.app · ...
   ```
   then `git commit -am "Add live demo link" && git push`.
2. **If the repo is private, add Wexa as a collaborator:** GitHub → **Settings → Collaborators**.
3. **Keep the CognoDB instance running** until the review is done — they may test against live data.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Frontend loads but every request fails; console shows a CORS error | `CORS_ORIGINS` on the backend doesn't exactly match the frontend origin. Fix it and redeploy the backend. |
| `/api/health` returns `"database": false` | The function reached itself but not CognoDB — check `NEO4J_URI`/`NEO4J_PASSWORD` and that the instance is running. |
| First request times out / 504 | Cold start while CognoDB was asleep. Retry after a few seconds; `maxDuration` is 30s. |
| Health is fine but pages are empty | The instance was never seeded. Run `python -m seed.seed` locally against the same URI. |
| Deep link like `/movie/x` 404s | Make sure the **frontend** project's Root Directory is `frontend` (so its `vercel.json` SPA rewrite applies). |
| Backend build fails importing `app` | Confirm the backend project's **Root Directory** is `backend` (so `api/index.py` can `import app`). |

---

## Alternatives (also no credit card)

- **Backend on a persistent container** (keeps the Bolt pool warm, no cold starts): **Hugging
  Face Spaces** (Docker) or **Koyeb** (Render-like, deploy from GitHub). Both run
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT` with the same env vars.
- **Frontend:** Netlify or Cloudflare Pages — build `npm run build`, publish `dist`, add an SPA
  fallback (Netlify: a `_redirects` file with `/* /index.html 200`).
