"""
Development Environment Service Connectivity Checker.
Verifies connection to PostgreSQL, Redis, Qdrant, and Ollama.
"""

import sys
import asyncio
import socket
import urllib.request
import json
from backend.config import settings


def check_port(host: str, port: int, service_name: str) -> bool:
    """Check if TCP port is open and listening."""
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        print(f"[OK] {service_name} listening at {host}:{port}")
        return True
    except Exception as e:
        print(f"[FAILED] {service_name} unreachable at {host}:{port} ({e})")
        return False


def check_http(url: str, service_name: str) -> bool:
    """Check if HTTP endpoint responds cleanly."""
    try:
        req = urllib.request.urlopen(url, timeout=3)
        status = req.getcode()
        if status in (200, 204):
            print(f"[OK] {service_name} HTTP API healthy at {url}")
            return True
        print(f"[WARNING] {service_name} returned HTTP status {status}")
        return False
    except Exception as e:
        print(f"[FAILED] {service_name} HTTP API error at {url} ({e})")
        return False


def main():
    print("=" * 60)
    print("  Adaptive AI Learning Platform - Infrastructure Service Check")
    print("=" * 60)
    
    postgres_ok = check_port(settings.POSTGRES_SERVER, settings.POSTGRES_PORT, "PostgreSQL")
    redis_ok = check_port(settings.REDIS_HOST, settings.REDIS_PORT, "Redis")
    qdrant_ok = check_port(settings.QDRANT_HOST, settings.QDRANT_PORT, "Qdrant Vector DB")
    ollama_ok = check_http(f"{settings.OLLAMA_BASE_URL}/api/version", "Ollama LLM Server")
    
    print("=" * 60)
    all_ok = postgres_ok and redis_ok and qdrant_ok and ollama_ok
    if all_ok:
        print("ALL INFRASTRUCTURE SERVICES OPERATIONAL.")
    else:
        print("SOME SERVICES ARE UNREACHABLE. Start docker services using:")
        print("  docker-compose -f docker/docker-compose.yml up -d")
    print("=" * 60)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
