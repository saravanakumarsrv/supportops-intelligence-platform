"""
Lesson purpose:
This file converts customer text into a simple sentiment label.

Why?
Support teams need to know which customers sound angry or unhappy.
In a real company this could use an ML model. For portfolio Version 1,
we use transparent rule-based NLP so recruiters can understand the logic.
"""
from __future__ import annotations
NEGATIVE_WORDS = ["frustrating", "tired", "unhappy", "cancel", "nobody", "immediately", "waiting", "affecting"]
POSITIVE_WORDS = ["thanks", "thank", "helpful", "appreciate", "quick", "well"]

def sentiment_score(message: str) -> int:
    text = str(message).lower()
    score = 0
    for word in POSITIVE_WORDS:
        if word in text:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in text:
            score -= 1
    return score

def sentiment_label(message: str) -> str:
    score = sentiment_score(message)
    if score <= -2:
        return "Very Negative"
    if score == -1:
        return "Negative"
    if score == 0:
        return "Neutral"
    return "Positive"
