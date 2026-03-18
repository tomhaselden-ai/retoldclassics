from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import yaml

from backend.config.settings import POLLY_LEXICON_NAMES, POLLY_PRONUNCIATION_DICTIONARY_PATH


@dataclass(frozen=True)
class PronunciationRule:
    alias: str | None = None
    phoneme: str | None = None
    alphabet: str = "ipa"


def load_lexicon_names() -> list[str]:
    return [item.strip() for item in POLLY_LEXICON_NAMES.split(",") if item.strip()]


def _coerce_rule(raw_rule: Any) -> PronunciationRule | None:
    if isinstance(raw_rule, str) and raw_rule.strip():
        return PronunciationRule(alias=raw_rule.strip())
    if isinstance(raw_rule, dict):
        alias = raw_rule.get("alias")
        phoneme = raw_rule.get("phoneme")
        alphabet = raw_rule.get("alphabet")
        if isinstance(alias, str) and alias.strip():
            return PronunciationRule(alias=alias.strip())
        if isinstance(phoneme, str) and phoneme.strip():
            normalized_alphabet = alphabet.strip() if isinstance(alphabet, str) and alphabet.strip() else "ipa"
            return PronunciationRule(phoneme=phoneme.strip(), alphabet=normalized_alphabet)
    return None


def load_pronunciation_rules(
    path: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, PronunciationRule]:
    resolved_path = Path(path or POLLY_PRONUNCIATION_DICTIONARY_PATH)
    rules: dict[str, PronunciationRule] = {}

    if resolved_path.exists():
        raw_payload: Any
        if resolved_path.suffix.lower() in {".yaml", ".yml"}:
            raw_payload = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
        else:
            raw_payload = json.loads(resolved_path.read_text(encoding="utf-8"))

        if isinstance(raw_payload, dict):
            for term, raw_rule in raw_payload.items():
                if not isinstance(term, str) or not term.strip():
                    continue
                rule = _coerce_rule(raw_rule)
                if rule is not None:
                    rules[term.strip()] = rule

    if overrides:
        for term, raw_rule in overrides.items():
            if not isinstance(term, str) or not term.strip():
                continue
            rule = _coerce_rule(raw_rule)
            if rule is not None:
                rules[term.strip()] = rule

    return rules


def apply_pronunciation_rules(text: str, rules: dict[str, PronunciationRule]) -> str:
    if not rules:
        return escape(text)

    normalized_text = text
    replacements: dict[str, str] = {}
    ordered_terms = sorted(rules.keys(), key=len, reverse=True)

    for index, term in enumerate(ordered_terms):
        rule = rules[term]
        placeholder = f"__PSU_PRON_RULE_{index}__"
        pattern = re.compile(rf"\b{re.escape(term)}\b", flags=re.IGNORECASE)
        if rule.alias:
            fragment = f'<sub alias="{escape(rule.alias)}">{escape(term)}</sub>'
        elif rule.phoneme:
            fragment = (
                f'<phoneme alphabet="{escape(rule.alphabet)}" ph="{escape(rule.phoneme)}">'
                f"{escape(term)}</phoneme>"
            )
        else:
            continue

        if not pattern.search(normalized_text):
            continue
        normalized_text = pattern.sub(placeholder, normalized_text)
        replacements[placeholder] = fragment

    escaped = escape(normalized_text)
    for placeholder, fragment in replacements.items():
        escaped = escaped.replace(placeholder, fragment)
    return escaped
