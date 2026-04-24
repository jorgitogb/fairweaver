"""
FAIRweaver AI Client
Connects to external OpenAI-compatible API (SAIA) for intelligent mapping suggestions.
"""

import os
from openai import OpenAI
from typing import Any


SAIA_API_KEY = os.getenv("OPENAI_API_KEY")
SAIA_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://chat-ai.academiccloud.de/v1")
SAIA_MODEL = os.getenv("OPENAI_MODEL", "meta-llama-3.1-8b-instruct")


_client: OpenAI | None = None


def get_client() -> OpenAI | None:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        if not SAIA_API_KEY:
            return None
        _client = OpenAI(
            api_key=SAIA_API_KEY,
            base_url=SAIA_BASE_URL,
        )
    return _client


def is_available() -> bool:
    """Check if SAIA API is configured and available."""
    return bool(SAIA_API_KEY)


def generate_mapping_suggestion(
    source_fields: list[str],
    pivot_fields: list[tuple[str, bool]],
    source_format: str = "unknown",
    pivot_id: str = "unknown",
) -> str:
    """
    Generate mapping suggestions using SAIA.
    
    Args:
        source_fields: List of field paths from source document
        pivot_fields: List of (field_name, is_required) tuples from pivot
        source_format: Source format ID
        pivot_id: Target pivot ID
    
    Returns:
        JSON string with mapping suggestions
    """
    client = get_client()
    if not client:
        return ""
    
    required_fields = [f[0] for f in pivot_fields if f[1]]
    recommended_fields = [f[0] for f in pivot_fields if not f[1]]
    
    prompt = f"""You are a metadata mapping expert. Given a metadata source with these fields:
{', '.join(source_fields)}

Map them to the {pivot_id} pivot profile.
Required fields: {', '.join(required_fields)}
Recommended fields: {', '.join(recommended_fields)}

Return a JSON array of mapping rules in this format:
[{{"source": "field.path", "target": "pivot_field", "confidence": 0.0-1.0, "reason": "brief explanation"}}]

Only include mappings where confidence > 0.3. Return valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=SAIA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful metadata mapping assistant that outputs only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        return content or ""
    except Exception as e:
        print(f"SAIA API error: {e}")
        return ""


def suggest_missing_fields(
    current_data: dict,
    pivot_fields: list[tuple[str, bool]],
) -> list[dict[str, Any]]:
    """
    Suggest values for missing fields using SAIA.
    
    Args:
        current_data: Current metadata document
        pivot_fields: List of (field_name, is_required) tuples from pivot
    
    Returns:
        List of suggestions for missing fields
    """
    client = get_client()
    if not client:
        return []
    
    missing = [f[0] for f in pivot_fields if f[0] not in current_data]
    if not missing:
        return []
    
    prompt = f"""Given this metadata:
{current_data}

Suggest appropriate values for these missing fields:
{missing}

Return a JSON object with suggested values where you can reasonably infer them from the existing data.
For fields that cannot be inferred, omit them from the response.
Return valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=SAIA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful metadata assistant that outputs only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        if content:
            import json
            return json.loads(content)
    except Exception as e:
        print(f"SAIA API error: {e}")
    
    return []