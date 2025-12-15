import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from app.main import app
from app.models.measurement import Measurement

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def mock_db(mock_db_session):
    """Mock database singleton"""
    with patch('app.api.reports.get_db') as mock_get_db:
        db_instance = MagicMock()
        db_instance.get_session.return_value.__enter__.return_value = mock_db_session
        db_instance.get_session.return_value.__exit__.return_value = None
        mock_get_db.return_value = db_instance
        yield mock_get_db, mock_db_session


class TestReportsEndpoints:
    """Tests for reports endpoints"""
    
    def test_milk_summary(self, mock_db):
        """Test GET /reports/milk/summary/{cow_id} - milk production summary"""
        mock_get_db, mock_session = mock_db
        
        # Mock aggregation result
        mock_result = (
            500.0,  # total_liters
            50,     # total_measurements
            10.0,   # avg_per_measurement
            datetime(2023, 1, 1, 10, 0, 0),  # first_measurement
            datetime(2023, 12, 31, 18, 0, 0)  # last_measurement
        )
        mock_session.exec.return_value.first.return_value = mock_result
        
        response = client.get("/api/v1/reports/milk/summary/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_liters"] == 500.0
        assert data["total_measurements"] == 50
        assert data["avg_per_measurement"] == 10.0
        assert data["first_measurement"] is not None
        assert data["last_measurement"] is not None
    
    def test_milk_summary_no_data(self, mock_db):
        """Test GET /reports/milk/summary/{cow_id} - no data"""
        mock_get_db, mock_session = mock_db
        
        mock_session.exec.return_value.first.return_value = (None, None, None, None, None)
        
        response = client.get("/api/v1/reports/milk/summary/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_liters"] == 0
        assert data["total_measurements"] == 0
        assert data["avg_per_measurement"] == 0
    
    def test_daily_milk_report(self, mock_db):
        """Test GET /reports/milk/daily/{cow_id}/{date} - daily report"""
        mock_get_db, mock_session = mock_db
        
        # Mock measurements for a day
        mock_measurements = [
            Measurement(
                id=1,
                cow_id="cow-1",
                sensor_id="sensor-1",
                timestamp=1234567890.0,
                measured_at=datetime(2023, 6, 15, 10, 0, 0),
                value=12.5,
                unit="L",
                name="Bessie",
                birthdate="2020-01-01",
                recorded_at=datetime(2023, 6, 15, 10, 0, 0)
            ),
            Measurement(
                id=2,
                cow_id="cow-1",
                sensor_id="sensor-1",
                timestamp=1234567900.0,
                measured_at=datetime(2023, 6, 15, 16, 0, 0),
                value=13.0,
                unit="L",
                name="Bessie",
                birthdate="2020-01-01",
                recorded_at=datetime(2023, 6, 15, 16, 0, 0)
            )
        ]
        mock_session.exec.return_value.all.return_value = mock_measurements
        
        response = client.get("/api/v1/reports/milk/daily/cow-1/2023-06-15")
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2023-06-15"
        assert data["total_liters"] == 25.5
        assert data["measurement_count"] == 2
        assert len(data["measurements"]) == 2
    
    def test_daily_milk_report_not_found(self, mock_db):
        """Test GET /reports/milk/daily/{cow_id}/{date} - no data"""
        mock_get_db, mock_session = mock_db
        
        mock_session.exec.return_value.all.return_value = []
        
        response = client.get("/api/v1/reports/milk/daily/cow-1/2023-06-15")
        
        assert response.status_code == 404
        assert "No milk measurements found" in response.json()["detail"]
    
    def test_weight_report(self, mock_db):
        """Test GET /reports/weight/{cow_id} - weight report"""
        mock_get_db, mock_session = mock_db
        
        # Mock current weight measurement
        mock_current = Measurement(
            id=1,
            cow_id="cow-1",
            sensor_id="sensor-2",
            timestamp=1234567890.0,
            measured_at=datetime.now(),
            value=520.5,
            unit="kg",
            name="Bessie",
            birthdate="2020-01-01",
            recorded_at=datetime.now()
        )
        
        # Mock average calculation
        mock_avg_result = (515.0, 10)  # avg_weight, count
        
        # Configure mock to return different values for different queries
        mock_exec = mock_session.exec
        mock_exec.return_value.first.side_effect = [mock_current, mock_avg_result]
        
        response = client.get("/api/v1/reports/weight/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cow_id"] == "cow-1"
        assert data["cow_name"] == "Bessie"
        assert data["current_weight"] == 520.5
        assert data["avg_weight_30_days"] == 515.0
        assert data["measurements_30_days"] == 10
    
    def test_weight_report_no_data(self, mock_db):
        """Test GET /reports/weight/{cow_id} - no weight data"""
        mock_get_db, mock_session = mock_db
        
        mock_session.exec.return_value.first.return_value = None
        
        response = client.get("/api/v1/reports/weight/cow-1")
        
        assert response.status_code == 404
        assert "No weight measurements found" in response.json()["detail"]
    
    def test_weight_report_no_avg_data(self, mock_db):
        """Test GET /reports/weight/{cow_id} - current weight but no 30-day avg"""
        mock_get_db, mock_session = mock_db
        
        # Mock current weight measurement
        mock_current = Measurement(
            id=1,
            cow_id="cow-1",
            sensor_id="sensor-2",
            timestamp=1234567890.0,
            measured_at=datetime.now(),
            value=520.5,
            unit="kg",
            name="Bessie",
            birthdate="2020-01-01",
            recorded_at=datetime.now()
        )
        
        # No average data
        mock_avg_result = (None, 0)
        
        mock_exec = mock_session.exec
        mock_exec.return_value.first.side_effect = [mock_current, mock_avg_result]
        
        response = client.get("/api/v1/reports/weight/cow-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_weight"] == 520.5
        assert data["avg_weight_30_days"] is None
        assert data["measurements_30_days"] == 0
