

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel
import polars as pl
from pathlib import Path
import time


class Measurement(BaseModel):
    """Pydantic model for measurement data"""
    cow_id: str
    sensor_id: str
    timestamp: float
    measured_at: datetime
    value: float
    unit: Optional[str] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None


class MeasurementReader:
    """
    Reads measurements from parquet file and returns consecutive records for a cow_id.
    Cycles back to the beginning when reaching the end of records for a specific cow.
    """
    
    def __init__(self, measurements_file: str = "data/measurements.parquet", sensor_file: str = "data/sensors.parquet", cows_file: str = "data/cows.parquet"):
        """Initialize the reader with parquet file path"""
        self.measurements_file: Path = Path(measurements_file)
        self.sensor_file: Path = Path(sensor_file)
        self.cows_file: Path = Path(cows_file)
        self.df: pl.DataFrame = pl.read_parquet(self.measurements_file)
        self.sensors_df: pl.DataFrame = pl.read_parquet(self.sensor_file)
        self.cows_df: pl.DataFrame = pl.read_parquet(self.cows_file)
        self.indices: dict[str, int] = {}  # Track current index for each cow_id
        self.cow_records: dict[str, pl.DataFrame] = {}  # Cache filtered records for each cow_id
        self.processed_records: dict[str, list[dict]] = {}  # Cache list of all processed records per cow
    
    def _initialize_cow_records(self, cow_id: str) -> None:
        """
        Initialize and cache records for a cow_id if not already cached.
        
        Args:
            cow_id: The ID of the cow
            
        Raises:
            ValueError: If no measurements found for the cow_id
        """
        if cow_id not in self.cow_records:
            cow_data = self.df.filter(pl.col('cow_id') == cow_id)
            if cow_data.height == 0:
                raise ValueError(f"No measurements found for cow_id: {cow_id}")
            self.cow_records[cow_id] = cow_data
            self.indices[cow_id] = 0
    
    def _get_current_record(self, cow_id: str) -> tuple[dict, int]:
        """
        Get the current record for a cow_id based on its index.
        
        Args:
            cow_id: The ID of the cow
            
        Returns:
            tuple: (record dict, current index)
        """
        records: pl.DataFrame = self.cow_records[cow_id]
        current_index: int = self.indices[cow_id]
        record: dict = records.row(current_index, named=True)
        return record, current_index
    
    def _enrich_with_sensor_unit(self, record: dict) -> Optional[str]:
        """
        Add sensor unit to the record by joining with sensors table.
        
        Args:
            record: The measurement record dict
            
        Returns:
            The unit value if found, None otherwise
        """
        current_unit = None
        if 'sensor_id' in record:
            sensor_unit = self.sensors_df.filter(pl.col('id') == record['sensor_id'])
            if sensor_unit.height > 0:
                current_unit = sensor_unit.row(0, named=True)['unit']
                record['unit'] = current_unit
        return current_unit
    
    def _enrich_with_cow_info(self, record: dict) -> None:
        """
        Add cow name and birthdate to the record by joining with cows table.
        
        Args:
            record: The measurement record dict
        """
        if 'cow_id' in record:
            cow_info = self.cows_df.filter(pl.col('id') == record['cow_id'])
            if cow_info.height > 0:
                cow_row = cow_info.row(0, named=True)
                record['name'] = cow_row['name']
                record['birthdate'] = cow_row['birthdate']
    
    def _replace_null_value(self, record: dict, cow_id: str, current_index: int, current_unit: Optional[str]) -> None:
        """
        Replace null value with the value from a previous record with matching unit.
        
        Args:
            record: The measurement record dict
            cow_id: The ID of the cow
            current_index: Current index in the cow's records
            current_unit: The unit of the current measurement
        """
        if record['value'] is None:
            if current_index == 0:
                # First record, default to 0
                record['value'] = 0
            else:
                # Initialize processed records list for this cow if not exists
                if cow_id not in self.processed_records:
                    self.processed_records[cow_id] = []
                
                # Iterate backwards through previously processed records to find one with the same unit
                found_value = None
                for prev_record in reversed(self.processed_records[cow_id]):
                    # Get unit for previous record
                    prev_unit: Optional[str] = prev_record.get('unit')
                    
                    # Check if units match and previous value is not null
                    if prev_unit == current_unit and prev_record.get('value') is not None:
                        found_value = prev_record['value']
                        break
                
                # Use found value or default to 0 if no matching unit found
                record['value'] = found_value if found_value is not None else 0
    
    def _store_processed_record(self, cow_id: str, record: dict) -> None:
        """
        Store the processed record for future null value replacements.
        
        Args:
            cow_id: The ID of the cow
            record: The measurement record dict
        """
        if cow_id not in self.processed_records:
            self.processed_records[cow_id] = []
        self.processed_records[cow_id].append(dict(record))
    
    def _advance_index(self, cow_id: str) -> None:
        """
        Move to the next index for the cow, cycling back to the beginning if at the end.
        
        Args:
            cow_id: The ID of the cow
        """
        records: pl.DataFrame = self.cow_records[cow_id]
        current_index: int = self.indices[cow_id]
        self.indices[cow_id] = (current_index + 1) % records.height
    
    def _update_timestamp(self, record: dict) -> None:
        """
        Update the timestamp of the record with the current timestamp.
        
        Args:
            record: The measurement record dict
        """
        current_time = time.time()
        record['timestamp'] = current_time
        # Adding a readable measured_at field
        record['measured_at'] = datetime.fromtimestamp(current_time)
        
    def get_next_measurement(self, cow_id: str) -> Measurement:
        """
        Get the next consecutive measurement for the specified cow_id.
        Cycles back to the beginning when reaching the end.
        
        Args:
            cow_id: The ID of the cow
            
        Returns:
            Measurement: A Pydantic model containing the measurement data
        """
        # Initialize cow records if first time
        self._initialize_cow_records(cow_id)
        
        # Get current record and index
        record, current_index = self._get_current_record(cow_id)
        
        # Enrich record with sensor unit
        current_unit = self._enrich_with_sensor_unit(record)
        
        # Enrich record with cow information
        self._enrich_with_cow_info(record)
        
        # Replace null values if needed
        self._replace_null_value(record, cow_id, current_index, current_unit)
        
        # Update timestamp with current time
        self._update_timestamp(record)
        
        # Store processed record
        self._store_processed_record(cow_id, record)
        
        # Advance to next index
        self._advance_index(cow_id)

        # Return as Pydantic model
        return Measurement(**record)
    
    def get_all_cow_ids(self) -> list:
        """Get list of all unique cow IDs in the measurements"""
        return self.df['cow_id'].unique().to_list()
    
    def reset_index(self, cow_id: str):
        """
        Reset the index for a specific cow or all cows
        
        Args:
            cow_id: The cow ID to reset. If None, reset all.
        """
        if cow_id is None:
            self.indices = {}
        elif cow_id in self.indices:
            self.indices[cow_id] = 0


# Example usage functions
def example_usage():
    """Example of how to use the MeasurementReader"""
    reader = MeasurementReader()
    
    # Get all available cow IDs
    cow_ids = reader.get_all_cow_ids()
    print(f"Available cow IDs: {cow_ids[:1]}...")  # Show first 5
    
    # Get measurements for a specific cow
    if cow_ids:
        cow_id = cow_ids[0]
        print(f"\nGetting measurements for cow: {cow_id}")
        
        # Get 5 consecutive measurements (will cycle if needed)
        for i in range(10):
            measurement = reader.get_next_measurement(cow_id)
            print(f"  Measurement {i+1}: {measurement}")

if __name__ == "__main__":
    example_usage()
