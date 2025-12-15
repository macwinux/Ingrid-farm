import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.schemas.cow import CowResponse

client = TestClient(app)


@pytest.fixture
def mock_cow_service():
    """Mock CowService"""
    with patch('app.api.cows.cow_service') as mock_service:
        yield mock_service


class TestCowsEndpoints:
    """Tests for cow endpoints"""
    
    def test_list_cows(self, mock_cow_service):
        """Test GET /cows/ - list all cows"""
        # Mock cow data
        mock_cows = [
            CowResponse(id="cow-1", name="Bessie", birthdate="2020-01-01"),
            CowResponse(id="cow-2", name="Daisy", birthdate="2019-06-15")
        ]
        # Use AsyncMock for async methods
        mock_cow_service.list_cows = AsyncMock(return_value=mock_cows)
        
        response = client.get("/api/v1/cows/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "cow-1"
        assert data[0]["name"] == "Bessie"
    
    def test_get_cow_by_id(self, mock_cow_service):
        """Test GET /cows/{cow_id} - get specific cow"""
        mock_cow = CowResponse(id="cow-1", name="Bessie", birthdate="2020-01-01")
        mock_cow_service.get_cow = AsyncMock(return_value=mock_cow)
        
        response = client.get("/api/v1/cows/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "cow-1"
        assert data["name"] == "Bessie"
    
    def test_get_cow_not_found(self, mock_cow_service):
        """Test GET /cows/{cow_id} - cow not found"""
        mock_cow_service.get_cow = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/cows/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_cow(self, mock_cow_service):
        """Test POST /cows/{cow_id} - create new cow"""
        new_cow_data = {
            "name": "Bessie",
            "birthdate": "2020-01-01"
        }
        
        mock_response = CowResponse(id="cow-1", name="Bessie", birthdate="2020-01-01")
        mock_cow_service.create_cow = AsyncMock(return_value=mock_response)
        
        response = client.post("/api/v1/cows/cow-1", json=new_cow_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Bessie"
        assert data["birthdate"] == "2020-01-01"
