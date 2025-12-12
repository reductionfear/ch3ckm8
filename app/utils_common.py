from fastapi import HTTPException
from typing import List
import random


def validate_api_key(key: str, valid_keys: List[str]):
    if key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")


def parse_card(cards: str):
    parts = cards.split("|")
    if len(parts) != 4:
        raise HTTPException(
            status_code=400, detail="Invalid card format (expected CC|MM|YY|CVV)"
        )
    cc, mm, yy, cvv = [p.strip() for p in parts]
    if len(yy) == 2:
        yy = f"20{yy}"
    return cc, mm, yy, cvv


def pick_site(site: str, builtin_code: str, pool: list[str]) -> str:
    if site == builtin_code:
        if not pool:
            return builtin_code
        return random.choice(pool)
    return site
