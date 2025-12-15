# IngFarm API

FastAPI application for managing cows and measurements with Streamlit dashboard.

## Setup

1. Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment file:

```bash
cp .env .env
```

## Running the Application

### FastAPI Backend

Development mode:

```bash
fastapi dev app/main.py
```

Production mode:

```bash
fastapi run app/main.py
```

The API will be available at `http://localhost:8000`
The dashboard will be available at `http://localhost:8501`

## API Endpoints

### Cows

- `POST /api/v1/cows/{id}` - Create a new cow
  
  ```bash
  curl -X POST "http://localhost:8000/api/v1/cows/123e4567-e89b-12d3-a456-426614174000" \
    -H "Content-Type: application/json" \
    -d '{"name": "Bessie", "birthdate": "2020-01-15"}'
  ```

- `GET /api/v1/cows/{id}` - Get cow by ID
  
  ```bash
  curl http://localhost:8000/api/v1/cows/123e4567-e89b-12d3-a456-426614174000
  ```

- `GET /api/v1/cows/` - List all cows
  
  ```bash
  curl http://localhost:8000/api/v1/cows/
  ```

### Measurements

- `GET /api/v1/measurements/{cow_id}` - Get next measurement for a cow
  
  ```bash
  curl http://localhost:8000/api/v1/measurements/123e4567-e89b-12d3-a456-426614174000
  ```

### Reports

- `GET /api/v1/reports/milk/summary/{cow_id}` - Get overall milk production summary by cow
  
  ```bash
  curl http://localhost:8000/api/v1/reports/milk/summary/123e4567-e89b-12d3-a456-426614174000
  ```

- `GET /api/v1/reports/milk/daily/{cow_id}/{report_date}` - Get daily milk production report
  
  ```bash
  curl http://localhost:8000/api/v1/reports/milk/daily/123e4567-e89b-12d3-a456-426614174000/2025-12-12
  ```

- `GET /api/v1/reports/weight/{cow_id}` - Get weight report by cow
  
  ```bash
  curl http://localhost:8000/api/v1/reports/weight/123e4567-e89b-12d3-a456-426614174000
  ```

### Health

- `GET /` - Root endpoint
- `GET /health` - Health check

## API Documentation

Once running, visit:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Testing

Run tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov=simulators
```

