from __future__ import annotations

from backend.utils import first_name


PROMPT_LIBRARY = {
    "episodic memory": {
        "domains": ["memory retrieval", "narrative detail"],
        "prompts": [
            "Tell me about a memorable family gathering and what stood out to you.",
            "Share a day from your past that still feels vivid to you.",
        ],
    },
    "sequencing": {
        "domains": ["sequencing", "organization"],
        "prompts": [
            "Walk through your morning routine step by step.",
            "Describe how you would get ready for a trip from start to finish.",
        ],
    },
    "emotional reflection": {
        "domains": ["reflection", "emotion labeling"],
        "prompts": [
            "Tell me about something that made you smile recently.",
            "Describe a recent moment that felt meaningful to you and why.",
        ],
    },
    "semantic recall": {
        "domains": ["semantic memory", "categorization"],
        "prompts": [
            "Tell me about a favorite place and what makes it special.",
            "Describe a hobby or topic you know well and what you enjoy about it.",
        ],
    },
    "narrative coherence": {
        "domains": ["coherence", "topic maintenance"],
        "prompts": [
            "Tell me about a trip you remember vividly, from beginning to end.",
            "Describe a recent outing and what happened in order.",
        ],
    },
    "procedural explanation": {
        "domains": ["procedural speech", "stepwise explanation"],
        "prompts": [
            "Describe how you prepare your favorite meal.",
            "Explain how you would teach someone to care for a garden or houseplant.",
        ],
    },
}


def generate_daily_prompt(patient_history: list[object], category_override: str | None = None, patient_name: str | None = None) -> dict:
    categories = list(PROMPT_LIBRARY.keys())
    last_category = next((session.prompt_category for session in patient_history if getattr(session, "prompt_category", "")), "")
    if category_override and category_override in PROMPT_LIBRARY:
        category = category_override
    else:
        category = next((name for name in categories if name != last_category), categories[0])

    bucket = PROMPT_LIBRARY[category]
    used_count = sum(1 for session in patient_history[:8] if getattr(session, "prompt_category", "") == category)
    prompt_text = bucket["prompts"][used_count % len(bucket["prompts"])]
    if patient_name:
        prompt_text = f"{first_name(patient_name)}, {prompt_text}"
    return {
        "prompt_text": prompt_text,
        "prompt_category": category,
        "targeted_domains": bucket["domains"],
        "available_categories": categories,
    }

