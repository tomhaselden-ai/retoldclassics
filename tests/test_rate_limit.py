import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from backend.api.rate_limit import InMemoryRateLimiter, build_rate_limit_dependency


class RateLimitTests(unittest.TestCase):
    def test_limiter_blocks_after_threshold(self) -> None:
        limiter = InMemoryRateLimiter()
        limiter.check("bucket:test", limit=2, window_seconds=60)
        limiter.check("bucket:test", limit=2, window_seconds=60)
        with self.assertRaises(HTTPException) as exc:
            limiter.check("bucket:test", limit=2, window_seconds=60)
        self.assertEqual(exc.exception.status_code, 429)

    def test_ip_scoped_dependency_uses_request_client_host(self) -> None:
        dependency = build_rate_limit_dependency("login", 1, 60)
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        dependency(request=request)
        with self.assertRaises(HTTPException):
            dependency(request=request)

    def test_account_scoped_dependency_uses_account_id(self) -> None:
        dependency = build_rate_limit_dependency(
            "generate",
            1,
            60,
            key_scope="account",
            account_dependency=lambda: None,
        )
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        current_account = SimpleNamespace(account_id=99)
        dependency(request=request, current_account=current_account)
        with self.assertRaises(HTTPException):
            dependency(request=request, current_account=current_account)


if __name__ == "__main__":
    unittest.main()
