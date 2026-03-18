from collections import deque
from threading import Lock
from time import monotonic
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        if limit <= 0 or window_seconds <= 0:
            return

        now = monotonic()
        floor = now - window_seconds
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= floor:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                )
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def build_rate_limit_dependency(
    bucket_name: str,
    limit: int,
    window_seconds: int,
    *,
    key_scope: str = "ip",
    account_dependency: Any | None = None,
) -> Callable[..., None]:
    def dependency(
        request: Request,
        current_account: Any | None = None,
    ) -> None:
        if key_scope == "account" and current_account is not None:
            identity = f"account:{getattr(current_account, 'account_id', 'unknown')}"
        else:
            client_host = request.client.host if request.client else "unknown"
            identity = f"ip:{client_host}"

        rate_limiter.check(
            key=f"{bucket_name}:{identity}",
            limit=limit,
            window_seconds=window_seconds,
        )

    if key_scope == "account":
        if account_dependency is None:
            raise ValueError("account_dependency is required for account-scoped rate limiting")

        def account_dependency(
            request: Request,
            current_account: Any = Depends(account_dependency),
        ) -> None:
            dependency(request=request, current_account=current_account)

        return account_dependency

    return dependency
