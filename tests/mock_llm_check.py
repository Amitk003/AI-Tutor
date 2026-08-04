"""Quick verification of the LLM clients against a local mock API server.

Run with: python -m tests.mock_llm_check
This does not need a real API key.

Covers both supported providers: OpenAI-compatible and Gemini.
"""

import json
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from backend import config
from backend.llm import (
    GeminiClient,
    LLMError,
    OpenAICompatibleClient,
)


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))

        # OpenAI-compatible paths.
        if self.path == "/v1/embeddings":
            inputs = payload["input"]
            if isinstance(inputs, str):
                inputs = [inputs]
            data = [
                {"index": i, "embedding": [float(i + 1), 0.5, -0.25]}
                for i in range(len(inputs))
            ]
            body = json.dumps({"data": data}).encode()
        elif self.path == "/v1/chat/completions":
            content = "The answer is 42."
            body = json.dumps(
                {
                    "choices": [
                        {"message": {"role": "assistant", "content": content}}
                    ]
                }
            ).encode()

        # Gemini paths.
        elif self.path.endswith(":batchEmbedContents"):
            values = []
            for i, _ in enumerate(payload["requests"]):
                values.append({"embedding": {"values": [float(i + 1), 0.5, -0.25]}})
            body = json.dumps({"embeddings": values}).encode()
        elif self.path.endswith(":generateContent"):
            content = "The answer is 42."
            body = json.dumps(
                {
                    "candidates": [
                        {"content": {"parts": [{"text": content}]}}
                    ]
                }
            ).encode()

        else:
            body = json.dumps({"error": "not found"}).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _test_openai(port: int) -> None:
    client = OpenAICompatibleClient(
        base_url=f"http://127.0.0.1:{port}/v1",
        api_key="test-key",
    )
    vectors = client.embed(["hello", "world"])
    assert len(vectors) == 2 and len(vectors[0]) == 3, vectors
    assert client.embed_one("hi") == [1.0, 0.5, -0.25]
    assert client.chat("be terse", "what is 6 times 7") == "The answer is 42."
    assert client.ping() is True
    print("openai client ok")


def _test_gemini(port: int) -> None:
    client = GeminiClient(
        base_url=f"http://127.0.0.1:{port}/v1beta",
        api_key="test-key",
    )
    vectors = client.embed(["hello", "world"])
    assert len(vectors) == 2 and len(vectors[0]) == 3, vectors
    assert client.embed_one("hi") == [1.0, 0.5, -0.25]
    assert client.chat("be terse", "what is 6 times 7") == "The answer is 42."
    assert client.ping() is True
    print("gemini client ok")


def _test_missing_key() -> None:
    config.LLM_API_KEY = ""
    try:
        OpenAICompatibleClient(base_url="http://127.0.0.1:1/v1").embed_one("x")
        raise AssertionError("expected LLMError for missing key")
    except LLMError:
        pass

    config.GEMINI_API_KEY = ""
    try:
        GeminiClient(base_url="http://127.0.0.1:1/v1beta").embed_one("x")
        raise AssertionError("expected LLMError for missing key")
    except LLMError:
        pass
    print("missing-key error paths ok")


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    _test_openai(port)
    _test_gemini(port)
    _test_missing_key()

    server.shutdown()
    print("ALL MOCK TESTS PASSED")


if __name__ == "__main__":
    main()
