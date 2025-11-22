# 1Lap Race Dashboard System - Implementation Plan

**Version:** 1.0
**Date:** 2025-11-22
**Status:** Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Data Sources & Capabilities](#data-sources--capabilities)
5. [Implementation Phases](#implementation-phases)
6. [API Contracts](#api-contracts)
7. [Deployment Options](#deployment-options)
8. [Testing Strategy](#testing-strategy)
9. [Future Enhancements](#future-enhancements)

---

## Overview

### Problem Statement

During endurance races, drivers can change car settings (tire pressures, fuel strategy, wing angles, etc.), but the rest of the team cannot see these settings in real-time. When the team wants to confirm a setting, they must ask the driver, which is distracting during the race.

### Solution

Create a real-time race dashboard system that monitors car telemetry, setup, and garage settings, then publishes this data to a web-based dashboard accessible to the entire team via a secret URL.

### Use Case

1. Driver starts race with `monitor` app running in background
2. Monitor reads car data from LMU and publishes to `server`
3. Server generates a secret URL (e.g., `https://dashboard.1lap.io/abc-def-ghi`)
4. Team members open URL on any device (laptop, tablet, phone)
5. Dashboard shows real-time telemetry, setup, and pit strategy
6. Team can monitor without distracting driver

**Future enhancement:** Add controls (set fuel amount, tire pressures, next driver, etc.) via dashboard.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         LMU (Windows)                           │
│  ┌─────────────────┐              ┌────────────────────┐       │
│  │ Shared Memory   │              │   REST API         │       │
│  │ (Telemetry)     │              │   (localhost:6397) │       │
│  │ - 50-100Hz      │              │   - Setup data     │       │
│  │ - All cars      │              │   - Vehicle meta   │       │
│  └────────┬────────┘              └─────────┬──────────┘       │
└───────────┼─────────────────────────────────┼──────────────────┘
            │                                 │
            └────────────┬────────────────────┘
                         ▼
            ┌─────────────────────────┐
            │   monitor (Python)      │
            │   - Reads shared memory │
            │   - Reads REST API      │
            │   - Packages data       │
            │   - Publishes to server │
            └────────────┬────────────┘
                         │ WebSocket/HTTP
                         ▼
            ┌─────────────────────────┐
            │   server (Flask)        │
            │   - Session manager     │
            │   - WebSocket broadcast │
            │   - Serves dashboard UI │
            └────────────┬────────────┘
                         │ WebSocket (bidirectional)
                         ▼
            ┌─────────────────────────┐
            │   Web Browser           │
            │   - Dashboard UI        │
            │   - Auto-updating       │
            │   - Mobile responsive   │
            └─────────────────────────┘
```

### Three-Repository Architecture

| Repository | Purpose | Language | Deployment |
|------------|---------|----------|------------|
| **monitor** | Data collector (fork of `writer`) | Python | Windows (with LMU) |
| **server** | Dashboard web service | Python (Flask) | Local or Cloud |
| **dashboard-ui** (optional) | Frontend (if separate) | HTML/JS/CSS | Static hosting |

---

## Repository Structure

### `monitor` Repository (Fork of `writer`)

#### What to Keep from `writer`

```
monitor/
├── src/
│   ├── telemetry/
│   │   ├── telemetry_interface.py      ✅ Keep
│   │   ├── telemetry_real.py           ✅ Keep (shared memory reader)
│   │   └── telemetry_mock.py           ✅ Keep (for testing)
│   ├── lmu_rest_api.py                 ✅ Keep (setup fetching)
│   ├── process_monitor.py              ✅ Keep (detect LMU.exe)
│   └── dashboard_publisher.py          ✅ NEW (publish to server)
├── tests/
│   ├── test_telemetry_real.py          ✅ Keep
│   ├── test_lmu_rest_api.py            ✅ Keep
│   └── test_dashboard_publisher.py     ✅ NEW
├── monitor.py                          ✅ NEW (entry point)
├── config.json                         ✅ NEW (simple config)
├── requirements.txt                    ✅ Minimal deps
├── README.md                           ✅ Monitor-specific docs
└── RACE_DASHBOARD_PLAN.md              ✅ This file
```

#### What to Remove from `writer`

```
❌ src/csv_formatter.py          (not needed for dashboard)
❌ src/file_manager.py            (not saving files)
❌ src/session_manager.py         (or simplify - no lap tracking)
❌ src/tray_ui.py                 (no UI in monitor)
❌ src/settings_ui.py             (simple config instead)
❌ src/update_*.py                (auto-update not needed)
❌ src/version.py                 (not needed)
❌ tray_app.py                    (no UI)
❌ example_app.py                 (replace with monitor.py)
❌ installer/                     (not distributing as exe)
❌ build.bat                      (not building exe)
❌ updater.py                     (not needed)
```

#### New Files to Add

**`monitor.py`** - Entry point
```python
"""
1Lap Race Dashboard Monitor
Reads LMU telemetry and publishes to dashboard server
"""
import json
import time
from src.telemetry.telemetry_interface import get_telemetry_reader
from src.lmu_rest_api import LMURestAPI
from src.process_monitor import ProcessMonitor
from src.dashboard_publisher import DashboardPublisher

def main():
    # Load config
    with open('config.json') as f:
        config = json.load(f)

    # Initialize components
    telemetry = get_telemetry_reader()
    rest_api = LMURestAPI()
    process_monitor = ProcessMonitor(config)
    publisher = DashboardPublisher(
        server_url=config['server_url'],
        session_id=config.get('session_id', 'auto')
    )

    # Main loop
    setup_sent = False
    while True:
        if not process_monitor.is_running():
            time.sleep(1)
            continue

        # Send setup once per session
        if not setup_sent and rest_api.is_available():
            setup = rest_api.fetch_setup_data()
            if setup:
                publisher.publish_setup(setup)
                setup_sent = True

        # Read and publish telemetry
        data = telemetry.read()
        if data:
            publisher.publish_telemetry(data)

        time.sleep(1.0 / config['update_rate_hz'])

if __name__ == '__main__':
    main()
```

**`config.json`** - Configuration
```json
{
  "server_url": "http://localhost:5000",
  "session_id": "auto",
  "update_rate_hz": 2,
  "poll_interval": 0.01,
  "target_process": "LMU.exe"
}
```

**`src/dashboard_publisher.py`** - Publisher module
```python
"""Publish telemetry to dashboard server"""
import socketio
import time
from typing import Dict, Any
from datetime import datetime

class DashboardPublisher:
    """
    Publishes telemetry and setup data to dashboard server via WebSocket
    """

    def __init__(self, server_url: str, session_id: str = 'auto'):
        """
        Initialize publisher

        Args:
            server_url: Dashboard server URL (e.g., 'http://localhost:5000')
            session_id: Session ID or 'auto' to get from server
        """
        self.sio = socketio.Client()
        self.server_url = server_url
        self.session_id = session_id
        self.connected = False

        @self.sio.event
        def connect():
            print(f"[Publisher] Connected to {server_url}")
            self.connected = True

            # Request session ID if auto
            if self.session_id == 'auto':
                self.sio.emit('request_session_id', {})

        @self.sio.event
        def disconnect():
            print("[Publisher] Disconnected")
            self.connected = False

        @self.sio.event
        def session_id_assigned(data):
            self.session_id = data['session_id']
            print(f"[Publisher] Session ID: {self.session_id}")
            print(f"[Publisher] Dashboard URL: {self.server_url}/dashboard/{self.session_id}")

    def connect(self):
        """Connect to server"""
        try:
            self.sio.connect(self.server_url)
        except Exception as e:
            print(f"[Publisher] Connection failed: {e}")

    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            self.sio.disconnect()

    def publish_setup(self, setup_data: Dict[str, Any]):
        """
        Publish car setup (once per session)

        Args:
            setup_data: Setup dictionary from REST API
        """
        if self.connected and self.session_id != 'auto':
            self.sio.emit('setup_data', {
                'session_id': self.session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'setup': setup_data
            })
            print(f"[Publisher] Setup data sent")

    def publish_telemetry(self, telemetry_data: Dict[str, Any]):
        """
        Publish live telemetry

        Args:
            telemetry_data: Telemetry dictionary from TelemetryReader
        """
        if self.connected and self.session_id != 'auto':
            # Extract key fields for dashboard
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'lap': telemetry_data.get('lap', 0),
                'position': telemetry_data.get('race_position', 0),
                'lap_time': telemetry_data.get('lap_time', 0.0),
                'fuel': telemetry_data.get('fuel_remaining', 0.0),
                'fuel_capacity': telemetry_data.get('fuel_at_start', 90.0),
                'tire_pressures': telemetry_data.get('tyre_pressure', {}),
                'tire_temps': telemetry_data.get('tyre_temp', {}),
                'tire_wear': telemetry_data.get('tyre_wear', {}),
                'brake_temps': telemetry_data.get('brake_temp', {}),
                'engine_water_temp': telemetry_data.get('engine_temp', 0.0),
                'track_temp': telemetry_data.get('track_temp', 0.0),
                'ambient_temp': telemetry_data.get('ambient_temp', 0.0),
                'speed': telemetry_data.get('speed', 0.0),
                'gear': telemetry_data.get('gear', 0),
                'rpm': telemetry_data.get('rpm', 0.0),
                # Session info
                'player_name': telemetry_data.get('player_name', ''),
                'car_name': telemetry_data.get('car_name', ''),
                'track_name': telemetry_data.get('track_name', ''),
                'session_type': telemetry_data.get('session_type', ''),
            }

            self.sio.emit('telemetry_update', {
                'session_id': self.session_id,
                'telemetry': dashboard_data
            })
```

**`requirements.txt`**
```txt
pyRfactor2SharedMemory>=0.1.0
psutil>=5.9.0
python-socketio[client]>=5.9.0
```

**`README.md`**
```markdown
# 1Lap Race Dashboard Monitor

Background service that reads LMU telemetry and publishes to dashboard server.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure server URL in `config.json`

3. Run monitor:
   ```bash
   python monitor.py
   ```

## Configuration

Edit `config.json`:
- `server_url`: Dashboard server URL (e.g., `http://localhost:5000`)
- `update_rate_hz`: Telemetry publish rate (default: 2Hz)
- `target_process`: Process to monitor (default: `LMU.exe`)

## How It Works

1. Monitors for LMU.exe process
2. Reads telemetry from shared memory (50-100Hz)
3. Fetches car setup from REST API (once per session)
4. Publishes to dashboard server (2Hz)
5. Server broadcasts to web dashboards

## See Also

- [server](https://github.com/1Lap/server) - Dashboard web service
- [RACE_DASHBOARD_PLAN.md](RACE_DASHBOARD_PLAN.md) - Complete implementation plan
```

---

### `server` Repository (New)

#### Directory Structure

```
server/
├── app/
│   ├── __init__.py                  # Flask app factory
│   ├── main.py                      # Main server logic
│   ├── session_manager.py           # UUID generation, session tracking
│   └── models.py                    # Data structures
├── static/
│   ├── css/
│   │   └── dashboard.css            # Dashboard styles
│   ├── js/
│   │   └── dashboard.js             # WebSocket client + UI logic
│   └── img/
│       └── logo.png                 # 1Lap logo
├── templates/
│   └── dashboard.html               # Single-page dashboard
├── tests/
│   ├── test_session_manager.py
│   ├── test_websocket.py
│   └── test_main.py
├── run.py                           # Entry point
├── config.py                        # Server configuration
├── requirements.txt
├── Dockerfile                       # Docker deployment (optional)
├── .env.example                     # Environment variables template
├── README.md
└── RACE_DASHBOARD_PLAN.md           # This file
```

#### Key Files

**`run.py`** - Entry point
```python
"""
1Lap Race Dashboard Server
Web service for broadcasting telemetry to team dashboards
"""
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("1Lap Race Dashboard Server")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("Waiting for monitor connections...")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

**`app/__init__.py`** - Flask app factory
```python
"""Flask app factory"""
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    socketio.init_app(app, cors_allowed_origins="*")

    # Import routes after socketio init
    from app import main

    return app
```

**`app/main.py`** - Main server logic
```python
"""Dashboard server main logic"""
from flask import render_template, request
from flask_socketio import emit, join_room
from app import socketio
from app.session_manager import SessionManager

# Initialize session manager
session_mgr = SessionManager()

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"[Server] Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"[Server] Client disconnected: {request.sid}")

@socketio.on('request_session_id')
def handle_request_session_id(data):
    """Monitor requests new session ID"""
    session_id = session_mgr.create_session()
    emit('session_id_assigned', {'session_id': session_id})
    print(f"[Server] New session created: {session_id}")

@socketio.on('setup_data')
def handle_setup(data):
    """Receive setup from monitor"""
    session_id = data['session_id']
    setup = data['setup']
    timestamp = data['timestamp']

    session_mgr.update_setup(session_id, setup, timestamp)

    # Broadcast to all dashboards watching this session
    emit('setup_update', data, room=session_id)
    print(f"[Server] Setup data received for session {session_id}")

@socketio.on('telemetry_update')
def handle_telemetry(data):
    """Receive telemetry from monitor"""
    session_id = data['session_id']
    telemetry = data['telemetry']

    session_mgr.update_telemetry(session_id, telemetry)

    # Broadcast to dashboards
    emit('telemetry_update', data, room=session_id)

@socketio.on('join_session')
def handle_join_session(data):
    """Dashboard client joins session room"""
    session_id = data['session_id']
    join_room(session_id)

    # Send current data if available
    session_data = session_mgr.get_session(session_id)
    if session_data:
        if session_data.get('setup'):
            emit('setup_update', {
                'session_id': session_id,
                'setup': session_data['setup'],
                'timestamp': session_data.get('setup_timestamp')
            })
        if session_data.get('telemetry'):
            emit('telemetry_update', {
                'session_id': session_id,
                'telemetry': session_data['telemetry']
            })

    print(f"[Server] Dashboard joined session {session_id}")

# Flask routes
from flask import current_app

@current_app.route('/')
def index():
    """Home page"""
    return "<h1>1Lap Race Dashboard Server</h1><p>Waiting for sessions...</p>"

@current_app.route('/dashboard/<session_id>')
def dashboard(session_id):
    """Serve dashboard for specific session"""
    return render_template('dashboard.html', session_id=session_id)
```

**`app/session_manager.py`** - Session management
```python
"""Session manager for tracking active sessions"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class SessionManager:
    """Manages active dashboard sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """
        Create new session with unique ID

        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created_at': datetime.utcnow().isoformat(),
            'setup': None,
            'setup_timestamp': None,
            'telemetry': None,
            'last_update': None
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)

    def update_setup(self, session_id: str, setup: Dict[str, Any], timestamp: str):
        """Update session setup data"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        self.sessions[session_id]['setup'] = setup
        self.sessions[session_id]['setup_timestamp'] = timestamp

    def update_telemetry(self, session_id: str, telemetry: Dict[str, Any]):
        """Update session telemetry data"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        self.sessions[session_id]['telemetry'] = telemetry
        self.sessions[session_id]['last_update'] = datetime.utcnow().isoformat()

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_active_sessions(self) -> list:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
```

**`config.py`** - Configuration
```python
"""Server configuration"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
```

**`requirements.txt`**
```txt
flask>=2.3.0
flask-socketio>=5.3.0
python-socketio>=5.9.0
gunicorn>=21.0.0  # For production deployment
```

**`templates/dashboard.html`** - Dashboard UI
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>1Lap Race Dashboard - {{ session_id }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏁 1Lap Race Dashboard</h1>
            <p class="session-id">Session: {{ session_id }}</p>
            <p id="connection-status" class="status disconnected">⚪ Disconnected</p>
        </header>

        <!-- Session Info -->
        <section class="card">
            <h2>📊 Session Info</h2>
            <div class="grid-2">
                <div>
                    <span class="label">Driver:</span>
                    <span id="player-name">-</span>
                </div>
                <div>
                    <span class="label">Car:</span>
                    <span id="car-name">-</span>
                </div>
                <div>
                    <span class="label">Track:</span>
                    <span id="track-name">-</span>
                </div>
                <div>
                    <span class="label">Session:</span>
                    <span id="session-type">-</span>
                </div>
                <div>
                    <span class="label">Position:</span>
                    <span id="position" class="big-value">-</span>
                </div>
                <div>
                    <span class="label">Lap:</span>
                    <span id="lap" class="big-value">-</span>
                </div>
            </div>
        </section>

        <!-- Live Telemetry -->
        <section class="card">
            <h2>🔴 Live Telemetry</h2>

            <div class="telemetry-group">
                <h3>⛽ Fuel</h3>
                <div class="progress-bar">
                    <div id="fuel-bar" class="progress-fill" style="width: 0%"></div>
                </div>
                <p><span id="fuel">0.0</span>L / <span id="fuel-capacity">90.0</span>L (<span id="fuel-percent">0</span>%)</p>
                <p class="hint">Est. laps remaining: <span id="fuel-laps">-</span></p>
            </div>

            <div class="telemetry-group">
                <h3>🔥 Tire Temperatures</h3>
                <div class="tire-grid">
                    <div class="tire">
                        <span class="label">FL</span>
                        <span id="tire-temp-fl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">FR</span>
                        <span id="tire-temp-fr" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RL</span>
                        <span id="tire-temp-rl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RR</span>
                        <span id="tire-temp-rr" class="value">-</span>
                    </div>
                </div>
            </div>

            <div class="telemetry-group">
                <h3>💨 Tire Pressures</h3>
                <div class="tire-grid">
                    <div class="tire">
                        <span class="label">FL</span>
                        <span id="tire-psi-fl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">FR</span>
                        <span id="tire-psi-fr" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RL</span>
                        <span id="tire-psi-rl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RR</span>
                        <span id="tire-psi-rr" class="value">-</span>
                    </div>
                </div>
            </div>

            <div class="telemetry-group">
                <h3>🔴 Brake Temperatures</h3>
                <div class="tire-grid">
                    <div class="tire">
                        <span class="label">FL</span>
                        <span id="brake-temp-fl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">FR</span>
                        <span id="brake-temp-fr" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RL</span>
                        <span id="brake-temp-rl" class="value">-</span>
                    </div>
                    <div class="tire">
                        <span class="label">RR</span>
                        <span id="brake-temp-rr" class="value">-</span>
                    </div>
                </div>
            </div>

            <div class="telemetry-group">
                <h3>🌡️ Engine</h3>
                <p>Water: <span id="engine-temp">-</span>°C</p>
            </div>

            <div class="telemetry-group">
                <h3>🌤️ Weather</h3>
                <p>Track: <span id="track-temp">-</span>°C | Ambient: <span id="ambient-temp">-</span>°C</p>
            </div>
        </section>

        <!-- Car Setup -->
        <section class="card">
            <h2>🔧 Car Setup</h2>
            <p class="hint">Setup captured at session start</p>
            <div id="setup-container">
                <p class="hint">Waiting for setup data...</p>
            </div>
        </section>
    </div>

    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
    <script>
        // Initialize dashboard with session ID
        const sessionId = "{{ session_id }}";
        initDashboard(sessionId);
    </script>
</body>
</html>
```

**`static/js/dashboard.js`** - Dashboard JavaScript
```javascript
// WebSocket connection
let socket;

function initDashboard(sessionId) {
    // Connect to server
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);

        // Join session room
        socket.emit('join_session', {session_id: sessionId});
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    // Listen for setup updates
    socket.on('setup_update', (data) => {
        console.log('Setup update received:', data);
        updateSetup(data.setup);
    });

    // Listen for telemetry updates
    socket.on('telemetry_update', (data) => {
        updateTelemetry(data.telemetry);
    });
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.textContent = '🟢 Connected';
        statusEl.className = 'status connected';
    } else {
        statusEl.textContent = '🔴 Disconnected';
        statusEl.className = 'status disconnected';
    }
}

function updateTelemetry(data) {
    // Session info
    setText('player-name', data.player_name || '-');
    setText('car-name', data.car_name || '-');
    setText('track-name', data.track_name || '-');
    setText('session-type', data.session_type || '-');
    setText('position', data.position > 0 ? `P${data.position}` : '-');
    setText('lap', data.lap || '-');

    // Fuel
    const fuel = data.fuel || 0;
    const fuelCapacity = data.fuel_capacity || 90;
    const fuelPercent = Math.round((fuel / fuelCapacity) * 100);
    setText('fuel', fuel.toFixed(1));
    setText('fuel-capacity', fuelCapacity.toFixed(1));
    setText('fuel-percent', fuelPercent);
    setWidth('fuel-bar', fuelPercent);

    // Estimate laps remaining (rough: 3L per lap)
    const fuelPerLap = 3.0;
    const lapsRemaining = Math.floor(fuel / fuelPerLap);
    setText('fuel-laps', lapsRemaining);

    // Tires
    updateTireData(data.tire_temps, 'tire-temp', '°C');
    updateTireData(data.tire_pressures, 'tire-psi', ' PSI');
    updateTireData(data.brake_temps, 'brake-temp', '°C');

    // Engine
    setText('engine-temp', data.engine_water_temp ? data.engine_water_temp.toFixed(1) : '-');

    // Weather
    setText('track-temp', data.track_temp ? data.track_temp.toFixed(1) : '-');
    setText('ambient-temp', data.ambient_temp ? data.ambient_temp.toFixed(1) : '-');
}

function updateTireData(tireObj, prefix, suffix) {
    if (!tireObj) return;

    const positions = ['fl', 'fr', 'rl', 'rr'];
    positions.forEach(pos => {
        const value = tireObj[pos];
        const text = value !== undefined ? value.toFixed(1) + suffix : '-';
        setText(`${prefix}-${pos}`, text);
    });
}

function updateSetup(setup) {
    const container = document.getElementById('setup-container');

    if (!setup || Object.keys(setup).length === 0) {
        container.innerHTML = '<p class="hint">No setup data available</p>';
        return;
    }

    // Display setup as nested structure
    container.innerHTML = '<pre>' + JSON.stringify(setup, null, 2) + '</pre>';
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setWidth(id, percent) {
    const el = document.getElementById(id);
    if (el) el.style.width = percent + '%';
}
```

**`static/css/dashboard.css`** - Styles
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, sans-serif;
    background: #0a0a0a;
    color: #e0e0e0;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #333;
}

h1 {
    color: #fff;
    margin-bottom: 10px;
}

.session-id {
    color: #888;
    font-size: 0.9em;
    font-family: monospace;
}

.status {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.9em;
    margin-top: 10px;
}

.status.connected {
    background: #1a4d1a;
    color: #4ade80;
}

.status.disconnected {
    background: #4d1a1a;
    color: #f87171;
}

.card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

h2 {
    color: #fff;
    margin-bottom: 15px;
    font-size: 1.3em;
}

h3 {
    color: #ccc;
    margin-bottom: 10px;
    font-size: 1.1em;
}

.grid-2 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.label {
    color: #888;
    margin-right: 8px;
}

.big-value {
    font-size: 1.3em;
    font-weight: bold;
    color: #4ade80;
}

.telemetry-group {
    margin-bottom: 25px;
}

.progress-bar {
    background: #333;
    height: 30px;
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e);
    transition: width 0.3s ease;
}

.tire-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    max-width: 400px;
}

.tire {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
}

.tire .label {
    display: block;
    font-size: 0.9em;
    margin-bottom: 5px;
}

.tire .value {
    display: block;
    font-size: 1.5em;
    font-weight: bold;
    color: #60a5fa;
}

.hint {
    color: #666;
    font-size: 0.9em;
    margin-top: 5px;
}

pre {
    background: #2a2a2a;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    font-size: 0.85em;
    color: #a0a0a0;
}

/* Mobile responsive */
@media (max-width: 768px) {
    body {
        padding: 10px;
    }

    .card {
        padding: 15px;
    }

    .tire-grid {
        grid-template-columns: 1fr 1fr;
    }
}
```

**`README.md`**
```markdown
# 1Lap Race Dashboard Server

Web service for broadcasting LMU telemetry to team dashboards.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run server:
   ```bash
   python run.py
   ```

3. Server runs at `http://localhost:5000`

## Usage

1. Start server
2. Run `monitor` app (connects automatically)
3. Monitor will print dashboard URL: `http://localhost:5000/dashboard/<session-id>`
4. Share URL with team members
5. Dashboard updates in real-time

## Configuration

Edit `config.py` or set environment variables:
- `SECRET_KEY`: Flask secret key
- `DEBUG`: Debug mode (default: True)
- `HOST`: Bind address (default: 0.0.0.0)
- `PORT`: Port number (default: 5000)

## Deployment

### Local Network
Run on driver's PC, team connects via LAN:
```bash
python run.py
# Access via: http://<driver-pc-ip>:5000/dashboard/<session-id>
```

### Cloud (Heroku)
```bash
# See DEPLOYMENT.md for cloud deployment guide
```

## See Also

- [monitor](https://github.com/1Lap/monitor) - Data collector
- [RACE_DASHBOARD_PLAN.md](RACE_DASHBOARD_PLAN.md) - Complete implementation plan
```

---

## Data Sources & Capabilities

### Shared Memory API (pyRfactor2SharedMemory)

**What's Available:**

| Category | Data Available | Update Rate | Notes |
|----------|----------------|-------------|-------|
| **Telemetry** | Fuel, tire temps/pressures/wear, brake temps, engine temps, speed, RPM, gear, inputs | 50-100Hz | All cars in session |
| **Pit Menu** | Current pit options, tire pressures, fuel amount, wing adjustments | 100Hz | Real-time pit strategy |
| **Session** | Track name, weather, temps, session type, time remaining | 5Hz | Session metadata |
| **Scoring** | Position, lap times, sector times, gaps | 5Hz | Race standings |
| **Physics** | Driver assists (TC, ABS, stability, auto-shift) | Event-based | Difficulty settings |

**Limitations:**
- ❌ Opponent car setups NOT available (competitive fairness)
- ✅ Opponent telemetry IS available (inputs, temps, pressures, fuel)

### LMU REST API (localhost:6397)

**What's Available:**

| Endpoint | Data | Frequency | Notes |
|----------|------|-----------|-------|
| `/rest/garage/setup` | Complete mechanical setup | Once per session | Player car only |
| `/rest/sessions/getAllVehicles` | Vehicle metadata (make, model, team, class) | Once per session | All cars |

**Setup Data Includes:**
- Suspension settings (springs, dampers, ARBs, ride height)
- Aerodynamics (wing angles, downforce levels)
- Gearing ratios
- Differential settings
- Brake balance
- Base tire pressures
- And more...

---

## Implementation Phases

### Phase 1: MVP (Read-Only Dashboard) ⏱️ 3-5 days

**Goals:**
- Monitor reads telemetry and setup
- Server broadcasts to dashboards
- Web UI shows real-time data
- Secret URL sharing

**Deliverables:**
1. ✅ `monitor` repo forked and cleaned up
2. ✅ `DashboardPublisher` implemented
3. ✅ `server` repo created with Flask app
4. ✅ WebSocket communication working
5. ✅ Dashboard UI displaying telemetry
6. ✅ Session management (UUID URLs)
7. ✅ Basic testing

**Success Criteria:**
- Monitor connects to LMU and server
- Dashboard shows live telemetry (2Hz updates)
- Setup data displayed on dashboard
- Multiple dashboards can view same session
- Works on local network

---

### Phase 2: Polish & Deployment ⏱️ 2-3 days

**Goals:**
- Production-ready deployment
- Error handling
- Mobile optimization
- Documentation

**Deliverables:**
1. ✅ Error handling (connection loss, API unavailable)
2. ✅ Reconnection logic (monitor → server)
3. ✅ Mobile-responsive UI
4. ✅ Deployment guide (local + cloud)
5. ✅ User documentation
6. ✅ Testing (unit + integration)

---

### Phase 3: Enhanced Features ⏱️ 3-5 days (Future)

**Goals:**
- Better UI/UX
- Additional telemetry displays
- Historical data
- Alerts/notifications

**Deliverables:**
1. ⬜ Lap time history chart
2. ⬜ Fuel consumption graph
3. ⬜ Tire degradation tracking
4. ⬜ Alerts (low fuel, high temps)
5. ⬜ Session recording/replay
6. ⬜ Export session data (CSV/JSON)

---

### Phase 4: Controls (Future) ⏱️ 3-7 days

**Goals:**
- Interactive controls
- Pit strategy management
- Two-way communication

**Deliverables:**
1. ⬜ Research LMU input API capabilities
2. ⬜ Implement pit menu controls
3. ⬜ UI controls (fuel amount, tire pressures, etc.)
4. ⬜ Authorization/permissions
5. ⬜ Confirmation dialogs
6. ⬜ Set next driver metadata
7. ⬜ Testing with live LMU

**Controls to Implement:**
- Set pit stop fuel amount
- Adjust tire pressures
- Change wing angles
- Set next driver (custom field)
- Toggle assists (if allowed)

---

## API Contracts

### Monitor → Server (WebSocket Events)

#### `request_session_id`
**Direction:** Monitor → Server
**Payload:**
```json
{}
```
**Response:** `session_id_assigned` event

---

#### `session_id_assigned`
**Direction:** Server → Monitor
**Payload:**
```json
{
  "session_id": "abc-def-ghi-jkl"
}
```

---

#### `setup_data`
**Direction:** Monitor → Server
**Frequency:** Once per session
**Payload:**
```json
{
  "session_id": "abc-def-ghi-jkl",
  "timestamp": "2025-11-22T14:30:22.123Z",
  "setup": {
    "suspension": {
      "front_spring_rate": 120.5,
      "rear_spring_rate": 115.0,
      ...
    },
    "aerodynamics": {
      "front_wing": 5,
      "rear_wing": 8
    },
    "brakes": {
      "brake_bias": 56.5
    },
    ...
  }
}
```

---

#### `telemetry_update`
**Direction:** Monitor → Server
**Frequency:** 2Hz (configurable)
**Payload:**
```json
{
  "session_id": "abc-def-ghi-jkl",
  "telemetry": {
    "timestamp": "2025-11-22T14:30:22.567Z",
    "lap": 45,
    "position": 3,
    "lap_time": 123.456,
    "fuel": 42.3,
    "fuel_capacity": 90.0,
    "tire_pressures": {
      "fl": 25.1,
      "fr": 24.9,
      "rl": 25.3,
      "rr": 25.0
    },
    "tire_temps": {
      "fl": 75.2,
      "fr": 73.8,
      "rl": 78.1,
      "rr": 76.5
    },
    "tire_wear": {
      "fl": 14.5,
      "fr": 13.2,
      "rl": 15.8,
      "rr": 12.1
    },
    "brake_temps": {
      "fl": 480.0,
      "fr": 485.0,
      "rl": 612.0,
      "rr": 615.0
    },
    "engine_water_temp": 109.5,
    "track_temp": 41.8,
    "ambient_temp": 24.0,
    "speed": 256.3,
    "gear": 6,
    "rpm": 7267.0,
    "player_name": "Driver Name",
    "car_name": "Toyota GR010",
    "track_name": "Bahrain International Circuit",
    "session_type": "Race"
  }
}
```

---

### Server → Dashboard (WebSocket Events)

#### `setup_update`
**Direction:** Server → Dashboard
**Frequency:** Once on join, then on updates
**Payload:** Same as `setup_data` from monitor

---

#### `telemetry_update`
**Direction:** Server → Dashboard
**Frequency:** 2Hz (as received from monitor)
**Payload:** Same as `telemetry_update` from monitor

---

### Dashboard → Server (WebSocket Events)

#### `join_session`
**Direction:** Dashboard → Server
**Frequency:** Once on connect
**Payload:**
```json
{
  "session_id": "abc-def-ghi-jkl"
}
```
**Response:** Current `setup_update` and `telemetry_update` if available

---

## Deployment Options

### Option 1: Local Network (Simplest)

**Setup:**
1. Run `server` on driver's PC
2. Run `monitor` on same PC
3. Team connects via LAN: `http://<driver-ip>:5000/dashboard/<session-id>`

**Pros:**
- ✅ No cloud costs
- ✅ Low latency
- ✅ No internet required

**Cons:**
- ❌ Requires LAN access
- ❌ Not accessible remotely

**Use Case:** Team in same location (e.g., LAN party, esports venue)

---

### Option 2: Cloud Hosted (Best for Remote Teams)

**Options:**
- **Heroku** (free tier available)
- **Railway** (generous free tier)
- **Render** (free tier available)
- **DigitalOcean** ($5/month)
- **AWS/GCP/Azure** (flexible pricing)

**Setup:**
1. Deploy `server` to cloud
2. Run `monitor` on driver's PC
3. Monitor connects to cloud server
4. Team accesses from anywhere: `https://dashboard.1lap.io/abc-def-ghi`

**Pros:**
- ✅ Accessible from anywhere
- ✅ No firewall/NAT issues
- ✅ Professional deployment

**Cons:**
- ❌ Requires internet
- ❌ Slight latency increase
- ❌ Monthly cost (or free tier limits)

**Use Case:** Remote team members, public viewing

---

### Option 3: Hybrid (Local + Cloud Backup)

**Setup:**
1. Primary: Local server on LAN
2. Backup: Cloud server for remote viewers
3. Monitor publishes to both

**Pros:**
- ✅ Best of both worlds
- ✅ Redundancy

**Cons:**
- ❌ More complex setup

---

### Deployment Guide: Heroku (Example)

```bash
# In server/ directory

# 1. Create Procfile
echo "web: gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 run:app" > Procfile

# 2. Create runtime.txt
echo "python-3.11.0" > runtime.txt

# 3. Install Heroku CLI and login
heroku login

# 4. Create app
heroku create 1lap-dashboard

# 5. Deploy
git push heroku main

# 6. Open
heroku open
```

---

## Testing Strategy

### Unit Tests

**`monitor` repo:**
```python
# tests/test_dashboard_publisher.py
def test_publisher_connect()
def test_publisher_publish_setup()
def test_publisher_publish_telemetry()
def test_publisher_reconnect_on_disconnect()
```

**`server` repo:**
```python
# tests/test_session_manager.py
def test_create_session()
def test_update_setup()
def test_update_telemetry()
def test_get_session()

# tests/test_websocket.py
def test_websocket_connect()
def test_join_session()
def test_setup_broadcast()
def test_telemetry_broadcast()
```

---

### Integration Tests

```python
# tests/test_integration.py
def test_end_to_end_flow():
    """Test complete flow: monitor → server → dashboard"""
    # 1. Start server
    # 2. Connect monitor
    # 3. Request session ID
    # 4. Publish setup
    # 5. Publish telemetry
    # 6. Connect dashboard
    # 7. Verify data received
```

---

### Manual Testing Checklist

**Phase 1 MVP:**
- [ ] Monitor connects to LMU
- [ ] Monitor connects to server
- [ ] Session ID generated
- [ ] Setup data published
- [ ] Telemetry published at 2Hz
- [ ] Dashboard loads
- [ ] Dashboard joins session
- [ ] Dashboard receives setup
- [ ] Dashboard receives telemetry
- [ ] UI updates in real-time
- [ ] Multiple dashboards can view same session
- [ ] Reconnection works after disconnect
- [ ] Mobile browser works

**Phase 2 Polish:**
- [ ] Error messages displayed clearly
- [ ] Graceful degradation (missing data)
- [ ] Mobile layout responsive
- [ ] Works on different browsers
- [ ] Local network deployment
- [ ] Cloud deployment (if applicable)

---

## Future Enhancements

### Phase 3: Enhanced Features

1. **Historical Data**
   - Store telemetry history (last 10 laps)
   - Lap time comparison chart
   - Fuel consumption trends
   - Tire degradation over time

2. **Alerts & Notifications**
   - Low fuel warning (< 2 laps)
   - High tire temps (> 90°C)
   - High brake temps (> 700°C)
   - Tire wear critical (> 80%)
   - Customizable thresholds

3. **Advanced UI**
   - Track map with car position
   - Sector analysis
   - Delta to best lap
   - Stint timer
   - Predicted pit window

4. **Session Recording**
   - Save session data to database
   - Export as CSV/JSON
   - Post-race analysis
   - Share sessions via URL

5. **Multi-Car Dashboard**
   - Show all cars in session
   - Compare with competitors
   - Gap analysis
   - Pit strategy comparison

---

### Phase 4: Interactive Controls

1. **Pit Strategy Controls**
   - Set fuel amount (slider)
   - Select tire compound
   - Adjust tire pressures (+/- buttons)
   - Change wing angles
   - Queue pit stop

2. **Driver Management**
   - Set next driver name
   - Driver change countdown
   - Stint history
   - Driver notes

3. **Team Communication**
   - Chat/notes section
   - Strategy notes
   - Issue reporting
   - Voice integration (future)

4. **Authorization**
   - Team member authentication
   - Role-based permissions (viewer vs. engineer)
   - Confirmation dialogs for changes
   - Audit log of changes

---

## Questions to Resolve Before Starting

1. **Deployment Preference**
   - [ ] Local network only
   - [ ] Cloud-hosted
   - [ ] Hybrid (local + cloud)

2. **Update Frequency**
   - [ ] 1Hz (low bandwidth)
   - [ ] 2Hz (recommended)
   - [ ] 5Hz (high bandwidth)
   - [ ] 10Hz (overkill for dashboard)

3. **Data Retention**
   - [ ] In-memory only (session ends when monitor stops)
   - [ ] Database storage (PostgreSQL, MongoDB)
   - [ ] File-based logging (CSV/JSON)

4. **Mobile Support**
   - [ ] Primary viewing device: Desktop
   - [ ] Primary viewing device: Tablet
   - [ ] Primary viewing device: Phone
   - [ ] All of the above

5. **Multi-Session Support**
   - [ ] Single session at a time
   - [ ] Multiple sessions simultaneously (different teams)
   - [ ] Session history/archive

6. **Security**
   - [ ] Secret URLs only (no auth)
   - [ ] Password-protected sessions
   - [ ] Team member authentication
   - [ ] Session expiry (auto-delete after N hours)

---

## Development Workflow

### Getting Started

```bash
# 1. Fork writer → monitor
cd ~/projects
git clone git@github.com:1Lap/writer.git monitor
cd monitor

# Clean up
git rm -r src/csv_formatter.py src/file_manager.py src/tray_ui.py
git rm -r src/update_*.py installer/ build.bat
git commit -m "Remove unneeded components"

# Add new code
# (implement dashboard_publisher.py, monitor.py, etc.)
git add .
git commit -m "Add dashboard publisher"

# Push to new repo
git remote set-url origin git@github.com:1Lap/monitor.git
git push -u origin main

# 2. Create server repo
mkdir ~/projects/server && cd ~/projects/server
git init
# (implement Flask app)
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:1Lap/server.git
git push -u origin main
```

---

### Development Loop

**Terminal 1: Server**
```bash
cd ~/projects/server
python run.py
# Watch for incoming connections
```

**Terminal 2: Monitor (on Windows with LMU)**
```bash
cd ~/projects/monitor
python monitor.py
# Should print dashboard URL
```

**Terminal 3: Browser**
```bash
# Open dashboard URL from monitor output
open http://localhost:5000/dashboard/<session-id>
```

---

## Contact & Support

- **GitHub Issues:** [1Lap/monitor/issues](https://github.com/1Lap/monitor/issues)
- **GitHub Issues:** [1Lap/server/issues](https://github.com/1Lap/server/issues)
- **Project Plan:** This file (RACE_DASHBOARD_PLAN.md)

---

## Changelog

### 2025-11-22 - Initial Plan
- Project architecture defined
- Repository structure designed
- Implementation phases outlined
- API contracts specified
- Ready for development

---

## References

### LMU Data Sources
- [rF2SharedMemoryMapPlugin](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin) - Shared memory API
- [pyRfactor2SharedMemory](https://github.com/TonyWhitley/pyRfactor2SharedMemory) - Python library
- [rF2 Shared Memory Tools](https://www.overtake.gg/downloads/rf2-shared-memory-tools-for-developers.19334/) - Developer tools

### Similar Projects
- [SEAT (Strategy Engineer Assistance Tool)](https://keberz.com/seat) - Pit stop analysis
- [Racelab Garage](https://garage.racelab.app/docs/first-steps/lmu/) - Setup management

### Technologies
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket support
- [Socket.IO](https://socket.io/) - Real-time communication

---

**End of Plan**
