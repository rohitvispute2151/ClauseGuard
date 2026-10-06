from enum import StrEnum


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ALREADY_EXISTS = "ALREADY_EXISTS"


class ExtractionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ClauseType(StrEnum):
    TERMINATION = "termination"
    LIABILITY_CAP = "liability_cap"
    INDEMNITY = "indemnity"
    AUTO_RENEWAL = "auto_renewal"
    GOVERNING_LAW = "governing_law"
    CONFIDENTIALITY = "confidentiality"
    IP_OWNERSHIP = "ip_ownership"
    NON_COMPETE = "non_compete"
    FORCE_MAJEURE = "force_majeure"
    ASSIGNMENT = "assignment"


class LLMProviderName(StrEnum):
    GEMINI = "gemini"
    GROQ = "groq"


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


# Magic numbers & system limits
MAX_PDF_SIZE_MB = 50
MAX_QUESTION_LENGTH = 2000
MIN_QUESTION_LENGTH = 5
MAX_CLAUSE_TYPES_PER_REQUEST = 10
RRF_K = 60
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64
DEFAULT_CONTEXT_TOKEN_BUDGET = 6000
DEFAULT_RETRIEVAL_LIMIT = 5
DEFAULT_EXTRACTION_CONCURRENCY = 4
DEFAULT_MAX_REPAIR_ATTEMPTS = 2
DEFAULT_SIMILARITY_THRESHOLD = 0.80
