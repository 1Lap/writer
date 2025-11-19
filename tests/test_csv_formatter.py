"""Tests for the MVP CSV formatter."""

from collections import OrderedDict

import pytest

from src.csv_formatter import CSVFormatter
from src.mvp_format import MVP_TELEMETRY_HEADER


@pytest.fixture
def formatter():
    return CSVFormatter()


@pytest.fixture
def metadata():
    return OrderedDict(
        [
            ("Format", "LMUTelemetry v2"),
            ("Version", "1"),
            ("Player", "Test Driver"),
            ("TrackName", "Test Track"),
            ("CarName", "Test Car"),
            ("SessionUTC", "2025-01-01T00:00:00Z"),
            ("LapTime [s]", "95.123"),
            ("TrackLen [m]", "5000.00"),
            ("Event", "Practice"),
        ]
    )


@pytest.fixture
def sample_row():
    return {
        "LapDistance [m]": 12.34567,
        "LapTime [s]": 0.45678,
        "Sector [int]": 1,
        "Speed [km/h]": 210.9876,
        "EngineRevs [rpm]": 7400.321,
        "ThrottlePercentage [%]": 99.95,
        "BrakePercentage [%]": 0.25,
        "Steer [%]": -4.5,
        "Gear [int]": 4,
        "X [m]": -10.1234,
        "Y [m]": 7.30001,
        "Z [m]": None,
    }


class TestCSVFormatter:
    def test_returns_non_empty_string(self, formatter, metadata, sample_row):
        result = formatter.format_lap([sample_row], metadata)
        assert isinstance(result, str)
        assert result.strip() != ""

    def test_returns_empty_string_for_no_samples(self, formatter, metadata):
        assert formatter.format_lap([], metadata) == ""

    def test_metadata_order_preserved(self, formatter, metadata, sample_row):
        result = formatter.format_lap([sample_row], metadata)
        lines = result.strip().split("\n")
        assert lines[0] == "Format,LMUTelemetry v2"
        assert lines[1] == "Version,1"
        assert lines[2] == "Player,Test Driver"
        assert "Event,Practice" in lines

    def test_header_matches_constant(self, formatter, metadata, sample_row):
        result = formatter.format_lap([sample_row], metadata)
        lines = result.strip().split("\n")
        header_line = lines[len(metadata) + 1]
        assert header_line == ",".join(MVP_TELEMETRY_HEADER)

    def test_sample_row_formatting(self, formatter, metadata, sample_row):
        result = formatter.format_lap([sample_row], metadata)
        sample_line = result.strip().split("\n")[-1]
        cells = sample_line.split(',')

        assert cells[0] == "12.346"  # LapDistance rounded to 3 decimals
        assert cells[1] == "0.457"   # LapTime rounded to 3 decimals
        assert cells[2] == "1"       # Sector int
        assert cells[5] == "99.95"   # Throttle preserves two decimals
        assert cells[10] == "7.30"   # Coordinate min decimals
        assert cells[11] == ""       # Missing Z becomes blank

    def test_samples_sorted_by_distance(self, formatter, metadata, sample_row):
        reordered = sample_row.copy()
        reordered["LapDistance [m]"] = 1.0
        reordered["LapTime [s]"] = 0.050

        result = formatter.format_lap([sample_row, reordered], metadata)
        lines = result.strip().split("\n")
        first_sample = lines[-2]
        second_sample = lines[-1]
        assert first_sample.startswith("1.000")
        assert second_sample.startswith("12.346")

    def test_sector_boundaries_in_metadata(self, formatter, sample_row):
        """Test that sector boundaries appear in CSV metadata"""
        metadata = OrderedDict([
            ("Format", "LMUTelemetry v2"),
            ("Version", "1"),
            ("Player", "Test Driver"),
            ("TrackName", "Test Track"),
            ("CarName", "Test Car"),
            ("SessionUTC", "2025-01-01T00:00:00Z"),
            ("LapTime [s]", "95.123"),
            ("TrackLen [m]", "5400.00"),
            ("NumSectors", "3"),
            ("Sector1End [m]", "1800.00"),
            ("Sector2End [m]", "3600.00"),
            ("Sector3End [m]", "5400.00"),
        ])

        result = formatter.format_lap([sample_row], metadata)
        lines = result.strip().split("\n")

        assert "NumSectors,3" in lines
        assert "Sector1End [m],1800.00" in lines
        assert "Sector2End [m],3600.00" in lines
        assert "Sector3End [m],5400.00" in lines
