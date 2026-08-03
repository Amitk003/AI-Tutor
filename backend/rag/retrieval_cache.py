"""
Redis Semantic Retrieval Cache.
Caches query retrieval context results with TTL to reduce vector DB search latency.
"""

import json
from typing import Any, Dict, Optional
import redis.asyncio as redis
from loguru import logger

from backend.core.config import settings


class RetrievalCache:
    """Redis-backed retrieval cache with memory fallback."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Lazy connects to Redis."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._redis.ping()
                logger.info("Connected to Redis retrieval cache at {url}", url=settings.REDIS_URL)
            except Exception as e:
                logger.warning("Redis connection unavailable ({err}). Using in-memory cache fallback.", err=str(e))
                self._redis = None
        return self._redis

    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Fetches cached retrieval result."""
        r = await self._get_redis()
        if r:
            try:
                cached_data = await r.get(cache_key)
                if cached_data:
                    logger.info("Retrieval cache HIT: key={key}", key=cache_key)
                    return json.loads(cached_data)
            except Exception as e:
                logger.error("Redis read error: {err}", err=str(e))

        # Memory fallback
        if cache_key in self._memory_cache:
            logger.info("In-memory retrieval cache HIT: key={key}", key=cache_key)
            return self._memory_cache[cache_key]

        return None

    async def set(self, cache_key: str, data: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Caches retrieval result with TTL."""
        r = await self._get_redis()
        json_data = json.dumps(data)

        if r:
            try:
                await r.setex(cache_key, ttl_seconds, json_data)
                logger.debug("Cached retrieval result in Redis: key={key} ttl={ttl}", key=cache_key, ttl=ttl_seconds)
                return
            except Exception as e:
                logger.error("Redis write error: {err}", err=str(e))

        # Memory fallback
        self._memory_cache[cache_key] = data


# Global retrieval cache singleton
retrieval_cache = RetrievalCache()
