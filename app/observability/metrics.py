from prometheus_client import Counter, Histogram, Gauge

# API Request metrics
REQUEST_COUNT = Counter(
    "clauseguard_requests_total",
    "Total API requests handled",
    ["endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "clauseguard_request_latency_seconds",
    "Total API request latency in seconds",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# LLM metrics
LLM_CALLS_TOTAL = Counter(
    "clauseguard_llm_calls_total",
    "Total LLM calls dispatched",
    ["provider", "model", "endpoint"],
)

LLM_TOKENS_TOTAL = Counter(
    "clauseguard_llm_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "model", "direction"],
)

LLM_COST_USD_TOTAL = Counter(
    "clauseguard_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["provider", "model"],
)

# Pipeline metrics
EXTRACTION_REPAIR_ATTEMPTS = Histogram(
    "clauseguard_extraction_repair_attempts",
    "Distribution of repair loop attempts per clause",
    ["clause_type"],
    buckets=[0, 1, 2, 3],
)

CITATION_VERIFICATION_RATE = Gauge(
    "clauseguard_citation_verification_rate",
    "Rolling citation verification success rate (0.0 to 1.0)",
)

CIRCUIT_BREAKER_STATE = Gauge(
    "clauseguard_circuit_breaker_state",
    "Circuit breaker state: 0=CLOSED, 1=OPEN, 2=HALF_OPEN",
    ["provider"],
)
