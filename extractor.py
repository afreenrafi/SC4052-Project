"""
Run:
python extractor.py

Local narrative feature extraction service.
Creates: data/dramas_enriched.json
"""

import json
import os
import re

INPUT_PATH = "data/dramas.json"
OUTPUT_PATH = "data/dramas_enriched.json"


TROPE_RULES = {
    "enemies-to-lovers": ["rival", "rival families", "enemies", "feud", "clashing personalities"],
    "fake relationship": ["pretend to be", "fake relationship", "fake boyfriend", "pretend boyfriend"],
    "forced proximity": ["roommate", "shares his apartment", "hostage", "stuck", "together"],
    "slow burn": ["slowly", "gradually", "over time", "growing relationship"],
    "second chance": ["reunite", "years apart", "meet again"],
    "childhood friends": ["childhood friends", "since childhood", "grew up together"],
    "bodyguard": ["bodyguard", "protect", "mafia family"],
    "found family": ["group of friends", "adopted daughter", "family life"],
    "hurt/comfort": ["helps him overcome", "comfort", "fear of water", "heals"],
    "forbidden love": ["forbidden", "teacher", "ethically complex", "rival families"],
    "unrequited love": ["harboured feelings", "not reciprocated", "persistent admirer"],
    "age gap": ["younger subordinate", "35-year-old", "older", "younger"],
}

TONE_RULES = {
    "fluffy": ["sweet", "tender", "light", "warmth", "playful"],
    "angsty": ["secrets", "betrayals", "complicated", "threats", "pain"],
    "bittersweet": ["cannot move on", "grief", "loss", "died", "heart"],
    "humorous": ["comedic", "funny", "awkward", "playful"],
    "dark": ["crime", "mafia", "conspiracy", "dangerous", "ghost", "curse"],
    "heartwarming": ["warmth", "family life", "joy", "gentle", "volunteer"],
    "tense": ["strict", "threats", "investigate", "kidnaps", "mysterious"],
    "melancholic": ["solitude", "stuck in life", "unspoken feelings", "move on"],
    "hopeful": ["discover", "following one's dreams", "open his heart", "redemption"],
}

THEME_RULES = {
    "identity": ["identity", "twin", "new body"],
    "acceptance": ["acceptance", "finding one's identity", "social pressure"],
    "family conflict": ["family", "rival families", "in-laws"],
    "loyalty": ["loyalties", "gang", "bodyguard", "protect"],
    "sacrifice": ["volunteer in place", "donated her heart", "sacrifice"],
    "class divide": ["powerful family", "ordinary man", "celebrity"],
    "grief": ["death", "died", "ghost", "loss"],
    "redemption": ["redemption", "second chance", "move on"],
    "trust": ["trust", "truth", "secrets", "open his heart"],
    "jealousy": ["jealousy", "persistent admirer"],
    "trauma": ["fear of water", "harm", "pain", "cannot move on"],
    "self-discovery": ["discover", "following one's dreams", "rediscover joy"],
    "social pressure": ["school", "family pressures", "strict school"],
}

SETTING_RULES = {
    "school": ["university", "school", "student", "faculty", "high school"],
    "workplace": ["salary man", "subordinate", "office", "colleague", "workaholic"],
    "crime/mafia": ["mafia", "crime boss", "gang", "police officer", "detective", "conspiracy"],
    "supernatural": ["ghost", "curse", "cemetery", "life and death", "read minds"],
    "slice of life": ["family life", "small pleasures", "apartment", "everyday life"],
    "historical": ["historical", "kingdom", "dynasty", "period"],
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def match_tags(text: str, rules: dict, max_tags: int = 4) -> list[str]:
    tags = []
    for tag, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    return tags[:max_tags]


def detect_setting(text: str) -> str:
    for setting, keywords in SETTING_RULES.items():
        if any(keyword in text for keyword in keywords):
            return setting
    return "other"


def detect_pacing(text: str) -> str:
    if any(x in text for x in ["slowly", "gradually", "over time", "unspoken feelings"]):
        return "slow burn"
    if any(x in text for x in ["suddenly", "forced to", "kidnaps", "intense"]):
        return "fast burn"
    return "medium"


def detect_conflict_type(text: str) -> str:
    internal = any(x in text for x in ["feelings", "identity", "struggles", "fear", "worry"])
    external = any(x in text for x in ["family", "crime", "curse", "threats", "school administration"])

    if internal and external:
        return "both"
    if internal:
        return "internal"
    if external:
        return "external"
    return "both"


def detect_angst_level(text: str) -> str:
    if any(x in text for x in ["death", "crime", "mafia", "betrayals", "threats", "harm", "ghost"]):
        return "high"
    if any(x in text for x in ["sweet", "warmth", "comedic", "gentle", "playful"]):
        return "low"
    return "medium"


def detect_fluff_level(text: str) -> str:
    if any(x in text for x in ["sweet", "warmth", "gentle", "joy", "playful"]):
        return "high"
    if any(x in text for x in ["crime", "death", "threats", "harm", "betrayals"]):
        return "low"
    return "medium"


def detect_happy_ending(text: str) -> bool:
    unhappy = ["cannot move on", "death", "loss", "grief"]
    return not any(x in text for x in unhappy)


def build_relationship_dynamic(text: str, tropes: list[str], setting: str) -> str:
    if "enemies-to-lovers" in tropes:
        return "A tense relationship evolves from rivalry into romance."
    if "fake relationship" in tropes:
        return "A performative relationship gradually becomes genuine."
    if "bodyguard" in tropes:
        return "A protective relationship develops in a high-stakes environment."
    if setting == "school":
        return "A youthful relationship develops through conflict, closeness, and growth."
    if setting == "crime/mafia":
        return "A dangerous relationship grows amid suspicion, loyalty, and external threats."
    return "A complex evolving relationship shaped by emotional tension and trust."


def extract_features(item: dict) -> dict:
    synopsis = clean_text(item.get("synopsis", ""))

    tropes = match_tags(synopsis, TROPE_RULES, max_tags=4)
    tones = match_tags(synopsis, TONE_RULES, max_tags=3)
    themes = match_tags(synopsis, THEME_RULES, max_tags=4)
    setting = detect_setting(synopsis)

    return {
        "tropes": tropes,
        "emotional_tone": tones,
        "pacing": detect_pacing(synopsis),
        "themes": themes,
        "relationship_dynamic": build_relationship_dynamic(synopsis, tropes, setting),
        "setting": setting,
        "conflict_type": detect_conflict_type(synopsis),
        "angst_level": detect_angst_level(synopsis),
        "fluff_level": detect_fluff_level(synopsis),
        "happy_ending": detect_happy_ending(synopsis),
    }


def enrich_all():
    if not os.path.exists(INPUT_PATH):
        print("Run scraper.py first.")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    enriched = []
    for i, item in enumerate(items, start=1):
        print(f"[{i}/{len(items)}] Extracting narrative features: {item['title']}")
        features = extract_features(item)
        enriched.append({**item, "features": features})

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Saved {len(enriched)} enriched items to {OUTPUT_PATH}")


if __name__ == "__main__":
    enrich_all()