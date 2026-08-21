"""Vercel serverless entrypoint for the FastAPI backend.

Vercel's Python runtime serves the ASGI ``app`` exposed here. A catch-all
rewrite in ``vercel.json`` sends every request to this function while
preserving the original path, so FastAPI still does its own routing
(``/api/health``, ``/api/movies``, …) exactly as it does locally.

Nothing app-specific lives here — it just re-exports the app so the same code
runs unchanged under uvicorn (local) and Vercel (hosted).
"""
from app.main import app  # noqa: F401  (re-exported for Vercel's ASGI runtime)
