# Token pricing table (FreeLLM.net providers offer free tiers, but we track token consumption)

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-flash-lite-latest": {
        "input_per_1k": 0.0004,   # Google AI Studio Free Tier (FreeLLM.net)
        "output_per_1k": 0.0025,
    },
    "openai/gpt-oss-120b": {
        "input_per_1k": 0.00017,   # Groq Free Tier (FreeLLM.net)
        "output_per_1k": 0.00060,
    },
    "default": {
        "input_per_1k": 0.0,
        "output_per_1k": 0.0,
    },
}


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost given model and token counts."""
    pricing = MODEL_PRICING.get(model_id, MODEL_PRICING["default"])
    cost = (input_tokens / 1000.0) * pricing["input_per_1k"] + (
        output_tokens / 1000.0
    ) * pricing["output_per_1k"]
    return round(cost, 6)
