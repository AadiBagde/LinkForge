"""
Tests for authentication endpoints and auth service.
"""

import pytest
from fastapi.testclient import TestClient
from app.db.models import User
from sqlalchemy.orm import Session


class TestAuthRegister:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "StrongPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"
        assert "access_token" in data
        assert data["access_token_type"] == "bearer"
    
    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "StrongPass123!",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username."""
        response = client.post(
            "/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "StrongPass123!",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "StrongPass123!",
            },
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "weak",
            },
        )
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


class TestAuthLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == test_user.email
        assert "access_token" in data
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123",
            },
        )
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client: TestClient, db: Session, test_user):
        """Test login with inactive user."""
        test_user.is_active = False
        db.commit()
        
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 401
        assert "not active" in response.json()["detail"].lower()


class TestAuthGetUser:
    """Tests for getting current user endpoint."""
    
    def test_get_user_authenticated(self, client: TestClient, auth_headers):
        """Test getting current user when authenticated."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "tokentest@example.com"
        assert data["username"] == "tokentest"
    
    def test_get_user_no_token(self, client: TestClient):
        """Test getting user without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 403
    
    def test_get_user_invalid_token(self, client: TestClient):
        """Test getting user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 403
    
    def test_get_user_expired_token(self, client: TestClient):
        """Test with expired token (would need special token for this)."""
        # This test would require generating an expired token
        # Skipped in basic test suite
        pass


class TestAuthIntegration:
    """Integration tests for auth flow."""
    
    def test_register_then_login(self, client: TestClient):
        """Test registering and then logging in."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "StrongPass123!",
            },
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        token1 = register_data["access_token"]
        
        # Login with same credentials
        login_response = client.post(
            "/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "StrongPass123!",
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token2 = login_data["access_token"]
        
        # Tokens should be different but valid
        assert token1 != token2
        
        # Both tokens should work
        response1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        response2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
