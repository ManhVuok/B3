from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Hardcode key đơn giản cho demo đồ án
API_KEY = "DVKN2026-SECRET-KEY"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Chỉ kiểm tra bảo mật cho các API, bỏ qua /health và /docs
        if request.url.path.startswith("/api/v1"):
            api_key = request.headers.get("X-API-Key")
            if api_key != API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Missing or invalid API Key in X-API-Key header"
                        }
                    }
                )
        response = await call_next(request)
        return response
