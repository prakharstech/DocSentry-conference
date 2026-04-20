"""Pydantic models for all API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List


# ---------------------------------------------------------------------------
# Privacy Level Enum (as string constant)
# ---------------------------------------------------------------------------
# SYNTHETIC  — realistic fake replacements (highest utility)
# GENERALIZE — [PERSON], [DATE], [SSN] tags (balanced)
# REDACT     — [REDACTED] for all PII (maximum privacy)

PRIVACY_LEVELS = ["SYNTHETIC", "GENERALIZE", "REDACT"]


# ---------------------------------------------------------------------------
# PII Entity Models
# ---------------------------------------------------------------------------

class PIIEntity(BaseModel):
    text_segment: str = Field(..., description="The exact text containing PII")
    pii_type: str = Field(..., description="PII category: PERSON, LOCATION, DATE, CONDITION, CONTACT, SSN")
    risk_level: str = Field(default="Medium", description="Risk level: Critical, High, Medium, Low")
    reasoning: str = Field(default="", description="Why this was classified as PII")


class GroundTruthPII(BaseModel):
    text: str
    type: str  # PERSON, LOCATION, DATE, CONDITION, CONTACT, SSN


# ---------------------------------------------------------------------------
# Upload / Query Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=4, description="Number of chunks to retrieve")


class QueryResponse(BaseModel):
    answer: str
    source_chunks: List[dict] = []
    anonymized: bool = True
    pattern_based: List[dict] = []


class UploadResponse(BaseModel):
    status: str
    message: str
    pii_count: int = 0
    pii_types: List[str] = []
    anonymized: bool = True
    privacy_level: str = "GENERALIZE"
    raw_text: Optional[str] = None
    anonymized_text: Optional[str] = None
    findings: List[dict] = []


# ---------------------------------------------------------------------------
# Evaluation Models
# ---------------------------------------------------------------------------

class PIIDetectionRequest(BaseModel):
    original_text: str
    ground_truth_pii: List[GroundTruthPII]


class PIIDetectionResponse(BaseModel):
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    # Bug 3 fix: renamed from false_positive_rate (was computing 1 - Precision)
    over_detection_rate: float = 0.0
    anonymized_text: str = ""
    per_category: dict = {}   # {category: {precision, recall, f1}}
    confusion_matrix: List = []
    total_ground_truth: int = 0
    total_detected: int = 0


class AnonymizationEvalRequest(BaseModel):
    original_text: str
    anonymized_text: str
    detected_pii: List[PIIEntity] = []
    privacy_level: str = Field(default="GENERALIZE", description="SYNTHETIC | GENERALIZE | REDACT")


class AnonymizationEvalResponse(BaseModel):
    redaction_coverage: float
    pii_leakage_detected: bool
    leaked_entities: List[str] = []
    k_anonymity: Optional[int] = None
    adversarial_success_rate: Optional[float] = None
    utility_score: Optional[int] = None
    fidelity_rating: Optional[str] = None
    privacy_level: str = "GENERALIZE"


class RAGEvalRequest(BaseModel):
    query: str
    response: str
    expected_answer: str = ""
    context_chunks: List[str] = []
    ground_truth_chunk_indices: List[int] = []


class RAGEvalResponse(BaseModel):
    relevancy_score: float
    groundedness_score: float
    relevancy_reasoning: str = ""
    groundedness_reasoning: str = ""
    # Bug 5 fix: these can be None when ground truth IDs not provided
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None


class OverallSystemEvalResponse(BaseModel):
    pii_detection_f1: float
    redaction_coverage: float
    inference_risk: float
    retrieval_accuracy: Optional[float] = None   # None = not measured
    llm_response_quality: float
    end_to_end_leakage_rate: float               # renamed from end_to_end_f1
    query_accuracy: float
    over_detection_rate: float = 0.0             # Bug 3 fix: renamed from false_positive_rate
    false_negative_rate: float
    privacy_score: float = 0.0
    composite_utility_score: float = 0.0
    privacy_level: str = "GENERALIZE"


# ---------------------------------------------------------------------------
# Experiment Models
# ---------------------------------------------------------------------------

class ExperimentRequest(BaseModel):
    num_samples: int = Field(default=5, ge=1, le=50, description="Number of synthetic records")
    document_text: Optional[str] = None
    privacy_level: str = Field(
        default="GENERALIZE",
        description="SYNTHETIC (fake data) | GENERALIZE ([TYPE] tags) | REDACT ([REDACTED])"
    )


class ExperimentResult(BaseModel):
    sample_index: int
    original_text: str
    masked_text: str
    ground_truth_count: int
    detected_count: int
    precision: float
    recall: float
    privacy_level: str = "GENERALIZE"

    # Group A - Privacy
    f1_score: float
    false_negative_rate: float = 0.0
    over_detection_rate: float = 0.0          # Bug 3 fix: renamed
    redaction_coverage: float = 0.0
    adversarial_success: bool = False

    # Group B - Utility
    retrieval_accuracy: Optional[float] = None   # Bug 5 fix: None when unmeasured
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    relevancy_score: float = 0.0
    groundedness_score: float = 0.0
    query_accuracy: float = 0.0
    end_to_end_leakage: bool = False

    # Extras and composites
    strategy_used: List[dict] = []
    utility_score: int = 0
    consistency_score: float = 0.0
    privacy_score: float = 0.0
    composite_utility_score: float = 0.0


class ExperimentResponse(BaseModel):
    status: str
    num_samples: int
    privacy_level: str = "GENERALIZE"
    results: List[ExperimentResult] = []

    # Aggregate Metrics (9 parameters + composites)
    false_negative_rate: float = 0.0
    over_detection_rate: float = 0.0           # Bug 3 fix: renamed
    redaction_coverage: float = 0.0
    retrieval_accuracy: Optional[float] = None # Bug 5 fix: None when unmeasured
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    relevancy_score: float = 0.0
    groundedness_score: float = 0.0
    end_to_end_leakage: float = 0.0
    privacy_score: float = 0.0
    composite_utility_score: float = 0.0

    aggregate_metrics: dict = {}
