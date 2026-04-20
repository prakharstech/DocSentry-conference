"""
PII detection and anonymization module.

Supports three privacy levels:
  - SYNTHETIC  : Replace PII with realistic fake data (names, SSNs, dates) via Faker.
                 Highest utility, moderate privacy.
  - GENERALIZE : Replace PII with category tags like [PERSON], [DATE], [SSN].
                 Balanced utility and privacy. (Default)
  - REDACT     : Replace all PII with [REDACTED]. Maximum privacy, minimum utility.
"""

import re
import logging
import random
from typing import Tuple, List, Dict

from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent

logger = logging.getLogger(__name__)

# Singletons
_scanner = None
_strategy = None
_masker = None

# Medical conditions for synthetic generation
_MEDICAL_CONDITIONS = [
    "Hypertension", "Type 2 Diabetes", "Pneumonia", "Chronic Kidney Disease",
    "Congestive Heart Failure", "Severe Migraine", "Acute Appendicitis",
    "Atrial Fibrillation", "Major Depressive Disorder", "Rheumatoid Arthritis",
    "Asthma", "Epilepsy", "Osteoporosis", "COPD", "Glaucoma"
]

# Privacy level constants
PRIVACY_LEVEL_SYNTHETIC = "SYNTHETIC"
PRIVACY_LEVEL_GENERALIZE = "GENERALIZE"
PRIVACY_LEVEL_REDACT = "REDACT"
VALID_PRIVACY_LEVELS = {PRIVACY_LEVEL_SYNTHETIC, PRIVACY_LEVEL_GENERALIZE, PRIVACY_LEVEL_REDACT}


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


def detect_pii(text: str) -> List[Dict]:
    """
    Detect PII entities in text using the ScannerAgent (LLM-based NER).
    Returns:
        List of PII entity dicts with text_segment, pii_type, risk_level, reasoning.
    """
    scanner = _get_scanner()
    result = scanner.scan(text)
    return result.get("findings", [])


# ---------------------------------------------------------------------------
# Synthetic replacement helpers
# ---------------------------------------------------------------------------

def _get_faker():
    """Lazy import Faker to avoid hard dependency at module load."""
    try:
        from faker import Faker
        return Faker()
    except ImportError:
        return None


def _synthetic_replacement(pii_type: str, fake) -> str:
    """Generate a realistic replacement for a given PII type."""
    if fake is None:
        # Fallback if Faker not installed
        return f"[{pii_type}]"
    type_map = {
        "PERSON":    lambda: fake.name(),
        "SSN":       lambda: fake.ssn(),
        "DATE":      lambda: fake.date(),
        "LOCATION":  lambda: fake.city(),
        "CONTACT":   lambda: fake.phone_number() if random.random() > 0.5 else fake.email(),
        "CONDITION": lambda: random.choice(_MEDICAL_CONDITIONS),
    }
    generator = type_map.get(pii_type.upper())
    return generator() if generator else f"[{pii_type}]"


# ---------------------------------------------------------------------------
# Core anonymization functions
# ---------------------------------------------------------------------------

def anonymize_text(text: str, pii_entities: List[Dict], privacy_level: str = PRIVACY_LEVEL_GENERALIZE) -> str:
    """
    Replace detected PII in text according to the selected privacy level.

    Args:
        text:           Original text containing PII.
        pii_entities:   List of PII entities from detect_pii().
        privacy_level:  One of SYNTHETIC, GENERALIZE, REDACT.

    Returns:
        Anonymized text string.
    """
    if not pii_entities:
        return text

    privacy_level = privacy_level.upper() if privacy_level else PRIVACY_LEVEL_GENERALIZE
    if privacy_level not in VALID_PRIVACY_LEVELS:
        logger.warning(f"Unknown privacy level '{privacy_level}', defaulting to GENERALIZE.")
        privacy_level = PRIVACY_LEVEL_GENERALIZE

    fake = _get_faker() if privacy_level == PRIVACY_LEVEL_SYNTHETIC else None

    # Synthetic strategy uses a consistency map so the same original value
    # always gets the same synthetic replacement within a session.
    consistency_map: Dict[str, str] = {}

    anonymized = text
    replacements = []

    for entity in pii_entities:
        segment = entity.get("text_segment", "")
        pii_type = entity.get("pii_type", "PII")

        if not segment:
            continue

        # Determine replacement tag based on privacy level
        if privacy_level == PRIVACY_LEVEL_REDACT:
            placeholder = "[REDACTED]"

        elif privacy_level == PRIVACY_LEVEL_SYNTHETIC:
            # Reuse existing synthetic value if same text was already mapped
            if segment in consistency_map:
                placeholder = consistency_map[segment]
            else:
                placeholder = _synthetic_replacement(pii_type, fake)
                consistency_map[segment] = placeholder

        else:  # GENERALIZE (default)
            placeholder = f"[{pii_type.upper()}]"

        # Find all occurrences of this segment in the current anonymized text
        start = 0
        while True:
            idx = anonymized.find(segment, start)
            if idx == -1:
                break
            replacements.append((idx, idx + len(segment), placeholder))
            start = idx + len(segment)

    # Sort by start position descending to avoid index shifting
    replacements.sort(key=lambda x: x[0], reverse=True)

    # Remove overlapping replacements (keep the first encountered)
    filtered = []
    last_start = len(anonymized)
    for start, end, placeholder in replacements:
        if end <= last_start:
            filtered.append((start, end, placeholder))
            last_start = start

    for start, end, placeholder in filtered:
        anonymized = anonymized[:start] + placeholder + anonymized[end:]

    logger.info(f"anonymize_text: {len(filtered)} replacements applied (level={privacy_level})")
    return anonymized


def detect_and_anonymize(text: str, privacy_level: str = PRIVACY_LEVEL_GENERALIZE) -> Tuple[str, List[Dict]]:
    """
    Combined pipeline: scan → anonymize.
    Supports all three privacy levels.

    Returns:
        Tuple of (anonymized_text, detected_pii_entities)
    """
    findings = detect_pii(text)
    if not findings:
        return text, []

    anonymized = anonymize_text(text, findings, privacy_level=privacy_level)
    return anonymized, findings


def reset_anonymizer():
    """Clear consistency maps and state."""
    masker = _get_masker()
    masker.reset_consistency_map()
