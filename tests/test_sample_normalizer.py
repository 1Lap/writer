"""Unit tests for the SampleNormalizer."""

import pytest

from src.mvp_format import SampleNormalizer


class TestSampleNormalizer:
    def test_scales_fractional_inputs(self):
        normalizer = SampleNormalizer()
        sample = normalizer.normalize({'lap_distance': 10.0, 'lap_time': 0.5, 'throttle': 0.65, 'brake': 1.2})

        assert sample['ThrottlePercentage [%]'] == pytest.approx(65.0)
        # Brake fractional should clamp at 100
        assert sample['BrakePercentage [%]'] == 100.0

    def test_converts_steering_ratio_to_percent(self):
        normalizer = SampleNormalizer()
        sample = normalizer.normalize({'lap_distance': 0.0, 'lap_time': 0.0, 'steering': -1.25})

        assert sample['Steer [%]'] == pytest.approx(-100.0)

    def test_preserves_explicit_percentages(self):
        normalizer = SampleNormalizer()
        sample = normalizer.normalize({'lap_distance': 0.0, 'lap_time': 0.0, 'throttle': 75.5, 'brake': 3.2})

        assert sample['ThrottlePercentage [%]'] == pytest.approx(75.5)
        assert sample['BrakePercentage [%]'] == pytest.approx(3.2)

    def test_handles_missing_coordinates(self):
        normalizer = SampleNormalizer()
        sample = normalizer.normalize({'lap_distance': 0.0, 'lap_time': 0.0, 'position_x': 5.0})

        assert sample['X [m]'] == 5.0
        assert sample['Y [m]'] is None
        assert sample['Z [m]'] is None

    def test_sector_estimation_uses_track_length(self):
        normalizer = SampleNormalizer()
        sample = normalizer.normalize({'lap_distance': 300.0, 'lap_time': 0.0, 'track_length': 900.0})

        assert sample['Sector [int]'] == 1
