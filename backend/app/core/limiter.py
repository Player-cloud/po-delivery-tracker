"""Per-IP rate limiting (currently just the login endpoint).

Behind Render + Cloudflare the socket peer is a proxy, so the client IP comes
from `X-Forwarded-For` (first hop). Falls back to the socket address locally.
"""

from slowapi import Limiter
from starlette.requests import Request


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)
