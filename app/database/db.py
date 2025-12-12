from sqlmodel import SQLModel, Session, create_engine, select
from pathlib import Path
import logging
from typing import Optional
import polars as pl
from app.schemas.measurement import MeasurementResponse
from app.models.measurement import Measurement
from app.models.cow import Cow, Sensor

logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path("data/IngFarm.db")


class Database:
    """Singleton Database class that maintains a persistent SQLite connection using SQLModel"""
    
    _instance: Optional['Database'] = None
    
    def __new__(cls, db_path: Path = DB_PATH):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Path = DB_PATH):
        # Only initialize once
        if self._initialized:
            return
            
        try:
            self.db_path = db_path
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create SQLModel engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                connect_args={"check_same_thread": False},
                echo=False  # Set to True for SQL query logging
            )
            self._initialized = True
            logger.info(f"Database singleton created at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise e
    
    @classmethod
    def get_instance(cls) -> 'Database':
        """Get the singleton instance of Database"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def init_database(self):
        """Initialize SQLite database and create all tables"""
        # Create all tables
        SQLModel.metadata.create_all(self.engine)
        logger.info(f"Database tables created at {self.db_path}")
        
        # Load data from parquet files
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Load initial data from parquet files into cows and sensors tables"""
        with self.get_session() as session:
            # Check if cows table is already populated
            cows_count = session.exec(select(Cow)).first()
            if cows_count is None:
                # Load cows data
                cows_file = Path("data/cows.parquet")
                if cows_file.exists():
                    cows_df = pl.read_parquet(cows_file)
                    for row in cows_df.iter_rows(named=True):
                        cow = Cow(
                            id=row['id'],
                            name=row['name'],
                            birthdate=row['birthdate']
                        )
                        session.add(cow)
                    session.commit()
                    logger.info(f"Loaded {len(cows_df)} cows from {cows_file}")
            
            # Check if sensors table is already populated
            sensors_count = session.exec(select(Sensor)).first()
            if sensors_count is None:
                # Load sensors data
                sensors_file = Path("data/sensors.parquet")
                if sensors_file.exists():
                    sensors_df = pl.read_parquet(sensors_file)
                    for row in sensors_df.iter_rows(named=True):
                        sensor = Sensor(
                            id=row['id'],
                            unit=row['unit']
                        )
                        session.add(sensor)
                    session.commit()
                    logger.info(f"Loaded {len(sensors_df)} sensors from {sensors_file}")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return Session(self.engine)
    
    def save_measurement(self, measurement: MeasurementResponse):
        """Save a single measurement to SQLite database"""
        with self.get_session() as session:
            db_measurement = Measurement(
                cow_id=measurement.cow_id,
                sensor_id=measurement.sensor_id,
                timestamp=measurement.timestamp,
                measured_at=measurement.measured_at,
                value=measurement.value,
                unit=measurement.unit,
                name=measurement.name,
                birthdate=measurement.birthdate
            )
            session.add(db_measurement)
            session.commit()
            logger.info(f"Saved measurement for cow_id {measurement.cow_id} to database")
    
    def save_measurements(self, measurements: list[MeasurementResponse]):
        """Save measurements to SQLite database"""
        with self.get_session() as session:
            for m in measurements:
                db_measurement = Measurement(
                    cow_id=m.cow_id,
                    sensor_id=m.sensor_id,
                    timestamp=m.timestamp,
                    measured_at=m.measured_at,
                    value=m.value,
                    unit=m.unit,
                    name=m.name,
                    birthdate=m.birthdate
                )
                session.add(db_measurement)
            session.commit()
            logger.info(f"Saved {len(measurements)} measurements to database")
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()
        logger.info("Database connection closed")