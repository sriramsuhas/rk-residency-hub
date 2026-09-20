"""
Tests the real rate limiter behavior. Uses its own TestClient rather than
the shared `client` fixture, since that fixture overrides the rate limiter
to a no-op to keep the rest of the suite from tripping the shared singleton.
"""
from fastapi.testclient import TestClient

from database.session import get_db
from main import app
from middleware.rate_limiter import RateLimiter, auth_rate_limiter


def test_rate_limiter_blocks_after_threshold(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Don't override the rate limiter here — we want the real thing. But
    # swap in a fresh, low-threshold instance so this test doesn't depend
    # on (or pollute) the shared module-level limiter used elsewhere.
    test_limiter = RateLimiter(max_requests=3, window_seconds=60)
    app.dependency_overrides[auth_rate_limiter] = test_limiter

    try:
        with TestClient(app) as client:
            statuses = []
            for i in range(5):
                r = client.post(
                    "/api/v1/auth/register",
                    json={"full_name": "Spammer", "email": f"spam{i}@example.com", "password": "SecurePass1"},
                )
                statuses.append(r.status_code)

            # First 3 succeed (201), the rest are rate-limited (429)
            assert statuses[:3] == [201, 201, 201]
            assert statuses[3] == 429
            assert statuses[4] == 429
    finally:
        app.dependency_overrides.clear()
