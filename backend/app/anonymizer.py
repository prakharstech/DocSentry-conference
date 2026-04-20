"""PII detection and anonymization module using ScannerAgent."""

import re
import logging
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent

logger = logging.getLogger(__name__)

# Singletons
_scanner = None
_strategy = None
_masker = None


def _get_scanner() -> ScannerAgent:
    global _scanner
    if _scanner is None:
        _scanner = ScannerAgent()
    return _scanner


def _get_strategy() -> StrategyAgent:
    global _strategy
    if _strategy is None:
        _strategy = StrategyAgent()
    return _strategy


def _get_masker() -> MaskingAgent:
    global _masker
    if _masker is None:
        _masker = MaskingAgent()
    return _masker


def detect_pii(text: str) -> list[dict]:
    """
    Detect PII entities in text using the ScannerAgent (LLM-based NER).

    Returns:
        List of PII entity dicts with text_segment, pii_type, risk_level, reasoning.
    """
    scanner = _get_scanner()
    result = scanner.scan(text)
    return result.get("findings", [])


def anonymize_text(text: str, pii_entities: list[dict]) -> str:
    """
    Replace detected PII with [PII_TYPE] placeholders.
    Processes entities from last to first to avoid offset issues.

    Args:
        text: Original text
        pii_entities: List of PII entities from detect_pii()

    Returns:
        Anonymized text with PII replaced by placeholders.
    """
    if not pii_entities:
        return text

    anonymized = text

    # Sort entities by their position in text (last first) to avoid index shifting
    # We find each entity's position and replace from end to start
    replacements = []
    for entity in pii_entities:
        segment = entity.get("text_segment", "")
        pii_type = entity.get("pii_type", "PII")
        if segment:
            # Find all occurrences
            start = 0
            while True:
                idx = anonymized.find(segment, start)
                if idx == -1:
                    break
                replacements.append((idx, idx + len(segment), f"[{pii_type}]"))
                start = idx + len(segment)

    # Sort by start position descending (replace from end first)
    replacements.sort(key=lambda x: x[0], reverse=True)

    # Remove overlapping replacements (keep the first one found)
    filtered = []
    last_start = len(anonymized)
    for start, end, placeholder in replacements:
        if end <= last_start:
            filtered.append((start, end, placeholder))
            last_start = start

    for start, end, placeholder in filtered:
        anonymized = anonymized[:start] + placeholder + anonymized[end:]

    logger.info(f"Anonymized {len(filtered)} PII entities in text")
    return anonymized


def detect_and_anonymize(text: str) -> tuple[str, list[dict]]:
    """
    Combined pipeline: scan -> strategy -> mask.
    Preserves consistency via singleton MaskingAgent.

    Returns:
        Tuple of (anonymized_text, detected_pii_entities)
    """
    # 1. Scan
    findings = detect_pii(text)
    if not findings:
        return text, []

    # Use the deterministic string replacement function to guarantee explicit [TYPE] tags
    anonymized = anonymize_text(text, findings)
    
    return anonymized, findings


def reset_anonymizer():
    """Clear consistency maps and state."""
    masker = _get_masker()
    masker.reset_consistency_map()
