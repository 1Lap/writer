"""Session state management and lap tracking"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List

from src.mvp_format import SampleNormalizer


class SessionState(Enum):
    """Session states"""
    IDLE = "idle"
    DETECTED = "detected"
    LOGGING = "logging"
    PAUSED = "paused"
    ERROR = "error"


class SessionManager:
    """
    Manages session state and lap tracking

    Responsibilities:
    - Track session state (idle, logging, etc.)
    - Detect lap changes
    - Buffer telemetry samples for current lap
    - Generate session IDs
    """

    def __init__(self, normalizer: SampleNormalizer | None = None):
        self.state = SessionState.IDLE
        self.current_lap = 0
        self.current_session_id = None
        self.lap_samples = []  # Buffer for current lap (normalized samples)
        self.normalizer = normalizer or SampleNormalizer()

    def update(self, telemetry: Dict[str, Any]) -> Dict[str, bool]:
        """
        Update session state based on telemetry

        Args:
            telemetry: Current telemetry data

        Returns:
            Dict with events: {'lap_completed': True, ...}
        """
        events = {}

        # Detect lap change
        new_lap = telemetry.get('lap', 0)
        if new_lap != self.current_lap and self.current_lap > 0:
            events['lap_completed'] = True

        self.current_lap = new_lap

        return events

    def add_sample(self, telemetry: Dict[str, Any]):
        """
        Add telemetry sample to current lap buffer

        Args:
            telemetry: Telemetry data to buffer
        """
        normalized = self.normalizer.normalize(telemetry)
        self.lap_samples.append(normalized)

    def get_lap_data(self) -> List[Dict[str, Any]]:
        """
        Get all samples for current lap

        Returns:
            List of telemetry samples
        """
        return self.lap_samples.copy()

    def clear_lap_buffer(self):
        """Clear lap buffer after write"""
        self.lap_samples.clear()

    def generate_session_id(self) -> str:
        """
        Generate unique session ID based on timestamp

        Returns:
            Session ID string (timestamp-based)
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return timestamp

    def get_lap_summary(self) -> Dict[str, Any]:
        """
        Calculate lap summary from buffered samples

        Returns:
            Dictionary with lap summary (times, sectors, etc.)
        """
        if not self.lap_samples:
            return {}

        last_sample = self.lap_samples[-1]

        return {
            'lap': self.current_lap,
            'lap_time': last_sample.get('LapTime [s]', 0.0),
            'samples_count': len(self.lap_samples),
            'lap_distance': last_sample.get('LapDistance [m]', 0.0),
        }
