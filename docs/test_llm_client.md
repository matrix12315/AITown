# LLM Client Test Documentation

## What is LLMClient?
Multi-provider LLM client with automatic fallback. Supports SiliconFlow (primary) and DashScope (fallback). Tries each provider → each model → retries on transient errors. On 403 (insufficient quota), skips to next model immediately.

## Tests

### test_generate_calls_api
**Asserts:** Returns response text, called `/chat/completions`
**Why it passes:** Mock returns valid response; extracts `choices[0].message.content`

### test_get_embedding
**Asserts:** Returns [0.1, 0.2, 0.3], called `/embeddings`, sends `dimensions=1024`
**Why it passes:** Mock returns `{"data": [{"embedding": [...]}]}`; extracts `data[0].embedding`. Also verifies the `dimensions` parameter is included in the request payload.

### test_generate_retries_on_failure
**Asserts:** Returns "ok" after first attempt fails with 500
**Why it passes:** Catches non-200, sleeps (mocked), retries. Second attempt succeeds.

### test_get_embedding_empty_text
**Asserts:** Empty string → sends "this is blank"
**Why it passes:** `get_embedding()` replaces empty text before sending to API

### test_generate_fallback_on_403
**Asserts:** Returns "hello from fallback" when first provider returns 403
**Why it passes:** First call returns 403 (SiliconFlow), client skips to next provider (DashScope), second call returns 200. Verifies model fallback logic.

### test_get_embedding_fallback_on_403
**Asserts:** Returns [0.1, 0.2, 0.3] when first provider returns 403
**Why it passes:** First call returns 403 (SiliconFlow/Qwen3-Embedding-8B), client skips to next provider (DashScope/text-embedding-v3), second call returns 200.

### test_generate_returns_error_when_all_fail
**Asserts:** Returns "ERROR" when all providers/models return 403
**Why it passes:** All calls return 403, exhausts all providers and models, returns "ERROR" as final fallback.
