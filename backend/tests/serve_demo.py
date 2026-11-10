"""Explicit HTTPS integration test entry point. The production image excludes this module."""

from app.main import SAMPLE, create_app
from app.security import Demo

app = create_app(Demo("https://127.0.0.1:5173", b"local-browser-test-signing-key-only", SAMPLE))
