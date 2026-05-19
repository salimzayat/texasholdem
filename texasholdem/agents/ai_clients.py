"""Returns an LLM client for use as a poker decision engine.

Prefers a local Ollama instance; falls back to Anthropic (Claude) if Ollama
is unavailable or no models are installed.
"""

import os
PREFERRED_MODELS = os.getenv('PREFERRED_MODELS', "").split(',')

def get_ai_client():
    """Return (client, model) tuple, Ollama-first with Anthropic fallback."""
    client, model = _try_ollama()
    if client is not None:
        return client, model
    return _get_anthropic_client()


def _get_model_from_list(models, preferred_models=PREFERRED_MODELS):
    assert len(models) > 0
    if len(preferred_models) == 0:
        return models[0]
    for model in preferred_models:
        if model in preferred_models:
            return model
    return models[0]

# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

def _try_ollama():
    try:
        import ollama  # pip install ollama

        # Ping the local server and grab the first available model.
        models = ollama.list().get("models", [])
        if not models:
            return None, None

        model = _get_model_from_list([x['model'] for x in models], PREFERRED_MODELS)
        return ollama, model
    except Exception as e:
        print(e)
        return None, None


# ---------------------------------------------------------------------------
# Anthropic (cloud fallback)
# ---------------------------------------------------------------------------

def _get_anthropic_client():
    try:
        import anthropic  # pip install anthropic
    except ImportError as exc:
        raise RuntimeError(
            "Neither Ollama nor the 'anthropic' package is available. "
            "Install one: `pip install ollama` or `pip install anthropic`."
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Ollama is unavailable and ANTHROPIC_API_KEY is not set. "
            "Set the environment variable or start Ollama locally."
        )

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-sonnet-4-6"
    return client, model
