import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from llm.client import LLMClient


def test_generate_calls_api():
    """generate() sends a POST to /chat/completions and returns the response text."""
    client = LLMClient(api_key="test", base_url="https://api.siliconflow.cn/v1",
                       chat_model="test-model", embedding_model="test-embed")
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"output": "hello"}'}}]
        }
        mock_post.return_value = mock_resp
        result = client.generate("test prompt")
        assert result == '{"output": "hello"}'
        assert "chat/completions" in mock_post.call_args[0][0]


def test_get_embedding():
    """get_embedding() sends a POST to /embeddings with dimensions param and returns the vector."""
    client = LLMClient(api_key="test", base_url="https://api.siliconflow.cn/v1",
                       chat_model="test-model", embedding_model="test-embed")
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        mock_post.return_value = mock_resp
        result = client.get_embedding("hello world")
        assert len(result) == 3
        assert result[0] == 0.1
        assert "embeddings" in mock_post.call_args[0][0]
        # Verify dimensions parameter is sent
        call_payload = mock_post.call_args[1]['json']
        assert call_payload['dimensions'] == 1024


def test_generate_retries_on_failure():
    """generate() retries when the API returns non-200 status."""
    client = LLMClient(api_key="test", base_url="https://api.siliconflow.cn/v1",
                       chat_model="test-model", embedding_model="test-embed")
    with patch('requests.post') as mock_post, patch('time.sleep'):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        mock_post.side_effect = [fail_resp, ok_resp]
        result = client.generate("test")
        assert result == "ok"
        assert mock_post.call_count == 2


def test_get_embedding_empty_text():
    """get_embedding() handles empty text by using a placeholder."""
    client = LLMClient(api_key="test", base_url="https://api.siliconflow.cn/v1",
                       chat_model="test-model", embedding_model="test-embed")
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"embedding": [0.5]}]}
        mock_post.return_value = mock_resp
        result = client.get_embedding("")
        assert result == [0.5]
        call_payload = mock_post.call_args[1]['json']
        assert call_payload['input'] == "this is blank"
