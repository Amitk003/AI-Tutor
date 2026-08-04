"""Quick verification of the LLM client against a local mock API server.

Run with: python -m tests.mock_llm_check
This does not need a real API key.
"""

import json
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from backend import config
from backend.llm import LLMClient


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))

        # The client calls /v1/embeddings and /v1/chat/completions.
        path = self.path.removeprefix("/v1")

        if path == "/embeddings":
            inputs = payload["input"]
            if isinstance(inputs, str):
                inputs = [inputs]
            data = [
                {"index": i, "embedding": [float(i + 1), 0.5, -0.25]}
                for i in range(len(inputs))
            ]
            body = json.dumps({"data": data}).encode()
        elif path == "/chat/completions":
            content = "The answer is 42."
            body = json.dumps(
                {
                    "choices": [
                        {"message": {"role": "assistant", "content": content}}
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


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    config.LLM_API_KEY = "test-key"
    client = LLMClient(base_url=f"http://127.0.0.1:{port}/v1", api_key="test-key")

    vectors = client.embed(["hello", "world"])
    assert len(vectors) == 2 and len(vectors[0]) == 3, vectors
    print("embed ok:", vectors)

    single = client.embed_one("hi")
    assert single == [1.0, 0.5, -0.25]
    print("embed_one ok")

    answer = client.chat("be terse", "what is 6 times 7")
    assert answer == "The answer is 42."
    print("chat ok:", answer)

    assert client.ping() is True
    print("ping ok")

    # Error path: missing key must raise LLMError, not crash.
    from backend.llm import LLMError

    config.LLM_API_KEY = ""
    client_without_key = LLMClient(base_url=f"http://127.0.0.1:{port}/v1")
    try:
        client_without_key.embed_one("x")
        raise AssertionError("expected LLMError for missing key")
    except LLMError:
        print("missing-key error path ok")

    server.shutdown()
    print("ALL MOCK TESTS PASSED")


if __name__ == "__main__":
    main()
