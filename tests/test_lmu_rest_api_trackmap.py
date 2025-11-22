"""
Tests for LMU REST API track map functionality

Tests the get_trackmap() method that fetches track outline and pit lane
waypoints from the LMU REST API /rest/watch/trackmap endpoint.
"""

import json
import pytest
from unittest.mock import Mock, patch
from src.lmu_rest_api import LMURestAPI


# Sample track map data (simplified from real LMU response)
SAMPLE_TRACKMAP_RESPONSE = [
    # Type 0 - Track outline (10 points for testing)
    {"type": 0, "x": -112.67, "y": 38.81, "z": -100.92},
    {"type": 0, "x": -111.46, "y": 38.95, "z": -105.79},
    {"type": 0, "x": -110.25, "y": 39.09, "z": -110.62},
    {"type": 0, "x": -109.05, "y": 39.23, "z": -115.45},
    {"type": 0, "x": -107.86, "y": 39.37, "z": -120.28},
    {"type": 0, "x": -106.68, "y": 39.51, "z": -125.11},
    {"type": 0, "x": -105.50, "y": 39.65, "z": -129.94},
    {"type": 0, "x": -104.33, "y": 39.79, "z": -134.77},
    {"type": 0, "x": -103.17, "y": 39.93, "z": -139.60},
    {"type": 0, "x": -102.01, "y": 40.07, "z": -144.43},

    # Type 1 - Pit lane (5 points for testing)
    {"type": 1, "x": -95.50, "y": 38.50, "z": -95.30},
    {"type": 1, "x": -94.20, "y": 38.45, "z": -98.10},
    {"type": 1, "x": -92.90, "y": 38.40, "z": -100.90},
    {"type": 1, "x": -91.60, "y": 38.35, "z": -103.70},
    {"type": 1, "x": -90.30, "y": 38.30, "z": -106.50},

    # Type 2-5 - Pit bays (should be filtered out)
    {"type": 2, "x": -37.29, "y": 38.20, "z": -351.83},
    {"type": 2, "x": -34.90, "y": 38.21, "z": -349.63},
    {"type": 3, "x": -38.60, "y": 38.19, "z": -347.11},
    {"type": 3, "x": -36.22, "y": 38.20, "z": -344.90},
]


class TestGetTrackmap:
    """Tests for get_trackmap() method"""

    def test_get_trackmap_success(self):
        """Test successful track map fetch"""
        api = LMURestAPI()

        # Mock the API response
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = api.get_trackmap()

        # Should return dict with track and pit_lane
        assert isinstance(result, dict)
        assert 'track' in result
        assert 'pit_lane' in result
        assert 'waypoint_count' in result
        assert 'source' in result

        # Track should have 10 waypoints (Type 0)
        assert len(result['track']) == 10
        assert result['track'][0] == [-112.67, -100.92]  # X, Z coords
        assert result['track'][9] == [-102.01, -144.43]

        # Pit lane should have 5 waypoints (Type 1)
        assert len(result['pit_lane']) == 5
        assert result['pit_lane'][0] == [-95.50, -95.30]
        assert result['pit_lane'][4] == [-90.30, -106.50]

        # Waypoint count should be 15 (10 track + 5 pit)
        assert result['waypoint_count'] == 15
        assert result['source'] == 'LMU_REST_API'

    def test_get_trackmap_filters_pit_bays(self):
        """Test that pit bays (types 2+) are filtered out"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = api.get_trackmap()

        # Should NOT include pit bay waypoints (types 2, 3, etc.)
        # Total should be 15, not 19
        assert result['waypoint_count'] == 15

        # Verify no pit bay coordinates in results
        all_coords = result['track'] + result['pit_lane']
        assert [-37.29, -351.83] not in all_coords  # Type 2 pit bay

    def test_get_trackmap_caches_by_track_name(self):
        """Test that track maps are cached by track name"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            # First call - should fetch from API
            result1 = api.get_trackmap(track_name="Bahrain")

            # Second call with same track - should return cached
            result2 = api.get_trackmap(track_name="Bahrain")

            # Should only have called API once
            assert mock_urlopen.call_count == 1

            # Results should be identical
            assert result1 == result2

    def test_get_trackmap_different_tracks(self):
        """Test that different tracks are cached separately"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            # Fetch for two different tracks
            result1 = api.get_trackmap(track_name="Bahrain")
            result2 = api.get_trackmap(track_name="Spa")

            # Should have called API twice (different tracks)
            assert mock_urlopen.call_count == 2

    def test_get_trackmap_force_refresh(self):
        """Test force refresh bypasses cache"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            # First call
            api.get_trackmap(track_name="Bahrain")

            # Second call with force_refresh
            api.get_trackmap(track_name="Bahrain", force_refresh=True)

            # Should have called API twice
            assert mock_urlopen.call_count == 2

    def test_get_trackmap_api_unavailable(self):
        """Test graceful handling when API is unavailable"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen', side_effect=ConnectionRefusedError()):
            result = api.get_trackmap()

        # Should return empty dict
        assert result == {}

    def test_get_trackmap_http_error(self):
        """Test handling of HTTP errors"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError(
                url="http://localhost:6397/rest/watch/trackmap",
                code=404,
                msg="Not Found",
                hdrs={},
                fp=None
            )

            result = api.get_trackmap()

        # Should return empty dict
        assert result == {}

    def test_get_trackmap_timeout(self):
        """Test handling of timeouts"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            import socket
            mock_urlopen.side_effect = socket.timeout()

            result = api.get_trackmap()

        # Should return empty dict
        assert result == {}

    def test_get_trackmap_invalid_json(self):
        """Test handling of invalid JSON response"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = b"invalid json{{"
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = api.get_trackmap()

        # Should return empty dict on JSON parse error
        assert result == {}

    def test_get_trackmap_empty_response(self):
        """Test handling of empty waypoint list"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps([]).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = api.get_trackmap()

        # Should return empty lists
        assert result == {
            'track': [],
            'pit_lane': [],
            'waypoint_count': 0,
            'source': 'LMU_REST_API'
        }

    def test_get_trackmap_only_type0(self):
        """Test track map with only Type 0 waypoints (no pit lane)"""
        api = LMURestAPI()

        # Response with only Type 0
        type0_only = [w for w in SAMPLE_TRACKMAP_RESPONSE if w['type'] == 0]

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(type0_only).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = api.get_trackmap()

        # Should have track but empty pit_lane
        assert len(result['track']) == 10
        assert len(result['pit_lane']) == 0
        assert result['waypoint_count'] == 10

    def test_clear_trackmap_cache(self):
        """Test clearing track map cache"""
        api = LMURestAPI()

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(SAMPLE_TRACKMAP_RESPONSE).encode('utf-8')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            # Fetch and cache
            api.get_trackmap(track_name="Bahrain")

            # Clear cache
            api.clear_cache()

            # Fetch again - should call API again
            api.get_trackmap(track_name="Bahrain")

            # Should have called API twice
            assert mock_urlopen.call_count == 2
