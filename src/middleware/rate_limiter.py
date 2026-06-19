import time
import threading
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.schemas import ErrorDetail, ErrorResponse

class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.fill_rate = float(fill_rate)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# Global limiters
global_limiter = TokenBucket(capacity=settings.rate_limit_global_rps, fill_rate=settings.rate_limit_global_rps)
log_limiter = TokenBucket(capacity=settings.rate_limit_log_rps, fill_rate=settings.rate_limit_log_rps)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check specific routes
        if request.url.path == "/api/v1/access/logs/recent":
            if not log_limiter.consume(1):
                return self._rate_limit_response("B6 rate limit exceeded (50 RPS)")
                
        # Check global limit
        if not global_limiter.consume(1):
            return self._rate_limit_response("Global rate limit exceeded (200 RPS)")

        response = await call_next(request)
        return response

    def _rate_limit_response(self, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="TOO_MANY_REQUESTS",
                    message=message
                )
            ).model_dump()
        )
