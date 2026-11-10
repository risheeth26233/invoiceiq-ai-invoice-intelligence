import asyncio
import hmac
import os
import re
import time
from dataclasses import dataclass
from secrets import token_hex
from urllib.parse import urlsplit

from fastapi import Request
from sqlalchemy.engine import make_url
from starlette.responses import JSONResponse

COOKIE = "__Host-invoiceiq"
SESSION_SECONDS = 24 * 60 * 60
SESSION_PATH = "/api/session"
PUBLIC_PATHS = {"/api/health", "/api/sample", SESSION_PATH}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass(frozen=True)
class Demo:
    origin: str
    secret: bytes
    sample: bytes

    def issue(self):
        payload = f"{token_hex(16)}.{int(time.time()) + SESSION_SECONDS}"
        return f"{payload}.{self.signature(payload)}"

    def signature(self, payload):
        return hmac.digest(self.secret, payload.encode("ascii"), "sha256").hex()

    def owner(self, token):
        if not token or not re.fullmatch(r"[0-9a-f]{32}\.[0-9]{1,12}\.[0-9a-f]{64}", token):
            return None
        owner, expires, signature = token.split(".")
        if int(expires) <= time.time() or not hmac.compare_digest(signature, self.signature(f"{owner}.{expires}")):
            return None
        return owner


def demo_from_env(sample):
    mode = os.environ.get("INVOICEIQ_PUBLIC_DEMO", "0")
    if mode == "0" and os.environ.get("RENDER") != "true":
        return None
    if mode != "1":
        raise RuntimeError("Render requires INVOICEIQ_PUBLIC_DEMO=1.")
    origin = os.environ.get("INVOICEIQ_DEMO_ORIGIN", "")
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.port
            or origin != f"https://{parsed.hostname}"):
        raise RuntimeError("Set INVOICEIQ_DEMO_ORIGIN to the exact HTTPS frontend origin without a trailing slash.")
    secret = os.environ.get("INVOICEIQ_SESSION_SECRET", "").encode()
    if len(secret) < 32:
        raise RuntimeError("Set INVOICEIQ_SESSION_SECRET to at least 32 random bytes.")
    url = make_url(os.environ.get("DATABASE_URL", "sqlite://"))
    if url.drivername != "postgresql+psycopg" or url.query.get("sslmode") != "verify-full":
        raise RuntimeError("Public demo requires a PostgreSQL DATABASE_URL with sslmode=verify-full.")
    return Demo(origin, secret, sample)


class DemoSecurity:
    """Bound public traffic for a single ASGI worker without trusting forwarded IP headers."""

    def __init__(self, app, demo):
        self.app = app
        self.demo = demo
        self.window = -1
        self.counts = {}

    def allow(self, owner, path):
        window = int(time.monotonic()) // 60
        if window != self.window:
            self.window = window
            self.counts.clear()
        limits = {"api": 300}
        if owner:
            limits[f"owner:{owner}"] = 90
        if path == "/api/extract":
            limits["uploads"] = 40
            limits[f"upload:{owner}"] = 8
        if path == SESSION_PATH and not owner:
            limits["new_sessions"] = 60
        if any(self.counts.get(key, 0) >= maximum for key, maximum in limits.items()):
            return False
        for key in limits:
            self.counts[key] = self.counts.get(key, 0) + 1
        return True

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend([(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")])
            await send(message)

        async def reject(status, detail, headers=None):
            return await JSONResponse({"detail": detail}, status, headers=headers)(scope, receive, private_send)

        request = Request(scope)
        path = request.url.path
        if path == "/api/health":
            return await self.app(scope, receive, private_send)
        origin = request.headers.get("origin")
        if (origin is not None or request.method not in SAFE_METHODS) and origin != self.demo.origin:
            return await reject(403, "Request origin is not allowed.")
        owner = self.demo.owner(request.cookies.get(COOKIE))
        if not self.allow(owner, path):
            return await reject(429, "Demo rate limit reached. Try again in a minute.", {"Retry-After": "60"})
        if owner is None and path not in PUBLIC_PATHS:
            return await reject(401, "Start a demo session first.")
        scope.setdefault("state", {})["invoice_owner"] = owner

        limit = len(self.demo.sample) if path == "/api/extract" else 16 * 1024
        length = request.headers.get("content-length")
        if length is not None:
            if not length.isascii() or not length.isdecimal() or len(length) > 10:
                return await reject(400, "Invalid Content-Length.")
            if int(length) > limit:
                return await reject(413, "Request body is too large.")

        if request.method not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, private_send)

        # Bound the entire request, including clients that send one byte at a time.
        body = bytearray()
        try:
            async with asyncio.timeout(12):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > limit:
                        return await reject(413, "Request body is too large.")
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await reject(408, "Request body timed out.")

        buffered = bytes(body)

        async def replay():
            nonlocal buffered
            if buffered is None:
                return await receive()
            message = {"type": "http.request", "body": buffered}
            buffered = None
            return message

        return await self.app(scope, replay, private_send)
