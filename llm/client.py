"""
LLM Client — SiliconFlow API Wrapper
=====================================
Provides two core capabilities:
1. generate(prompt) → text response from the chat model
2. get_embedding(text) → vector of numbers from the embedding model

The chat model (Qwen2.5-7B) is used for:
- Generating daily plans
- Creating reflections/insights
- Writing conversations between agents

The embedding model (bge-large-zh) is used for:
- Converting memory text into vectors for similarity search
- Comparing "how similar" two pieces of text are (cosine similarity)
"""
import requests
import time


class LLMClient:
    """
    Wrapper around SiliconFlow's OpenAI-compatible API.

    Usage:
        client = LLMClient(api_key="sk-xxx", base_url="https://api.siliconflow.cn/v1",
                           chat_model="Qwen/Qwen2.5-7B-Instruct",
                           embedding_model="BAAI/bge-large-zh-v1.5")
        response = client.generate("What should Isabella do today?")
        vector = client.get_embedding("Isabella is cooking breakfast")
    """
    def __init__(self, api_key, base_url, chat_model, embedding_model):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.chat_model = chat_model
        self.embedding_model = embedding_model

    def generate(self, prompt, max_retries=3):
        """
        Send a prompt to the chat model and get a text response.
        Returns the LLM's response as a string, or "ERROR" if all retries fail.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers, json=payload, timeout=60,
                    proxies={"http": None, "https": None}
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        return "ERROR"

    def get_embedding(self, text, max_retries=3):
        """
        Convert text into a vector for similarity comparison.
        Returns a list of floats, or empty list on failure.
        """
        if not text:
            text = "this is blank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.embedding_model,
            "input": text.replace("\n", " "),
            "dimensions": 1024,
        }
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/embeddings",
                    headers=headers, json=payload, timeout=30
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        return []
