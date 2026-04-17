import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# TMDb TV genre IDs
TV_GENRE_DRAMA = 18
TV_GENRE_COMEDY = 35
TV_GENRE_MYSTERY = 9648
TV_GENRE_SCI_FI_FANTASY = 10765
TV_GENRE_CRIME = 80


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _is_probably_thai(item: Dict[str, Any]) -> bool:
    lang = _safe_text(item.get("original_language")).lower()
    origin_countries = item.get("origin_country") or []
    return lang == "th" or "TH" in origin_countries


def _keyword_score(text: str, keywords: List[str], weight: float) -> float:
    text = text.lower()
    score = 0.0
    for kw in keywords:
        if kw.lower() in text:
            score += weight
    return score


def _setting_to_genres(setting: str) -> List[int]:
    setting = setting.lower().strip()
    if setting == "crime/mafia":
        return [TV_GENRE_CRIME, TV_GENRE_DRAMA]
    if setting == "supernatural":
        return [TV_GENRE_SCI_FI_FANTASY, TV_GENRE_DRAMA]
    if setting == "slice of life":
        return [TV_GENRE_DRAMA, TV_GENRE_COMEDY]
    if setting == "historical":
        return [TV_GENRE_DRAMA]
    if setting == "school":
        return [TV_GENRE_DRAMA, TV_GENRE_COMEDY]
    if setting == "workplace":
        return [TV_GENRE_DRAMA]
    return [TV_GENRE_DRAMA]


def _score_candidate(item: Dict[str, Any], features: Dict[str, Any]) -> float:
    score = 0.0

    title = _safe_text(item.get("name"))
    overview = _safe_text(item.get("overview"))
    blob = f"{title} {overview}".lower()

    tropes = [x.lower() for x in (features.get("tropes") or [])]
    tones = [x.lower() for x in (features.get("emotional_tone") or [])]
    setting = _safe_text(features.get("setting")).lower()
    angst = _safe_text(features.get("angst_level")).lower()

    if _is_probably_thai(item):
        score += 5.0
    else:
        score -= 0.5

    score += _keyword_score(blob, tropes, 1.8)
    score += _keyword_score(blob, tones, 1.2)

    setting_keywords = {
        "school": ["school", "student", "university", "campus"],
        "workplace": ["office", "work", "intern", "colleague"],
        "crime/mafia": ["mafia", "crime", "gang", "bodyguard"],
        "supernatural": ["ghost", "spirit", "supernatural", "curse"],
        "slice of life": ["family", "daily life", "friendship", "ordinary"],
        "historical": ["period", "historical", "kingdom", "century"],
    }

    if setting in setting_keywords:
        score += _keyword_score(blob, setting_keywords[setting], 1.5)

    if angst == "high":
        score += _keyword_score(blob, ["betrayal", "tragedy", "danger", "crime", "pain"], 1.0)
    elif angst == "low":
        score += _keyword_score(blob, ["sweet", "soft", "cute", "light", "warm"], 1.0)

    vote = float(item.get("vote_average") or 0.0)
    score += min(vote / 10.0, 1.0)

    popularity = float(item.get("popularity") or 0.0)
    score += min(popularity / 100.0, 1.0)

    return round(score, 3)


async def _tmdb_get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not TMDB_API_KEY:
        raise RuntimeError("Missing TMDB_API_KEY in environment.")

    merged = {"api_key": TMDB_API_KEY, "language": "en-US"}
    if params:
        merged.update(params)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{TMDB_BASE_URL}{path}", params=merged)
        response.raise_for_status()
        return response.json()


async def _fetch_tv_details(series_id: int) -> Dict[str, Any]:
    return await _tmdb_get("/tv/" + str(series_id))


async def _discover_candidates(features: Dict[str, Any], page: int = 1) -> List[Dict[str, Any]]:
    setting = _safe_text(features.get("setting"))
    genre_ids = _setting_to_genres(setting)

    params = {
        "page": page,
        "include_adult": "false",
        "sort_by": "popularity.desc",
        "with_original_language": "th",
        "with_genres": ",".join(str(g) for g in genre_ids),
        "vote_count.gte": 5,
    }

    data = await _tmdb_get("/discover/tv", params)
    print("TMDb discover params:", params)
    print("TMDb discover result count:", len(data.get("results", [])))
    return data.get("results", [])


async def _search_candidates(original_text: str, page: int = 1) -> List[Dict[str, Any]]:
    if not original_text.strip():
        return []

    data = await _tmdb_get(
        "/search/tv",
        {
            "query": original_text.strip(),
            "page": page,
            "include_adult": "false",
        },
    )
    print("TMDb search query:", original_text.strip())
    print("TMDb search result count:", len(data.get("results", [])))
    return data.get("results", [])


async def search_tmdb_titles(features: Dict[str, Any], original_text: str, max_results: int = 6) -> List[Dict[str, Any]]:
    candidate_map: Dict[int, Dict[str, Any]] = {}

    # 1. Broad discover-based retrieval
    discover_results = await _discover_candidates(features, page=1)
    for item in discover_results:
        series_id = item.get("id")
        if not series_id:
            continue
        score = _score_candidate(item, features)
        item["_score"] = score
        candidate_map[series_id] = item

    # 2. Supplemental text search using user's original text
    search_results = await _search_candidates(original_text, page=1)
    for item in search_results:
        series_id = item.get("id")
        if not series_id:
            continue
        score = _score_candidate(item, features) + 0.5
        if series_id not in candidate_map or score > candidate_map[series_id]["_score"]:
            item["_score"] = score
            candidate_map[series_id] = item

    ranked = sorted(candidate_map.values(), key=lambda x: x["_score"], reverse=True)[: max_results * 2]
    print("TMDb candidate count after ranking:", len(ranked))

    results: List[Dict[str, Any]] = []
    for item in ranked[:max_results]:
        details = await _fetch_tv_details(item["id"])

        poster_path = details.get("poster_path") or item.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else ""

        first_air_date = _safe_text(details.get("first_air_date") or item.get("first_air_date"))
        year = first_air_date[:4] if len(first_air_date) >= 4 else ""

        country = "Thailand"
        if details.get("origin_country"):
            if "TH" in details["origin_country"]:
                country = "Thailand"
            else:
                country = details["origin_country"][0]

        results.append(
            {
                "title": details.get("name") or item.get("name") or "",
                "country": country,
                "year": year,
                "episodes": details.get("number_of_episodes") or 0,
                "rating": round(float(details.get("vote_average") or item.get("vote_average") or 0.0), 1),
                "main_couple": "",
                "poster": poster_url,
                "poster_is_absolute": True,
                "synopsis": details.get("overview") or item.get("overview") or "",
                "features": {},
                "source": "tmdb",
                "tmdb_id": details.get("id") or item.get("id"),
                "similarity_score": item["_score"],
            }
        )

    print("TMDb final live results count:", len(results))
    return results