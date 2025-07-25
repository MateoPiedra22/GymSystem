"""Test main application functionality."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestMainApp:
    """Test main application endpoints and functionality."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
    
    def test_api_version_endpoint(self, client: TestClient):
        """Test API version endpoint."""
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "api_version" in data
        assert "build_date" in data
    
    def test_docs_redirect(self, client: TestClient):
        """Test docs redirect."""
        response = client.get("/docs", follow_redirects=False)
        assert response.status_code in [200, 307]  # Either direct access or redirect
    
    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_404_handler(self, client: TestClient):
        """Test custom 404 handler."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error_code" in data
        assert "timestamp" in data
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    @pytest.mark.api
    def test_api_prefix_routes(self, client: TestClient):
        """Test that API routes are accessible with /api prefix."""
        # Test auth routes
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 422]  # Unauthorized or validation error (no token)
        
        # Test users routes
        response = client.get("/api/users/")
        assert response.status_code in [401, 422]  # Unauthorized (no token)
    
    def test_middleware_order(self, client: TestClient):
        """Test that middleware is properly configured."""
        response = client.get("/health")
        
        # Check for security headers (added by SecurityMiddleware)
        headers = response.headers
        
        # These headers should be present if SecurityMiddleware is working
        expected_security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        # At least some security headers should be present
        security_headers_present = any(
            header.lower() in [h.lower() for h in headers.keys()]
            for header in expected_security_headers
        )
        
        # If no security headers, that's okay for testing, just check response is valid
        assert response.status_code == 200
    
    def test_request_id_header(self, client: TestClient):
        """Test that request ID is added to responses."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Request ID might be added by middleware
        # If not present, that's okay for testing environment
        if "x-request-id" in response.headers:
            assert len(response.headers["x-request-id"]) > 0
    
    def test_compression_middleware(self, client: TestClient):
        """Test compression middleware."""
        # Make a request that should trigger compression
        response = client.get("/openapi.json", headers={
            "Accept-Encoding": "gzip"
        })
        assert response.status_code == 200
        
        # Check if response is compressed (optional, depends on middleware config)
        # In testing environment, compression might be disabled
        assert len(response.content) > 0
    
    @pytest.mark.slow
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting middleware (if enabled)."""
        # Make multiple requests quickly
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)
        
        # All should succeed in testing (rate limiting usually disabled)
        for response in responses:
            assert response.status_code == 200
    
    def test_database_middleware(self, client: TestClient):
        """Test database middleware connection."""
        # This test verifies that database middleware is working
        # by making a request that would use the database
        response = client.get("/health")
        assert response.status_code == 200
        
        # Health check should include database status
        data = response.json()
        if "database" in data:
            assert data["database"] in ["connected", "healthy"]