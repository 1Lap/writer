"""Process monitoring for auto-detection of LMU"""

import time
import sys
from pathlib import Path
import psutil
from typing import Dict, Any, Optional


class ProcessMonitor:
    """
    Monitors for target process (LMU.exe or test process on macOS)

    On Windows: Looks for LMU.exe
    On macOS: Configurable test process (e.g., "Chrome", "python")
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize process monitor

        Args:
            config: Configuration dictionary with optional 'target_process' key
        """
        # On Windows: look for LMU.exe
        # On macOS: configurable test process (e.g., "Chrome", "python")
        self.target_process = config.get('target_process', 'LMU.exe')
        self._process = None

    def is_running(self) -> bool:
        """
        Check if target process is running

        Returns:
            True if process found, False otherwise
        """
        # Quick self-check so environments that restrict process listing still
        # detect the current Python interpreter when it matches the target.
        if self._matches_current_process():
            return True

        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and self.target_process.lower() in proc_name.lower():
                        self._process = proc
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process disappeared or we don't have permission to access it
                    continue
        except (psutil.Error, PermissionError):
            # If we can't iterate processes, fall back to inspecting the
            # current Python process.
            return self._matches_current_process()

        # If we didn't match while iterating, also check the current process
        # name as a last resort (useful in constrained environments where
        # process iteration may be limited).
        return self._matches_current_process()

    def _matches_current_process(self) -> bool:
        """Fallback when process iteration is not permitted."""
        target = self.target_process.lower()

        # Use the Python executable name as a lightweight fallback that doesn't
        # require process iteration permissions.
        exe_name = Path(sys.executable).name.lower()
        if target in exe_name:
            return True

        try:
            current = psutil.Process()
            proc_name = current.name()
            if proc_name and target in proc_name.lower():
                self._process = current
                return True
        except (psutil.Error, PermissionError):
            pass
        return False

    def wait_for_process(self, timeout: Optional[float] = None) -> bool:
        """
        Block until process appears or timeout

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if process found, False if timeout
        """
        start = time.time()
        while True:
            if self.is_running():
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(1.0)

    def get_process_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the detected process

        Returns:
            Dictionary with process info or None if not running
        """
        if self._process:
            try:
                return {
                    'pid': self._process.pid,
                    'name': self._process.name(),
                    'status': self._process.status(),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        return None
