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

    Fixes vs. original:
    - Uses re.sub(..., flags=re.IGNORECASE) so case mismatches are caught
    - Sorts entities by text length descending — replaces longer strings first
      (prevents "Sarah" from matching inside "Sarah Elizabeth Thornton" prematurely)
    - All occurrences of each entity are replaced in one pass (not just first)
    - Strips whitespace from detected segments before matching

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
    consistency_map: Dict[str, str] = {}

    # Sort longest-first so "Sarah Elizabeth Thornton" is replaced before "Sarah"
    # This prevents partial matches from leaving residual PII
    sorted_entities = sorted(
        [e for e in pii_entities if e.get("text_segment", "").strip()],
        key=lambda e: len(e.get("text_segment", "")),
        reverse=True
    )

    anonymized = text
    total_replacements = 0

    for entity in sorted_entities:
        segment = entity.get("text_segment", "").strip()
        pii_type = entity.get("pii_type", "PII")

        if not segment:
            continue

        # Determine replacement placeholder
        if privacy_level == PRIVACY_LEVEL_REDACT:
            placeholder = "[REDACTED]"

        elif privacy_level == PRIVACY_LEVEL_SYNTHETIC:
            if segment in consistency_map:
                placeholder = consistency_map[segment]
            else:
                placeholder = _synthetic_replacement(pii_type, fake)
                consistency_map[segment] = placeholder
            # Also map the stripped version for case-insensitive consistency
            if segment.lower() not in [k.lower() for k in consistency_map]:
                consistency_map[segment] = placeholder

        else:  # GENERALIZE
            placeholder = f"[{pii_type.upper()}]"

        # Case-insensitive replacement — catches all occurrences including
        # different capitalizations (e.g. "THORNTON" / "Thornton" / "thornton")
        try:
            pattern = re.escape(segment)
            new_text, count = re.subn(pattern, placeholder, anonymized, flags=re.IGNORECASE)
            if count > 0:
                anonymized = new_text
                total_replacements += count
            else:
                # Fallback: try with stripped punctuation from segment edges
                # (LLM sometimes includes trailing period or comma)
                segment_stripped = re.sub(r'^[^\w]+|[^\w]+$', '', segment)
                if segment_stripped and segment_stripped != segment:
                    pattern2 = re.escape(segment_stripped)
                    new_text2, count2 = re.subn(pattern2, placeholder, anonymized, flags=re.IGNORECASE)
                    if count2 > 0:
                        anonymized = new_text2
                        total_replacements += count2
        except re.error as e:
            logger.warning(f"Regex error for segment '{segment}': {e} — skipping")
            continue

    logger.info(f"anonymize_text: {total_replacements} replacements applied (level={privacy_level})")
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
