"""
A minimal in-memory rate limiter for the auth endpoints most worth
protecting against brute-forcing (login, register, forgot-password).

This is intentionally simple: an in-process fixed-window counter keyed by
client IP. It resets on restart and doesn't share state across multiple
instances — that's a real limitation, but Redis is explicitly out of scope
for this project, and a single-instance limiter still meaningfully raises
the cost of a brute-force attempt, which is the actual goal here.
"""
import time
from collections import defaultdict, deque

from fastapi import Request

from utils.exceptions import AppException


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            raise AppException(
                "Too many attempts. Please wait a moment before trying again.", status_code=429
            )

        hits.append(now)


# 10 attempts per minute per IP is generous enough for normal use (including
# a person mistyping their password a few times) while still meaningfully
# slowing down automated credential-stuffing against these endpoints.
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
