from __future__ import annotations

import json
import re
from collections import Counter


FILLER_PATTERNS = (
    ("um", r"\bum\b"),
    ("uh", r"\buh\b"),
    ("like", r"\blike\b"),
    ("you know", r"\byou know\b"),
    ("sort of", r"\bsort of\b"),
    ("kind of", r"\bkind of\b"),
    ("basically", r"\bbasically\b"),
    ("actually", r"\bactually\b"),
    ("i mean", r"\bi mean\b"),
    ("right", r"\bright\b"),
)

PRONOUNS = {
    "he", "she", "it", "they", "this", "that", "these", "those", "him", "her", "them", "his", "hers", "their",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "with", "at", "by", "from", "is", "are",
    "was", "were", "be", "been", "being", "i", "you", "we", "they", "he", "she", "it", "my", "our", "your",
}


def build_marker_evidence(transcript: str, markers: dict[str, float], acoustic_markers: dict[str, float]) -> dict[str, dict[str, str | int | float | list[str]]]:
    words = re.findall(r"\b[\w']+\b", transcript.lower())
    sentences = [segment.strip() for segment in re.split(r"[.!?]+", transcript) if segment.strip()]
    unique_words = len(set(words))
    total_words = len(words)
    word_counter = Counter(word for word in words if word not in STOPWORDS and len(word) > 2)
    repeated = [word for word, count in word_counter.most_common(3) if count > 1]

    filler_counts = {}
    total_fillers = 0
    for label, pattern in FILLER_PATTERNS:
        count = len(re.findall(pattern, transcript.lower()))
        if count:
            filler_counts[label] = count
            total_fillers += count

    pronoun_count = sum(1 for word in words if word in PRONOUNS)
    noun_proxy = sum(1 for word in words if word not in STOPWORDS and word not in PRONOUNS)
    sentence_lengths = [len(re.findall(r"\b[\w']+\b", sentence)) for sentence in sentences]
    longest_sentence = max(sentence_lengths) if sentence_lengths else 0
    shortest_sentence = min(sentence_lengths) if sentence_lengths else 0
    first_sentence = sentences[0][:90] + ("..." if len(sentences[0]) > 90 else "") if sentences else ""
    last_sentence = sentences[-1][:90] + ("..." if len(sentences[-1]) > 90 else "") if sentences else ""

    evidence = {
        "ttr_score": {
            "headline": f"Used {unique_words} unique words across {total_words} total words.",
            "detail": f"Repeated content words included {', '.join(repeated)}." if repeated else "Word choices were fairly varied without heavy repetition.",
        },
        "mlu_score": {
            "headline": f"Spoke in {len(sentences)} sentences, ranging from {shortest_sentence} to {longest_sentence} words.",
            "detail": f"Average sentence length came out to about {markers.get('mlu_score', 0):.1f} words.",
        },
        "filler_density": {
            "headline": f"Included {total_fillers} filler phrase{'s' if total_fillers != 1 else ''} in the transcript.",
            "detail": _format_filler_detail(filler_counts),
        },
        "idea_density": {
            "headline": f"Shared {len(sentences)} main thought unit{'s' if len(sentences) != 1 else ''} across {total_words} words.",
            "detail": "The score reflects how much information was packed into each part of the story.",
        },
        "referential_cohesion": {
            "headline": f"Used {pronoun_count} pronoun references and about {noun_proxy} specific naming words.",
            "detail": "Higher reliance on pronouns can make the narrative feel less specific.",
        },
        "semantic_coherence": {
            "headline": f"The narrative opened with “{first_sentence or 'No clear opening sentence found'}”.",
            "detail": f"It closed with “{last_sentence or 'No clear closing sentence found'}”.",
        },
        "words_per_minute": {
            "headline": f"Spoke at about {acoustic_markers.get('words_per_minute', 0):.0f} words per minute.",
            "detail": f"The recording lasted about {acoustic_markers.get('duration_seconds', 0) or 0:.1f} seconds." if acoustic_markers.get("duration_seconds") else "Speech pace was estimated from the recording duration and transcript length.",
        },
        "average_pause_duration": {
            "headline": f"Average pause length was about {acoustic_markers.get('average_pause_duration', 0):.2f} seconds.",
            "detail": f"Pause frequency was about {acoustic_markers.get('pause_frequency', 0):.1f} pauses per minute.",
        },
        "pause_frequency": {
            "headline": f"Detected about {acoustic_markers.get('pause_frequency', 0):.1f} pauses per minute.",
            "detail": f"Average pause length was about {acoustic_markers.get('average_pause_duration', 0):.2f} seconds.",
        },
        "pitch_variability": {
            "headline": f"Pitch variability measured about {acoustic_markers.get('pitch_variability', 0):.1f}.",
            "detail": f"Vocal energy averaged about {acoustic_markers.get('vocal_energy', 0):.3f}.",
        },
    }
    return evidence


def serialize_marker_evidence(evidence: dict) -> str:
    return json.dumps(evidence, sort_keys=True)


def _format_filler_detail(filler_counts: dict[str, int]) -> str:
    if not filler_counts:
        return "No common filler phrases stood out in this recording."
    top_items = [f"{count} {label}" for label, count in sorted(filler_counts.items(), key=lambda item: item[1], reverse=True)[:3]]
    return "Most noticeable fillers: " + ", ".join(top_items) + "."
