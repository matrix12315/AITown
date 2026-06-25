"""
LLM Client — Multi-Provider API Wrapper with Fallback
=====================================================
Supports multiple API providers with automatic fallback:
1. SiliconFlow (primary)
2. DashScope / Alibaba (fallback)

When a model returns 403 (insufficient quota), automatically tries the next model.
When all models for a provider fail, falls back to the next provider.

Two core functions:
1. generate(prompt) → text response from chat model
2. get_embedding(text) → vector of numbers from embedding model

Provider configuration is imported from config.py (single source of truth).
"""
import requests
import time
from config import API_PROVIDERS


# Disable proxy for direct API access (SiliconFlow/DashScope don't need proxies)
PROXIES = {"http": None, "https": None}


class LLMClient:
    """
    Multi-provider LLM client with automatic fallback.

    Tries each model in order. If a 403 (insufficient quota) is returned,
    moves to the next model. If all models fail for a provider, tries the
    next provider.
    """
    def __init__(self):
        pass

    def _request_chat(self, provider, model, prompt, system_prompt=None):
        """Send a chat request to a specific provider/model."""
        if system_prompt is None:
            system_prompt = (
                "You are a character in a small-town simulation called the Ville. "
                "Stay in character. Respond only with the requested output format, "
                "no extra commentary."
            )
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_thinking": False,  # 7x faster; skip Qwen reasoning mode
        }
        resp = requests.post(
            f"{provider['base_url']}/chat/completions",
            headers=headers, json=payload, timeout=60, proxies=PROXIES
        )
        return resp

    def _request_embedding(self, provider, model, dimension, text):
        """Send an embedding request to a specific provider/model."""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text.replace("\n", " "),
            "dimensions": dimension,
        }
        resp = requests.post(
            f"{provider['base_url']}/embeddings",
            headers=headers, json=payload, timeout=30, proxies=PROXIES
        )
        return resp

    def generate(self, prompt, system_prompt=None, max_retries=3):
        """
        Generate text using chat model with provider/model fallback.

        Order: try each provider → try each model in that provider → retry on transient errors.
        On 403 (insufficient), skip to next model immediately.

        Args:
            prompt: user prompt text
            system_prompt: optional system prompt (defaults to English simulation prompt)
            max_retries: retry count per model on transient errors
        """
        for provider in API_PROVIDERS:
            if not provider["api_key"]:
                print(f"[LLM] Skipping {provider['name']} — API key not set")
                continue
            for model in provider["chat_models"]:
                for attempt in range(max_retries):
                    try:
                        print(f"[LLM] Calling {provider['name']}/{model} (attempt {attempt+1})")
                        resp = self._request_chat(provider, model, prompt, system_prompt)
                        if resp.status_code == 200:
                            print(f"[LLM] Success from {provider['name']}/{model}")
                            return resp.json()["choices"][0]["message"]["content"]
                        if resp.status_code == 403:
                            print(f"[LLM] 403 from {provider['name']}/{model}, trying next model")
                            break  # skip to next model
                        print(f"[LLM] HTTP {resp.status_code} from {provider['name']}/{model}: {resp.text[:200]}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"[LLM] Error from {provider['name']}/{model}: {e}")
                        if attempt == max_retries - 1:
                            break  # skip to next model
                        time.sleep(1)
        print("[LLM] All providers failed, returning None")
        return None

    def get_embedding(self, text, max_retries=3):
        """
        Get embedding vector with provider/model fallback.
        Returns a list of floats, or empty list on complete failure.
        """
        if not text:
            text = "this is blank"
        for provider in API_PROVIDERS:
            if not provider["api_key"]:
                continue
            for model, dimension in provider["embedding_models"]:
                for attempt in range(max_retries):
                    try:
                        print(f"[LLM] Embedding: {provider['name']}/{model}")
                        resp = self._request_embedding(provider, model, dimension, text)
                        if resp.status_code == 200:
                            return resp.json()["data"][0]["embedding"]
                        if resp.status_code == 403:
                            print(f"[LLM] 403 from {provider['name']}/{model}, trying next model")
                            break
                        print(f"[LLM] Embedding HTTP {resp.status_code}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"[LLM] Embedding error: {e}")
                        if attempt == max_retries - 1:
                            break
                        time.sleep(1)
        print("[LLM] All embedding providers failed")
        return []
