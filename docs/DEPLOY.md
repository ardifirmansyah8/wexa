# Deploying MovieGraph

MovieGraph is two independently-deployable pieces plus your CognoDB instance:

```
Vercel (static frontend)  ──▶  Render (FastAPI backend)  ──▶  CognoDB (already running)
```

Any free host works; this guide uses **Render** for the backend and **Vercel** for the
frontend because both have zero-cost tiers and no credit card is required.

> **The one ordering gotcha.** The frontend needs the backend's URL (`VITE_API_BASE`), and the
> backend needs the frontend's URL (`CORS_ORIGINS`). That's circular, so the order is:
> **1)** deploy the backend, **2)** deploy the frontend pointing at it, **3)** come back and set
> the backend's `CORS_ORIGINS` to the frontend URL and redeploy. Steps below follow that order.

---

## 0. Prerequisites

- The repo is on GitHub: **https://github.com/ardifirmansyah8/wexa**. Both Render and Vercel
  import straight from it. (If it's private, add Wexa as a collaborator — see [§4](#4-after-you-deploy).)
- Your CognoDB instance is running and already seeded, **posters included** (`python -m seed.seed`
  after `enrich_posters`). The hosted backend reads the **same** instance, so you do **not**
  re-seed and the deployed app already shows real posters.
- You have the CognoDB **URI** and **password** handy.

---

## 1. Deploy the backend (Render)

1. Go to **https://render.com** → sign in with GitHub → **New +** → **Web Service**.
2. Select this repository.
3. Configure:
   | Field | Value |
   | --- | --- |
   | **Root Directory** | `backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |
4. Under **Environment**, add these variables (⚠️ secrets — set them here, never in git):
   | Key | Value |
   | --- | --- |
   | `NEO4J_URI` | `bolt+s://<your-instance-id>.databases.cognodb.com` |
   | `NEO4J_USER` | `cognodb` |
   | `NEO4J_PASSWORD` | _your CognoDB password_ |
   | `NEO4J_DATABASE` | `neo4j` |
   | `PYTHON_VERSION` | `3.12.7` |
   | `CORS_ORIGINS` | `*` _(temporary — tighten in step 3)_ |

   `TMDB_API_KEY` is **not** needed here — it's only used by the one-off `enrich_posters` script
   at seed time, and posters are already stored on your instance.
5. **Create Web Service.** When it's live, note the URL, e.g.
   `https://moviegraph-api.onrender.com`.
6. Verify: open `https://<your-backend>/api/health` — you want
   `{"status":"ok","configured":true,"database":true}`.

> **Free-tier note:** Render free services sleep after ~15 min idle, so the first request after
> a nap takes 30–60s to wake. The app already handles this gracefully (the health banner and
> 503 states), but mention it in your demo so reviewers aren't surprised.

---

## 2. Deploy the frontend (Vercel)

1. Go to **https://vercel.com** → sign in with GitHub → **Add New… → Project** → import this repo.
2. Configure:
   | Field | Value |
   | --- | --- |
   | **Root Directory** | `frontend` |
   | **Framework Preset** | Vite (auto-detected) |
   | **Build Command** | `npm run build` (default) |
   | **Output Directory** | `dist` (default) |
3. Under **Environment Variables**, add:
   | Key | Value |
   | --- | --- |
   | `VITE_API_BASE` | your backend URL from step 1, e.g. `https://moviegraph-api.onrender.com` |
4. **Deploy.** Note the frontend URL, e.g. `https://moviegraph.vercel.app`.

`frontend/vercel.json` is already included so client-side routes (e.g. `/movie/inception`)
serve `index.html` instead of 404-ing.

> `VITE_API_BASE` is baked in at **build** time. If you change it later, trigger a redeploy.

---

## 3. Close the loop — lock down CORS

1. Back in **Render → your service → Environment**, change `CORS_ORIGINS` from `*` to your exact
   frontend URL:
   ```
   CORS_ORIGINS=https://moviegraph.vercel.app
   ```
2. Save — Render redeploys automatically.
3. Open the Vercel URL and click through Browse → a movie → Six Degrees → For You. Data should
   load on every page.

That's the hosted demo the assignment asks for. 🎉

---

## 4. After you deploy

1. **Put the live URL in the README.** Replace the placeholder in the top callout:
   ```
   > **▶️ Live demo:** https://moviegraph.vercel.app · ...
   ```
   then commit and push:
   ```bash
   git commit -am "Add live demo link" && git push
   ```
2. **If the repo is private, add Wexa as a collaborator** (they request access in the brief):
   GitHub → **Settings → Collaborators → Add people**.
3. **Keep the CognoDB instance running** until the review is done — Wexa may test against live data.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Frontend loads but every request fails; console shows a CORS error | `CORS_ORIGINS` on the backend doesn't exactly match the frontend origin (scheme + host, no trailing slash). Fix in Render and redeploy. |
| `/api/health` returns `"database": false` | Backend can reach itself but not CognoDB — check `NEO4J_URI`/`NEO4J_PASSWORD`, and that the instance is running. |
| Health is fine but pages are empty | The instance was never seeded. Run `python -m seed.seed` locally against the same URI. |
| First load after idle is very slow | Render free tier cold start — expected; it wakes in under a minute. |
| Deep link like `/movie/x` 404s | `vercel.json` rewrite missing — it's included in `frontend/`; make sure the Vercel **Root Directory** is `frontend`. |
| Build fails on Render with a Python version error | Set `PYTHON_VERSION=3.12.7` in the Render environment. |

---

## Alternatives

- **Backend:** Railway, Fly.io, or any host that runs `uvicorn app.main:app`. Same env vars.
- **Frontend:** Netlify or Cloudflare Pages — build `npm run build`, publish `dist`, and add an
  SPA fallback rewrite (Netlify: a `_redirects` file with `/* /index.html 200`).
