import pytest
import polars as pl
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))
from simulators.read_measurements import MeasurementReader

@pytest.fixture
def sample_parquet_files():
    """Create temporary measurement and sensor parquet files for testing joins"""
    # Create measurements data
    measurements_data = {
        'cow_id': ['cow-1', 'cow-2', 'cow-1', 'cow-2', 'cow-1'],
        'sensor_id': ['sensor-1', 'sensor-2', 'sensor-1', 'sensor-2', 'sensor-3'],
        'timestamp': [1704067200.0, 1704070800.0, 1704074400.0, 1704078000.0, 1704081600.0],
        'value': [10.5, None, None, 15.2, 600.8]
    }
    measurements_df = pl.DataFrame(measurements_data)
    
    # Create sensors data
    sensors_data = {
        'id': ['sensor-1', 'sensor-2', 'sensor-3'],
        'unit': ['L', 'L', 'Kg']
    }
    sensors_df = pl.DataFrame(sensors_data)
    
    # Create cows data
    cows_data = {
        'id': ['cow-1', 'cow-2'],
        'name': ['Bessie', 'Daisy'],
        'birthdate': ['2020-01-15', '2021-03-20']
    }
    cows_df = pl.DataFrame(cows_data)
    
    # Create temporary files
    measurements_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='_measurements.parquet')
    measurements_df.write_parquet(measurements_file.name)
    measurements_file.close()
    
    sensors_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='_sensors.parquet')
    sensors_df.write_parquet(sensors_file.name)
    sensors_file.close()
    
    cows_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='_cows.parquet')
    cows_df.write_parquet(cows_file.name)
    cows_file.close()
    
    yield measurements_file.name, sensors_file.name, cows_file.name
    
    # Cleanup
    os.unlink(measurements_file.name)
    os.unlink(sensors_file.name)
    os.unlink(cows_file.name)


def test_initialization(sample_parquet_files):
    """Test that the reader initializes correctly"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    assert reader.df.height == 5
    assert reader.indices == {}
    assert reader.cow_records == {}


def test_consecutive_measurements(sample_parquet_files):
    """Test that consecutive calls return consecutive measurements"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get three consecutive measurements for cow-1
    m1 = reader.get_next_measurement('cow-1')
    m2 = reader.get_next_measurement('cow-1')
    m3 = reader.get_next_measurement('cow-1')
    
    assert m1.name == 'Bessie'
    assert m1.value == 10.5
    assert m1.unit == 'L'
    assert m2.value == 10.5
    assert m2.unit == 'L'
    assert m3.value == 600.8
    assert m3.unit == 'Kg'
    
    # Index should now be at 0 (cycled back)
    assert reader.indices['cow-1'] == 0


def test_cycling_at_end_of_records(sample_parquet_files):
    """Test that the reader cycles back to the beginning when reaching the end"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # cow-1 has 3 measurements, get 4 to test cycling
    m1 = reader.get_next_measurement('cow-1')
    _ = reader.get_next_measurement('cow-1')
    _ = reader.get_next_measurement('cow-1')
    
    # At this point, we've read all 3 records and index should have cycled to 0
    assert reader.indices['cow-1'] == 0
    
    # Get the 4th measurement - should cycle back to first
    m4 = reader.get_next_measurement('cow-1')
    
    # Fourth measurement should be same as first
    assert m1.value == m4.value
    assert m1.cow_id == m4.cow_id
    # But different timestamp
    assert m1.timestamp != m4.timestamp
    
    # Index should be at 1 after cycling
    assert reader.indices['cow-1'] == 1


def test_multiple_cows_independent_indices(sample_parquet_files):
    """Test that different cows maintain independent indices"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get measurements for two different cows
    cow1_m1 = reader.get_next_measurement('cow-1')
    cow2_m1 = reader.get_next_measurement('cow-2')
    cow1_m2 = reader.get_next_measurement('cow-1')
    
    # Indices should be independent
    assert reader.indices['cow-1'] == 2
    assert reader.indices['cow-2'] == 1
    
    # Values should be correct
    assert cow1_m1.value == 10.5
    assert cow2_m1.value == 0
    assert cow1_m2.value == 10.5



def test_invalid_cow_id(sample_parquet_files):
    """Test that requesting invalid cow_id raises error"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    with pytest.raises(ValueError, match="No measurements found for cow_id"):
        reader.get_next_measurement('invalid-cow')


def test_many_cycles(sample_parquet_files):
    """Test that cycling works correctly over many iterations"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get 100 measurements and verify pattern repeats
    values = []
    for _ in range(100):
        m = reader.get_next_measurement('cow-1')
        values.append(m.value)
    
    # Every 3 values should repeat the pattern [10.5, 10.5, 600.8]
    expected_pattern = [10.5, 10.5, 600.8]
    for i in range(100):
        assert values[i] == expected_pattern[i % 3]
    
    # After 99 cycles (99 % 3 = 0), index should be at 1 (100th call moved it)
    assert reader.indices['cow-1'] == 1


# Tests with nulls

def test_null_value_replaced_with_index(sample_parquet_files):
    """Test that null values are replaced with the current index"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get measurements for cow-1
    m1 = reader.get_next_measurement('cow-1')  # index 0, value 10.5
    m2 = reader.get_next_measurement('cow-1')  # index 1, value is null -> should be 10.5
    m3 = reader.get_next_measurement('cow-1')  # index 2, value 25.8
    
    # First has original value
    assert m1.value == 10.5
    
    # Second had null, should be replaced with index 1
    print("m1:", m1)
    print("m2:", m2)
    assert m2.value == 10.5
    
    # Third has original value
    assert m3.value == 600.8


def test_null_value_initial_null(sample_parquet_files):
    """Test null value replacement for cow-2"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get measurements for cow-2
    m1 = reader.get_next_measurement('cow-2')  # index 0, value is null -> should be 0
    m2 = reader.get_next_measurement('cow-2')  # index 1, value 15.2
    
    assert m1.value == 0
    
    # Second has original value
    assert m2.value == 15.2


# Tests for sensor unit join
def test_sensor_unit_join(sample_parquet_files):
    """Test that sensor unit is added to measurement records"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get measurements for cow-1
    m1 = reader.get_next_measurement('cow-1')
    _ = reader.get_next_measurement('cow-1')
    m3 = reader.get_next_measurement('cow-1')
    
    # First measurement uses sensor-1
    assert m1.sensor_id == 'sensor-1'
    assert m1.unit == 'L'
    assert m1.value == 10.5
    
    # Third measurement uses sensor-3
    assert m3.sensor_id == 'sensor-3'
    assert m3.unit == 'Kg'
    assert m3.value == 600.8


def test_sensor_unit_after_cycling(sample_parquet_files):
    """Test that sensor unit join works correctly after cycling"""
    measurements_file, sensors_file, cows_file = sample_parquet_files
    reader = MeasurementReader(measurements_file, sensors_file, cows_file)
    
    # Get 4 measurements (will cycle after 3)
    m1 = reader.get_next_measurement('cow-1')
    _ = reader.get_next_measurement('cow-1')
    _ = reader.get_next_measurement('cow-1')
    m4 = reader.get_next_measurement('cow-1')  # Cycles back to first
    
    # Fourth should have same sensor and unit as first
    assert m4.sensor_id == m1.sensor_id
    assert m4.unit == m1.unit

