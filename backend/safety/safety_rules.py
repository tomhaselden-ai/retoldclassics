import re
from dataclasses import dataclass


@dataclass
class SafetyEvaluation:
    safety_score: int
    classification: str
    flags: list[str]
    matched_terms: list[str]


BLOCKED_PATTERNS: dict[str, list[str]] = {
    "graphic_violence": [
        r"\bkill\b",
        r"\bkilled\b",
        r"\bmurder\b",
        r"\bblood\b",
        r"\bstab\b",
        r"\bshoot\b",
        r"\bweapon\b",
    ],
    "sexual_content": [
        r"\bsex\b",
        r"\bnaked\b",
        r"\bkissed passionately\b",
    ],
    "self_harm": [
        r"\bsuicide\b",
        r"\bself-harm\b",
        r"\bhurt myself\b",
    ],
}

REVIEW_PATTERNS: dict[str, list[str]] = {
    "frightening_content": [
        r"\bmonster\b",
        r"\bscary\b",
        r"\bterrifying\b",
        r"\bhaunted\b",
        r"\bdark cave\b",
    ],
    "harmful_behavior": [
        r"\bfight\b",
        r"\bhit\b",
        r"\btrick(ed|ing)?\b",
        r"\bsteal\b",
        r"\blie\b",
    ],
    "unsafe_situations": [
        r"\babandoned\b",
        r"\blost alone\b",
        r"\bdangerous\b",
        r"\btrapped\b",
        r"\bfire\b",
    ],
}


def _normalize_text(text: str) -> str:
    return text.lower().strip()


def _find_matches(text: str, patterns: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    matched_flags: list[str] = []
    matched_terms: list[str] = []
    for flag, rule_list in patterns.items():
        matched_for_flag = False
        for pattern in rule_list:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                matched_terms.append(match.group(0))
                matched_for_flag = True
        if matched_for_flag:
            matched_flags.append(flag)
    return matched_flags, matched_terms


def evaluate_text_safety(text: str) -> SafetyEvaluation:
    normalized = _normalize_text(text)
    if not normalized:
        return SafetyEvaluation(
            safety_score=100,
            classification="approved",
            flags=[],
            matched_terms=[],
        )

    blocked_flags, blocked_terms = _find_matches(normalized, BLOCKED_PATTERNS)
    review_flags, review_terms = _find_matches(normalized, REVIEW_PATTERNS)

    score = 100
    score -= min(70, len(blocked_terms) * 25)
    score -= min(30, len(review_terms) * 8)
    score = max(0, score)

    if blocked_flags:
        classification = "blocked"
    elif review_flags:
        classification = "review_required"
    else:
        classification = "approved"

    combined_flags = blocked_flags + [flag for flag in review_flags if flag not in blocked_flags]
    combined_terms = blocked_terms + [term for term in review_terms if term not in blocked_terms]

    return SafetyEvaluation(
        safety_score=score,
        classification=classification,
        flags=combined_flags,
        matched_terms=combined_terms,
    )
