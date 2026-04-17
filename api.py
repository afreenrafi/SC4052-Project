"""
Run:
python -m uvicorn api:app --reload
"""

import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from recommender import NarrativeRecommender
from extractor import extract_features
from llm_client import analyze_text_with_gemini
from tmdb_client import search_tmdb_titles

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "dramas_enriched.json"
FEEDBACK_PATH = BASE_DIR / "data" / "feedback.json"
POSTERS_DIR = BASE_DIR / "posters"

recommender: Optional[NarrativeRecommender] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender
    if DATA_PATH.exists():
        recommender = NarrativeRecommender(str(DATA_PATH))
        print(f"Loaded {len(recommender.items)} narrative items.")
    else:
        print("WARNING: Run scraper.py then extractor.py first.")
    yield


app = FastAPI(
    title="Narrative Intelligence API",
    version="3.0.0",
    description="Narrative Intelligence-as-a-Service with local + live recommendations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/posters", StaticFiles(directory=str(POSTERS_DIR)), name="posters")


def get_rec() -> NarrativeRecommender:
    if recommender is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded. Run scraper.py then extractor.py first.")
    return recommender


def build_query_from_features(features: dict) -> dict:
    return {
        "tropes": features.get("tropes", []),
        "emotional_tone": features.get("emotional_tone", []),
        "angst_level": features.get("angst_level", ""),
        "setting": features.get("setting", ""),
    }


class ExtractRequest(BaseModel):
    title: str = Field(default="")
    country: str = Field(default="")
    synopsis: str = Field(..., min_length=20)


class RecommendByTitleRequest(BaseModel):
    title: str = Field(..., min_length=1)
    top_n: int = Field(default=5, ge=1, le=20)


class RecommendByPrefsRequest(BaseModel):
    tropes: List[str] = []
    emotional_tone: List[str] = []
    angst_level: str = ""
    setting: str = ""
    top_n: int = Field(default=5, ge=1, le=20)


class FeedbackRequest(BaseModel):
    source_title: str = Field(..., min_length=1)
    recommended_title: str = Field(..., min_length=1)
    helpful: bool


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=10)
    top_n: int = Field(default=6, ge=1, le=20)


@app.get("/")
def root():
    return {
        "message": "Narrative Intelligence API is running.",
        "status": "ok",
        "services": [
            "narrative extraction",
            "narrative recommendation",
            "live catalog recommendation",
            "narrative analytics",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ready" if recommender is not None else "not_ready",
        "dataset_loaded": recommender is not None,
        "dataset_size": len(recommender.items) if recommender else 0,
        "posters_exists": POSTERS_DIR.exists(),
    }


@app.post("/extract")
def extract_narrative_features(body: ExtractRequest):
    item = {
        "title": body.title,
        "country": body.country,
        "synopsis": body.synopsis,
    }
    features = extract_features(item)
    return {"input": item, "features": features}


@app.get("/items")
def list_items(search: str = "", country: str = ""):
    rec = get_rec()
    items = rec.get_all()

    if search:
        items = [d for d in items if search.lower() in d["title"].lower()]
    if country:
        items = [d for d in items if d["country"].lower() == country.lower()]

    return {"count": len(items), "items": items}


@app.get("/item/{title}")
def get_item(title: str):
    item = get_rec().get_one(title)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{title}' not found.")
    return item


@app.post("/recommend/by-title")
def recommend_by_title(body: RecommendByTitleRequest):
    rec = get_rec()
    source = rec.get_one(body.title)

    if not source:
        raise HTTPException(status_code=404, detail=f"Title '{body.title}' not found.")

    recommendations = rec.recommend_by_title(body.title, body.top_n)

    return {
        "service": "narrative recommendation",
        "mode": "reference-title",
        "source_item": source,
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
    }


@app.post("/recommend/by-features")
def recommend_by_features(body: RecommendByPrefsRequest):
    rec = get_rec()
    results = rec.recommend_by_preferences(
        tropes=body.tropes or None,
        emotional_tone=body.emotional_tone or None,
        angst_level=body.angst_level or None,
        setting=body.setting or None,
        top_n=body.top_n,
    )

    return {
        "service": "narrative recommendation",
        "mode": "feature-query",
        "query": {
            "tropes": body.tropes,
            "emotional_tone": body.emotional_tone,
            "angst_level": body.angst_level,
            "setting": body.setting,
        },
        "recommendation_count": len(results),
        "recommendations": results,
    }


@app.post("/recommend/hybrid")
async def recommend_hybrid(body: AnalyzeTextRequest):
    rec = get_rec()

    try:
        features = await analyze_text_with_gemini(body.text)
        source = "gemini"
    except Exception:
        features = extract_features({
            "title": "",
            "country": "",
            "synopsis": body.text,
        })
        source = "local_fallback"

    query = build_query_from_features(features)

    local_results = rec.recommend_by_preferences(
        tropes=query["tropes"] or None,
        emotional_tone=query["emotional_tone"] or None,
        angst_level=query["angst_level"] or None,
        setting=query["setting"] or None,
        top_n=body.top_n,
    )

    try:
        live_results = await search_tmdb_titles(features, body.text, max_results=body.top_n)
    except Exception as e:
        live_results = []
        print(f"TMDb live fetch failed: {e}")

    return {
        "input_text": body.text,
        "source": source,
        "extracted_features": features,
        "local_results": local_results,
        "live_results": live_results,
    }


@app.post("/feedback")
def feedback(body: FeedbackRequest):
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    if FEEDBACK_PATH.exists():
        try:
            with FEEDBACK_PATH.open("r", encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []
    else:
        log = []

    entry = {
        "source_title": body.source_title,
        "recommended_title": body.recommended_title,
        "helpful": body.helpful,
    }
    log.append(entry)

    with FEEDBACK_PATH.open("w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    return {
        "message": "Feedback recorded.",
        "entry": entry,
        "total_feedback_records": len(log),
    }


@app.get("/analytics/overview")
def analytics_overview():
    rec = get_rec()
    items = rec.get_all()

    by_country = {}
    trope_freq = {}
    tone_freq = {}
    setting_freq = {}
    angst_freq = {}

    for item in items:
        country = item.get("country", "Unknown")
        by_country[country] = by_country.get(country, 0) + 1

        features = item.get("features", {})

        for trope in features.get("tropes", []):
            trope_freq[trope] = trope_freq.get(trope, 0) + 1

        for tone in features.get("emotional_tone", []):
            tone_freq[tone] = tone_freq.get(tone, 0) + 1

        setting = features.get("setting", "other")
        setting_freq[setting] = setting_freq.get(setting, 0) + 1

        angst = features.get("angst_level", "unknown")
        angst_freq[angst] = angst_freq.get(angst, 0) + 1

    return {
        "service": "narrative analytics",
        "total_items": len(items),
        "by_country": by_country,
        "top_tropes": dict(sorted(trope_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
        "top_tones": dict(sorted(tone_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
        "by_setting": setting_freq,
        "by_angst_level": angst_freq,
    }


@app.get("/analytics/country/{country}")
def analytics_by_country(country: str):
    rec = get_rec()
    items = [x for x in rec.get_all() if x["country"].lower() == country.lower()]

    if not items:
        raise HTTPException(status_code=404, detail=f"No items found for country '{country}'.")

    trope_freq = {}
    tone_freq = {}

    for item in items:
        features = item.get("features", {})
        for trope in features.get("tropes", []):
            trope_freq[trope] = trope_freq.get(trope, 0) + 1
        for tone in features.get("emotional_tone", []):
            tone_freq[tone] = tone_freq.get(tone, 0) + 1

    return {
        "country": country,
        "item_count": len(items),
        "top_tropes": dict(sorted(trope_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
        "top_tones": dict(sorted(tone_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
    }