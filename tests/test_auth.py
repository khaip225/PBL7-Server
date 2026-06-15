"""Tests for authentication endpoints."""

import sys
import os

import pytest

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAuthLogin:
    """Test login endpoint validation."""

    def test_login_missing_username(self):
        """Login without username should be rejected."""
        # This is a structural test — actual HTTP testing needs a running server
        # Test that the Pydantic model validates correctly
        from backend.app.schemas.user import LoginRequest

        with pytest.raises(Exception):
            LoginRequest(password="test")

    def test_login_missing_password(self):
        """Login without password should be rejected."""
        from backend.app.schemas.user import LoginRequest

        with pytest.raises(Exception):
            LoginRequest(username="admin")

    def test_login_valid_request(self):
        """Valid login request should parse correctly."""
        from backend.app.schemas.user import LoginRequest

        req = LoginRequest(username="admin", password="admin123")
        assert req.username == "admin"
        assert req.password == "admin123"


class TestAuthToken:
    """Test JWT token creation and validation."""

    def test_token_create_and_decode(self):
        """Token should be creatable and decodable."""
        import jwt
        from datetime import datetime, timedelta, timezone

        secret = "test-secret-key"
        payload = {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert decoded["sub"] == "admin"

    def test_expired_token_rejected(self):
        """Expired token should raise error."""
        import jwt
        from datetime import datetime, timedelta, timezone

        secret = "test-secret-key"
        payload = {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, secret, algorithms=["HS256"])
