from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    PROJECT_NAME: str = "IngFarm API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Data paths
    COWS_DATA_PATH: str = "data/cows.parquet"
    MEASUREMENTS_DATA_PATH: str = "data/measurements.parquet"
    SENSORS_DATA_PATH: str = "data/sensors.parquet"
    
    class Config:
        case_sensitive = True

settings = Settings()
