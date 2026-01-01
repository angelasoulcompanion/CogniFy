"""
CogniFy Security Tests
Created with love by Angela & David - 1 January 2026
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_tokens,
    decode_token,
)


class TestPasswordHashing:
    """Test password hashing functions"""

    @pytest.mark.unit
    def test_hash_password(self):
        """Test password hashing"""
        password = "test123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """Test correct password verification"""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """Test incorrect password verification"""
        password = "test123"
        wrong_password = "wrong123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    @pytest.mark.unit
    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes"""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token functions"""

    @pytest.mark.unit
    def test_create_access_token(self):
        """Test access token creation"""
        user_id = uuid4()
        token = create_access_token(user_id, "user")

        assert token is not None
        assert len(token) > 50

    @pytest.mark.unit
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = uuid4()
        token = create_refresh_token(user_id)

        assert token is not None
        assert len(token) > 50

    @pytest.mark.unit
    def test_create_tokens(self):
        """Test creating both tokens"""
        user_id = uuid4()
        tokens = create_tokens(user_id, "admin")

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    @pytest.mark.unit
    def test_decode_access_token(self):
        """Test decoding access token"""
        user_id = uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == str(user_id)
        assert payload.type == "access"
        assert payload.role == "user"

    @pytest.mark.unit
    def test_decode_refresh_token(self):
        """Test decoding refresh token"""
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == str(user_id)
        assert payload.type == "refresh"

    @pytest.mark.unit
    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None"""
        payload = decode_token("invalid.token.here")
        assert payload is None

    @pytest.mark.unit
    def test_decode_expired_token(self):
        """Test decoding expired token"""
        user_id = uuid4()
        # Create token with negative expiry
        token = create_access_token(user_id, "user", expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)

        assert payload is None
