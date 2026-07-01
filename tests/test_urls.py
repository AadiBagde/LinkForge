"""
Tests for URL shortening and CRUD endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.db.models import URL, Click
from sqlalchemy.orm import Session


class TestURLShortening:
    """Tests for URL shortening endpoint."""
    
    def test_shorten_url_success(self, client: TestClient):
        """Test successful URL shortening."""
        response = client.post(
            "/shorten",
            json={
                "original_url": "https://github.com/AadiBagde/LinkForge",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "short_url" in data
        assert "localhost:8000" in data["short_url"]
    
    def test_shorten_url_with_custom_code(self, client: TestClient):
        """Test URL shortening with custom code."""
        response = client.post(
            "/shorten",
            json={
                "original_url": "https://github.com",
                "custom_code": "mygithub",
            },
        )
        assert response.status_code == 200
        assert "mygithub" in response.json()["short_url"]
    
    def test_shorten_invalid_url(self, client: TestClient):
        """Test shortening invalid URL."""
        response = client.post(
            "/shorten",
            json={
                "original_url": "not-a-url",
            },
        )
        assert response.status_code == 400
        assert "URL" in response.json()["detail"]
    
    def test_shorten_duplicate_custom_code(self, client: TestClient, test_url: URL):
        """Test shortening with duplicate custom code."""
        response = client.post(
            "/shorten",
            json={
                "original_url": "https://example.com",
                "custom_code": test_url.short_code,  # Already in use
            },
        )
        assert response.status_code == 409
        assert "already in use" in response.json()["detail"].lower()


class TestURLRedirect:
    """Tests for URL redirect endpoint."""
    
    def test_redirect_success(self, client: TestClient, test_url: URL, db: Session):
        """Test successful redirect."""
        response = client.get(f"/{test_url.short_code}", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == test_url.original_url
        
        # Click should be logged
        clicks = db.query(Click).filter(Click.url_id == test_url.id).all()
        assert len(clicks) > 0
    
    def test_redirect_nonexistent(self, client: TestClient):
        """Test redirect for non-existent URL."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_redirect_expired_url(self, client: TestClient, db: Session, test_url: URL):
        """Test redirect for expired URL."""
        from datetime import datetime, timedelta
        
        # Expire the URL
        test_url.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        
        response = client.get(f"/{test_url.short_code}")
        assert response.status_code == 410  # Gone


class TestURLAnalytics:
    """Tests for URL analytics endpoints."""
    
    def test_get_analytics(self, client: TestClient, test_url: URL, db: Session):
        """Test getting URL analytics."""
        response = client.get(f"/analytics/{test_url.short_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == test_url.short_code
        assert "click_count" in data or "clicks" in data
    
    def test_analytics_nonexistent(self, client: TestClient):
        """Test analytics for non-existent URL."""
        response = client.get("/analytics/nonexistent")
        assert response.status_code == 404
    
    def test_get_top_urls(self, client: TestClient, db: Session, test_url: URL):
        """Test getting top URLs."""
        response = client.get("/analytics/top")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestURLManagement:
    """Tests for URL management endpoints (CRUD)."""
    
    def test_get_user_urls(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """Test getting user's URLs."""
        # Create a URL for the user
        url = URL(
            original_url="https://example.com",
            short_code="example123",
            user_id=test_user.id,
        )
        db.add(url)
        db.commit()
        
        response = client.get("/urls/my-urls", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_urls" in data
        assert data["total_urls"] >= 1
        assert len(data["urls"]) > 0
    
    def test_search_urls(self, client: TestClient, auth_headers: dict):
        """Test searching user's URLs."""
        response = client.get(
            "/urls/search",
            params={"q": "example"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "results" in data
    
    def test_update_url(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """Test updating a URL."""
        # Create URL
        url = URL(
            original_url="https://old.example.com",
            short_code="oldcode",
            user_id=test_user.id,
        )
        db.add(url)
        db.commit()
        
        # Update it
        response = client.put(
            f"/urls/{url.short_code}",
            json={
                "original_url": "https://new.example.com",
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["original_url"] == "https://new.example.com"
    
    def test_delete_url(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """Test deleting a URL."""
        # Create URL
        url = URL(
            original_url="https://todelete.example.com",
            short_code="todelete",
            user_id=test_user.id,
        )
        db.add(url)
        db.commit()
        url_id = url.id
        
        # Delete it
        response = client.delete(
            f"/urls/{url.short_code}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it's deleted
        deleted_url = db.query(URL).filter(URL.id == url_id).first()
        assert deleted_url is None
    
    def test_bulk_create_urls(self, client: TestClient, auth_headers: dict):
        """Test bulk creating URLs."""
        response = client.post(
            "/urls/bulk-create",
            json={
                "urls": [
                    "https://example1.com",
                    "https://example2.com",
                    "https://example3.com",
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 3
        assert data["failed"] == 0
        assert len(data["urls"]) == 3


class TestQRCode:
    """Tests for QR code generation endpoint."""
    
    def test_generate_qr_code(self, client: TestClient, test_url: URL):
        """Test QR code generation."""
        response = client.get(f"/qr/{test_url.short_code}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0
    
    def test_qr_code_nonexistent(self, client: TestClient):
        """Test QR code for non-existent URL."""
        response = client.get("/qr/nonexistent")
        assert response.status_code == 404


class TestURLProtection:
    """Tests for URL access control and protection."""
    
    def test_update_others_url(self, client: TestClient, db: Session, test_user):
        """Test that users can't update other users' URLs."""
        # Create URL for test_user
        url = URL(
            original_url="https://example.com",
            short_code="example",
            user_id=test_user.id,
        )
        db.add(url)
        db.commit()
        
        # Try to update as different user
        other_token_response = client.post(
            "/auth/register",
            json={
                "email": "otheruser@example.com",
                "username": "otheruser",
                "password": "Password123!",
            },
        )
        other_token = other_token_response.json()["access_token"]
        
        response = client.put(
            f"/urls/{url.short_code}",
            json={"original_url": "https://hacked.com"},
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert response.status_code == 404
    
    def test_delete_others_url(self, client: TestClient, db: Session, test_user):
        """Test that users can't delete other users' URLs."""
        # Create URL for test_user
        url = URL(
            original_url="https://example.com",
            short_code="example2",
            user_id=test_user.id,
        )
        db.add(url)
        db.commit()
        
        # Try to delete as different user
        other_token_response = client.post(
            "/auth/register",
            json={
                "email": "otheruser2@example.com",
                "username": "otheruser2",
                "password": "Password123!",
            },
        )
        other_token = other_token_response.json()["access_token"]
        
        response = client.delete(
            f"/urls/{url.short_code}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert response.status_code == 404
        
        # Verify URL still exists
        existing = db.query(URL).filter(URL.short_code == "example2").first()
        assert existing is not None
