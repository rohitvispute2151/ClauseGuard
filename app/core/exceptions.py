class ClauseGuardException(Exception):
    """Base domain exception."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DocumentNotFoundError(ClauseGuardException):
    """Raised when a document is not found."""


class DocumentProcessingError(ClauseGuardException):
    """Raised when document ingestion fails."""


class LLMProviderError(ClauseGuardException):
    """Raised when an LLM provider returns an unrecoverable error."""


class CircuitOpenError(ClauseGuardException):
    """Raised when the circuit breaker is open."""


class ExtractionValidationError(ClauseGuardException):
    """Raised when structured extraction schema validation fails after repair attempts."""


class RateLimitExceededError(ClauseGuardException):
    """Raised when the rate limit is exceeded."""

    def __init__(self, retry_after: float):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")
        self.retry_after = retry_after
