"""Tests for mock telemetry reader"""

import pytest
import time
from src.telemetry.telemetry_mock import MockTelemetryReader


class TestMockTelemetryReader:
    """Test suite for MockTelemetryReader"""

    def test_is_available(self):
        """Mock telemetry should always be available"""
        reader = MockTelemetryReader()
        assert reader.is_available() is True

    def test_get_session_info(self):
        """Should return valid session information"""
        reader = MockTelemetryReader()
        session_info = reader.get_session_info()

        assert 'player_name' in session_info
        assert 'track_name' in session_info
        assert 'car_name' in session_info
        assert session_info['track_name'] == "Bahrain International Circuit"

    def test_read_returns_valid_data(self):
        """Should return dictionary with all required fields"""
        reader = MockTelemetryReader()
        data = reader.read()

        # Check essential fields exist
        assert 'lap' in data
        assert 'speed' in data
        assert 'lap_distance' in data
        assert 'total_distance' in data

        # Check data types
        assert isinstance(data['lap'], int)
        assert isinstance(data['speed'], (int, float))
        assert isinstance(data['lap_distance'], (int, float))

    def test_lap_progression(self):
        """Lap distance should increase over time"""
        reader = MockTelemetryReader()

        # Read initial state
        data1 = reader.read()
        initial_distance = data1['lap_distance']

        # Wait a bit
        time.sleep(0.1)

        # Read again
        data2 = reader.read()
        new_distance = data2['lap_distance']

        # Distance should have increased
        assert new_distance > initial_distance

    def test_lap_increment(self):
        """Lap number should increment when lap completes"""
        # Set a very short track for faster testing
        reader = MockTelemetryReader()
        reader.track_length = 100  # Very short track (100m)

        initial_lap = reader.read()['lap']

        # Wait for lap to complete (~1.5 seconds at 70 m/s)
        time.sleep(2)

        new_lap = reader.read()['lap']

        # Lap should have incremented
        assert new_lap > initial_lap

    def test_required_fields_present(self):
        """All required telemetry fields should be present"""
        reader = MockTelemetryReader()
        data = reader.read()

        required_fields = [
            'player_name', 'track_name', 'car_name', 'session_type',
            'lap', 'lap_distance', 'speed', 'rpm', 'gear',
            'position_x', 'position_y', 'position_z',
            'wheel_speed', 'tyre_temp', 'tyre_pressure',
            'engine_temp', 'fuel_remaining', 'sector_index'
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_wheel_data_structure(self):
        """Wheel data should be dictionaries with rl, rr, fl, fr keys"""
        reader = MockTelemetryReader()
        data = reader.read()

        wheel_fields = ['wheel_speed', 'tyre_temp', 'tyre_pressure', 'tyre_wear']

        for field in wheel_fields:
            assert isinstance(data[field], dict)
            assert 'rl' in data[field]
            assert 'rr' in data[field]
            assert 'fl' in data[field]
            assert 'fr' in data[field]
