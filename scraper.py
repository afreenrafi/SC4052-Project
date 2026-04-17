import json
import os

SEED_DRAMAS = [
    {
        "title": "Only Boo!",
        "country": "Thailand",
        "year": 2024,
        "episodes": 12,
        "rating": 8.1,
        "main_couple": "Sea D & Keen S",
        "poster": "posters/only_boo.jpg",
        "synopsis": "A cheerful aspiring idol transfers to a new school and clashes with a strict senior. Their relationship slowly softens into a gentle romance."
    },
    {
        "title": "Head 2 Head",
        "country": "Thailand",
        "year": 2024,
        "episodes": 10,
        "rating": 7.8,
        "main_couple": "Sea D & Keen S",
        "poster": "posters/head2head.jpg",
        "synopsis": "Two competitive fashion students constantly clash in academics and personality, but their rivalry slowly turns into mutual and unexpected feelings as one of them is able to see what the future holds for them."
    },
    {
        "title": "Muteluv: Hi By My Luck",
        "country": "Thailand",
        "year": 2024,
        "episodes": 12,
        "rating": 7.7,
        "main_couple": "Sea D & Keen S",
        "poster": "posters/muteluv.jpg",
        "synopsis": "An academic overachiever meets his match when a new rival joins his class. Sent together for a high-stakes scholarship exam, a rattled fortune-teller's mysterious demands have him desperately trying to win over the cold and indifferent stranger."
    },
    {
        "title": "My School President",
        "country": "Thailand",
        "year": 2022,
        "episodes": 12,
        "rating": 8.7,
        "main_couple": "Gemini N & Fourth N",
        "poster": "posters/msp.jpg",
        "synopsis": "A student council president helps the music club leader save his club, and their partnership blossoms into a sweet romance."
    },
    {
        "title": "Fish Upon the Sky",
        "country": "Thailand",
        "year": 2021,
        "episodes": 12,
        "rating": 7.9,
        "main_couple": "Pond N & Phuwin T",
        "poster": "posters/futs.jpg",
        "synopsis": "A shy student transforms himself to impress his crush, only to find love where he least expects it."
    },
    {
        "title": "2gether: The Series",
        "country": "Thailand",
        "year": 2020,
        "episodes": 13,
        "rating": 8.0,
        "main_couple": "Bright & Win",
        "poster": "posters/2gether.jpg",
        "synopsis": "A fake relationship between two students gradually turns into real love."
    },
    {
        "title": "Bad Buddy",
        "country": "Thailand",
        "year": 2021,
        "episodes": 12,
        "rating": 9.0,
        "main_couple": "Ohm & Nanon",
        "poster": "posters/bb.jpg",
        "synopsis": "Two neighbours from rival families grow from enemies into lovers."
    },
    {
        "title": "Boys in Love",
        "country": "Thailand",
        "year": 2025,
        "episodes": 12,
        "rating": 8.2,
        "main_couple": "Luke & Mick, Chokun & Aston, Ken & Paul",
        "poster": "posters/boysinlove.jpg",
        "synopsis": "Three unlikely pairs navigate the fine line between rivalry and romance when an unlikely tutorship and a chance encounter turn their worlds upside down."
    },
    {
        "title": "We Are",
        "country": "Thailand",
        "year": 2024,
        "episodes": 16,
        "rating": 8.2,
        "main_couple": "Pond N & Phuwin T",
        "poster": "posters/weare.jpg",
        "synopsis": "A group of university students navigate friendships, relationships, and emotional growth."
    },
    {
        "title": "Spare Me Your Mercy",
        "country": "Thailand",
        "year": 2024,
        "episodes": 8,
        "rating": 8.2,
        "main_couple": "Tor & JJ",
        "poster": "posters/spare.jpg",
        "synopsis": "A detective's investigation into a string of suspicious deaths takes a dark turn when his growing feelings for a key suspect begin to blur the line between truth and desire."
    },
    {
        "title": "My Romance Scammer",
        "country": "Thailand",
        "year": 2026,
        "episodes": 12,
        "rating": 8.3,
        "main_couple": "Junior & Mark",
        "poster": "posters/mrs.jpg",
        "synopsis": "When two heirs to a vast fortune fall for a pair of cunning scammers, a web of deceit, hidden marriages, and stolen assets threatens to unravel everything — including their hearts."
    },
    {
        "title": "Not Me",
        "country": "Thailand",
        "year": 2021,
        "episodes": 14,
        "rating": 8.3,
        "main_couple": "Off & Gun",
        "poster": "posters/notme.jpg",
        "synopsis": "A man assumes his twin’s identity to uncover a conspiracy and forms a deep connection with a rebel leader."
    },
    {
        "title": "The Eclipse",
        "country": "Thailand",
        "year": 2022,
        "episodes": 12,
        "rating": 8.3,
        "main_couple": "First & Khao",
        "poster": "posters/theeclipse.jpg",
        "synopsis": "A rebellious student and a rule-following prefect uncover secrets at their strict school."
    },
    {
        "title": "Jack & Joker",
        "country": "Thailand",
        "year": 2024,
        "episodes": 12,
        "rating": 8.7,
        "main_couple": "Yin & War",
        "poster": "posters/jj.jpg",
        "synopsis": "When a charming thief and a reluctant enforcer are thrown together for an impossible heist, their clashing codes of honor prove harder to navigate than the job itself."
    },
    {
        "title": "ThamePo",
        "country": "Thailand",
        "year": 2024,
        "episodes": 12,
        "rating": 8.5,
        "main_couple": "William & Est",
        "poster": "posters/thamepo.jpg",
        "synopsis": "A documentarian gets more than footage when he becomes the unlikely confidant of a boy group's leader — whose imminent solo debut threatens to shatter the bonds holding his bandmates together."
    },
    {
        "title": "Manner of Death",
        "country": "Thailand",
        "year": 2020,
        "episodes": 14,
        "rating": 8.4,
        "main_couple": "Max & Tul",
        "poster": "posters/mod.jpg",
        "synopsis": "A coroner investigates a suspicious death and uncovers a dangerous conspiracy."
    },
    {
        "title": "Memoir of Rati",
        "country": "Thailand",
        "year": 2025,
        "episodes": 12,
        "rating": 8.2,
        "main_couple": "Great & Inn",
        "poster": "posters/mor.jpg",
        "synopsis": "In early 20th century Thailand, love and friendship dare to cross the rigid boundaries of class and status — but society is rarely so forgiving."
    },
    {
        "title": "Only Friends",
        "country": "Thailand",
        "year": 2023,
        "episodes": 12,
        "rating": 8.3,
        "main_couple": "First & Khao, Force & Book, Neo & Mark",
        "poster": "posters/of.jpg",
        "synopsis": "A group of friends navigate complicated relationships filled with jealousy, love, and emotional conflict."
    }
]


def save_seed_dataset():
    os.makedirs("data", exist_ok=True)
    with open("data/dramas.json", "w", encoding="utf-8") as f:
        json.dump(SEED_DRAMAS, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(SEED_DRAMAS)} seed dramas to data/dramas.json")


if __name__ == "__main__":
    save_seed_dataset()