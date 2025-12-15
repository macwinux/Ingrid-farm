import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from app.main import app
from app.schemas.measurement import MeasurementResponse

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database"""
    with patch('app.api.measurements.db') as mock_database:
        mock_database.save_measurements = Mock()
        yield mock_database


@pytest.fixture
def mock_measurement_service():
    """Mock MeasurementService"""
    with patch('app.api.measurements.measurement_service') as mock_service:
        yield mock_service


class TestMeasurementsEndpoints:
    """Tests for measurement endpoints"""
    
    def test_get_next_measurement(self, mock_db, mock_measurement_service):
        """Test GET /measurements/{cow_id} - get next measurement"""
        # Mock measurement data
        mock_measurement = MeasurementResponse(
            cow_id="cow-1",
            sensor_id="sensor-1",
            timestamp=1234567890.0,
            measured_at=datetime(2023, 1, 1, 10, 0, 0),
            value=25.5,
            unit="L",
            name="Bessie",
            birthdate="2020-01-01"
        )
        mock_measurement_service.get_next_measurement = AsyncMock(return_value=mock_measurement)
        
        response = client.get("/api/v1/measurements/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cow_id"] == "cow-1"
        assert data["value"] == 25.5
        assert data["unit"] == "L"
        # Verify db.save_measurements was called
        mock_db.save_measurements.assert_called_once()
    
    def test_get_next_measurement_not_found(self, mock_measurement_service):
        """Test GET /measurements/{cow_id} - cow not found"""
        mock_measurement_service.get_next_measurement = AsyncMock(side_effect=ValueError("Cow not found"))
        
        response = client.get("/api/v1/measurements/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

