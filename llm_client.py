import json
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

SYSTEM_PROMPT = """
You are a narrative intelligence extraction engine.

Your job is to analyze a Thai BL drama synopsis or a natural-language preference
message and convert it into structured narrative metadata.

Return ONLY valid JSON in this exact format:

{
  "tropes": [],
  "emotional_tone": [],
  "themes": [],
  "relationship_dynamic": "",
  "setting": "",
  "conflict_type": "",
  "angst_level": "",
  "fluff_level": "",
  "happy_ending": true
}

Rules:
- tropes must be a list of short strings
- emotional_tone must be a list of short strings
- themes must be a list of short strings
- setting must be one of:
  "school", "workplace", "crime/mafia", "supernatural", "slice of life", "historical", "other"
- conflict_type must be one of:
  "internal", "external", "both"
- angst_level must be one of:
  "low", "medium", "high"
- fluff_level must be one of:
  "low", "medium", "high"
- relationship_dynamic must be a single concise sentence
- happy_ending must be true or false
- Do not include markdown
- Do not include explanation text
"""

async def analyze_text_with_gemini(text: str) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY in environment.")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\nTEXT TO ANALYZE:\n{text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        }
    }

    params = {"key": GEMINI_API_KEY}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(GEMINI_URL, params=params, json=payload)
        response.raise_for_status()
        data = response.json()

    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
        return parsed
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini response: {e}")