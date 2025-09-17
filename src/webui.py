from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from agent import analyze_user

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure template/static dirs exist (FastAPI won't create them automatically)
TEMPLATE_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="X 用户兴趣分析", description="输入用户名，分析其最近 tweets")

# Simple in-memory cache structure
# cache = { username_lower: {"result": str, "ts": datetime, "count": int} }
CACHE: Dict[str, Dict[str, Any]] = {}
MAX_CACHE_SIZE = 30
CACHE_TTL = timedelta(hours=6)

def _prune_cache():
    # Remove expired
    now = datetime.utcnow()
    expired = [k for k,v in CACHE.items() if now - v["ts"] > CACHE_TTL]
    for k in expired:
        CACHE.pop(k, None)
    # Trim size (LRU-like: oldest ts first)
    if len(CACHE) > MAX_CACHE_SIZE:
        for k,_ in sorted(CACHE.items(), key=lambda kv: kv[1]["ts"])[: len(CACHE)-MAX_CACHE_SIZE]:
            CACHE.pop(k, None)

def _cache_put(username: str, result: str):
    key = username.lower()
    CACHE[key] = {"result": result, "ts": datetime.utcnow(), "count": CACHE.get(key, {}).get("count", 0) + 1}
    _prune_cache()

def _cache_get(username: str):
    data = CACHE.get(username.lower())
    if not data:
        return None
    if datetime.utcnow() - data["ts"] > CACHE_TTL:
        CACHE.pop(username.lower(), None)
        return None
    return data

def _history_list() -> List[Dict[str, Any]]:
    return [
        {"username": k, "age_minutes": int((datetime.utcnow()-v["ts"]).total_seconds()/60), "ts": v["ts"], "count": v["count"]}
        for k,v in sorted(CACHE.items(), key=lambda kv: kv[1]["ts"], reverse=True)
    ]

# Mount static (even if empty now) for potential future assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": None, "username": "", "history": _history_list(), "cached": False}
    )

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, username: str = Form(...)):
    username = username.strip().lstrip('@')
    error = None
    result: str | None = None
    cached = False
    if not username:
        error = "请输入用户名"
    else:
        cached_entry = _cache_get(username)
        if cached_entry:
            result = cached_entry["result"]
            cached = True
        else:
            try:
                result = await analyze_user(username)
                if result:
                    _cache_put(username, result)
            except Exception as e:  # Broad catch for UI; internal logs could be added
                error = f"分析失败: {e}"  # Avoid leaking sensitive internal details
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": result, "username": username, "error": error, "history": _history_list(), "cached": cached},
    )

@app.get("/history/{username}", response_class=HTMLResponse)
async def history_view(request: Request, username: str):
    entry = _cache_get(username)
    if not entry:
        # redirect to analyze to fetch fresh
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": entry["result"], "username": username, "error": None, "history": _history_list(), "cached": True},
    )

@app.post("/refresh/{username}", response_class=HTMLResponse)
async def refresh_user(request: Request, username: str):
    username = username.strip().lstrip('@')
    try:
        result = await analyze_user(username)
        if result:
            _cache_put(username, result)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": result, "username": username, "error": None, "history": _history_list(), "cached": False, "refreshed": True},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": None, "username": username, "error": f"刷新失败: {e}", "history": _history_list(), "cached": False},
        )

# Optional: simple health check
@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run("webui:app", host="0.0.0.0", port=8000, reload=True)
