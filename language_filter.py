# -*- coding: utf-8 -*-
"""
Simple inappropriate language filter for RO/EN.
Usage:
    from profanity_filter import is_inappropriate
    blocked, term = is_inappropriate(user_text)
    if blocked: ...
Design:
- Normalize text (diacritics -> base chars, lower)
- Map common leetspeak: 0->o, 1->i/l, 3->e, 4->a, 5->s, 7->t, @->a, $->s
- Remove punctuation; collapse long repeating characters
- Match against a compact blacklist (extend as needed)
"""
from __future__ import annotations
import re
import unicodedata
from typing import Tuple

LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "€": "e", "£": "l", "!": "i"
})

# Basic RO/EN list; extend safely for your app's policy
BLACKLIST = {
    # English common
    "fuck", "fucking", "motherfucker", "mf", "shit", "bullshit", "bastard",
    "asshole", "dick", "prick", "cunt", "slut", "whore", "retard",
    # Romanian common (non-exhaustive)
    "prost", "idiot", "bou", "tampit", "handicapat", "jegos", "nesimtit",
    "pula", "pizda", "muie", "futu", "futut", "fut", "curve", "curva", "panarama"
}

def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKD", s).lower()
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.translate(LEET_MAP)
    # Replace non-letters with spaces (allow Romanian diacritics)
    s = re.sub(r"[^a-zăâîșşţțoe ]+", " ", s)
    # Collapse long repeats (cooool -> cool)
    s = re.sub(r"(.)\1{2,}", r"\1\1", s)
    # Extra spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s

def is_inappropriate(text: str) -> Tuple[bool, str]:
    # Return (True, offending_term) if offensive language is detected; else (False, '').
    norm = normalize_text(text)
    tokens = set(norm.split())
    # Direct matches
    for w in BLACKLIST:
        if w in tokens:
            return True, w
    # Substring word-boundary matches (handles spacing/obfuscation)
    for w in BLACKLIST:
        if re.search(rf"\b{re.escape(w)}\b", norm):
            return True, w
    return False, ""
