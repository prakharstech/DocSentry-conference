"""Pydantic models for all API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional


# --- PII Entity Models ---

class PIIEntity(BaseModel):
    text_segment: str = Field(..., description="The exact text containing PII")
    pii_type: str = Field(..., description="PII category: PERSON, LOCATION, DATE, CONDITION, CONTACT, SSN")
    risk_level: str = Field(default="Medium", description="Risk level: Critical, High, Medium, Low")
    reasoning: str = Field(default="", description="Why this was classified as PII")


class GroundTruthPII(BaseModel):
    text: str
    type: str  # PERSON, LOCATION, DATE, CONDITION, CONTACT, SSN


# --- Upload/Query Models ---

class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=4, description="Number of chunks to retrieve")


class QueryResponse(BaseModel):
    answer: str
    source_chunks: list[dict] = []
    anonymized: bool = True
    pattern_based: list[dict] = []


class UploadResponse(BaseModel):
    status: str
    message: str
    pii_count: int = 0
    pii_types: list[str] = []
    anonymized: bool = True
    raw_text: Optional[str] = None
    findings: list[dict] = []


# --- Evaluation Models ---

class PIIDetectionRequest(BaseModel):
    original_text: str
    ground_truth_pii: list[GroundTruthPII]


class PIIDetectionResponse(BaseModel):
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    false_positive_rate: float
    anonymized_text: str = ""
    per_category: dict = {}  # {category: {precision, recall, f1}}
    confusion_matrix: list = []
    total_ground_truth: int = 0
    total_detected: int = 0


class AnonymizationEvalRequest(BaseModel):
    original_text: str
    anonymized_text: str
    detected_pii: list[PIIEntity] = []


class AnonymizationEvalResponse(BaseModel):
    redaction_coverage: float
    pii_leakage_detected: bool
    leaked_entities: list[str] = []
    k_anonymity: Optional[int] = None
    adversarial_success_rate: Optional[float] = None
    utility_score: Optional[int] = None
    fidelity_rating: Optional[str] = None


class RAGEvalRequest(BaseModel):
    query: str
    response: str
    expected_answer: str = ""
    context_chunks: list[str] = []
    ground_truth_chunk_indices: list[int] = []


class RAGEvalResponse(BaseModel):
    relevancy_score: float
    groundedness_score: float
    relevancy_reasoning: str = ""
    groundedness_reasoning: str = ""
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None


class OverallSystemEvalResponse(BaseModel):
    pii_detection_f1: float
    redaction_coverage: float
    inference_risk: float
    retrieval_accuracy: float
    llm_response_quality: float
    end_to_end_f1: float
    query_accuracy: float
    false_positive_rate: float
    false_negative_rate: float


# --- Experiment Models ---

class ExperimentRequest(BaseModel):
    num_samples: int = Field(default=5, ge=1, le=50, description="Number of synthetic records")


class ExperimentResult(BaseModel):
    sample_index: int
    original_text: str
    masked_text: str
    ground_truth_count: int
    detected_count: int
    precision: float
    recall: float
    f1_score: float
    strategy_used: list[dict] = []
    adversarial_success: bool = False
    utility_score: int = 0
    consistency_score: float = 0.0


class ExperimentResponse(BaseModel):
    status: str
    num_samples: int
    results: list[ExperimentResult] = []
    aggregate_metrics: dict = {}
