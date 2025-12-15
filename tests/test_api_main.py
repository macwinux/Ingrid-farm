import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthAndRoot:
    """Tests for health check and root endpoints"""
    
    def test_root_endpoint(self):
        """Test GET / - root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Cow" in data["message"] or "API" in data["message"]
    
    def test_docs_endpoint(self):
        """Test GET /docs - OpenAPI documentation"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json(self):
        """Test GET /openapi.json - OpenAPI schema"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
