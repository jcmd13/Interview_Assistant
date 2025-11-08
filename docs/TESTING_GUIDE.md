# Interview Assistant - Testing & QA Guide

**Status:** Phase 6 Complete - Integration Tests & Deployment Ready
**Last Updated:** November 8, 2025

---

## Overview

This guide covers all testing approaches for the Interview Assistant system across:
- **Unit Tests**: Individual component validation
- **Integration Tests**: Full system workflows with plugin architecture
- **Performance Tests**: End-to-end latency measurement and benchmarking
- **Manual Testing**: Real-world interview scenarios
- **Load Testing**: Concurrent connection stability

---

## Quick Start Testing

### 1. Run All Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run full test suite
pytest tests/test_integration_phase6.py -v

# Run specific test
pytest tests/test_integration_phase6.py::test_server_connection -v

# Run with detailed output
pytest tests/test_integration_phase6.py -v -s
```

### 2. Run Performance Benchmarks

```bash
# Measure API response times
pytest tests/test_integration_phase6.py::test_api_response_time -v

# Measure broadcast latency
pytest tests/test_integration_phase6.py::test_broadcast_latency -v

# Run all performance tests
pytest tests/test_integration_phase6.py -k "performance or latency or timing" -v
```

### 3. Start Server for Manual Testing

```bash
# Terminal 1: Start server
python server_v4_pluggable.py

# Terminal 2: Verify server is ready
python -m pytest tests/test_integration_phase6.py::test_server_connection -v

# Terminal 3: Start audio client
python stable_audio_client_multi_os.py --device "YOUR_DEVICE_NAME"

# Browser: Open main UI
open http://127.0.0.1:8123/

# Browser: Open admin panel
open http://127.0.0.1:8123/admin.html
```

---

## Unit Tests

### Testing Individual Components

```bash
# Test plugin system
pytest tests/ -k "plugin" -v

# Test settings management
pytest tests/ -k "settings" -v

# Test model swapping
pytest tests/ -k "swap" -v
```

### Key Test Categories

| Component | Test File | Test Cases |
|-----------|-----------|-----------|
| **Plugin System** | `test_integration_phase6.py` | `test_get_plugins`, `test_reload_plugin` |
| **Settings Manager** | `test_integration_phase6.py` | `test_get_settings`, `test_set_setting`, `test_reset_settings` |
| **Model Swapping** | `test_integration_phase6.py` | `test_whisper_model_swap`, `test_llm_model_swap` |
| **API Endpoints** | `test_integration_phase6.py` | `test_get_*` commands, `test_command_error_handling` |
| **Server Status** | `test_integration_phase6.py` | `test_get_server_status` |

---

## Integration Tests

### Full Workflow Testing

The integration test suite covers complete system workflows:

#### Test 1: Server Connection & Setup
```python
# Verify server is reachable and responding
pytest tests/test_integration_phase6.py::test_server_connection -v
```

**What it tests:**
- WebSocket connection to server
- Basic handshake and response
- Server availability

**Expected output:**
```
✓ Server connection successful
```

#### Test 2: Plugin System Integration
```python
# Verify plugin loading and status
pytest tests/test_integration_phase6.py::test_get_plugins -v
```

**What it tests:**
- All plugins load successfully
- Plugin status reflects correct state
- Plugin metadata is accessible

**Expected output:**
```
✓ Plugins retrieved: 3 plugins
  - WhisperTranscriber: loaded
  - OllamaAnalyzer: loaded
  - SettingsManager: loaded
```

#### Test 3: Settings Management Workflow
```python
# Verify settings can be read, modified, and reset
pytest tests/test_integration_phase6.py::test_settings_persistence -v
```

**What it tests:**
- Settings are read correctly
- Settings can be changed
- Changes persist across multiple reads
- Settings don't interfere with other connections

#### Test 4: Model Hot-Swapping
```python
# Verify Whisper and LLM models can be swapped
pytest tests/test_integration_phase6.py::test_whisper_model_swap -v
pytest tests/test_integration_phase6.py::test_llm_model_swap -v
```

**What it tests:**
- Model swap requests are accepted
- Server doesn't crash during swap
- New model takes effect on next processing

#### Test 5: Concurrent Connections
```python
# Verify multiple simultaneous clients work correctly
pytest tests/test_integration_phase6.py::test_concurrent_connections -v
```

**What it tests:**
- Server handles 5+ concurrent WebSocket connections
- Each connection maintains isolation
- No message cross-contamination between clients

---

## Performance Tests

### Latency Measurement

All performance tests measure end-to-end latency from command sent to response received.

#### API Response Time Benchmark

```bash
pytest tests/test_integration_phase6.py::test_api_response_time -v
```

**Measures:**
- get_server_status: ~50-100ms
- get_settings: ~50-100ms
- get_available_models: ~50-100ms
- get_plugins: ~50-100ms

**Target:** All commands should respond < 500ms

#### Broadcast Latency

```bash
pytest tests/test_integration_phase6.py::test_broadcast_latency -v
```

**Measures:** Time from command sent to UI clients receiving broadcast

**Target:** < 500ms for real-time responsiveness

### Performance Targets (From CLAUDE.md)

| Stage | Target | Measurement |
|-------|--------|-------------|
| **Audio Capture** | < 500ms | Time from audio input to WebSocket transmission |
| **Transcription** | < 2s | Time from audio window to Whisper output |
| **Question Detection** | < 100ms | Time from transcribed text to LLM analysis |
| **LLM Response** | < 1.5s | Time from question detected to answer generated |
| **UI Display** | < 200ms | Time from server broadcast to rendered on screen |
| **TOTAL END-TO-END** | < 4s | From question asked to answer displayed |

### Custom Performance Testing

Create a custom benchmark test:

```python
# tests/test_custom_performance.py
import asyncio
import json
import time
import websockets

async def test_custom_latency():
    """Measure latency for your specific workflow"""
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        start = time.time()

        # Your custom command
        await ws.send(json.dumps({
            "cmd": "get_server_status"
        }))
        response = json.loads(await ws.recv())

        elapsed = (time.time() - start) * 1000
        print(f"Command latency: {elapsed:.2f}ms")
        assert elapsed < 500, f"Too slow: {elapsed:.2f}ms"

# Run with: pytest tests/test_custom_performance.py -v
```

---

## Manual Testing Workflows

### Scenario 1: Live Interview with Hot Model Swap

**Setup:**
1. Start server: `python server_v4_pluggable.py`
2. Open admin: `http://127.0.0.1:8123/admin.html`
3. Open main UI: `http://127.0.0.1:8123/`
4. Start audio: `python stable_audio_client_multi_os.py --device "Built-in Microphone"`

**Test Steps:**
1. Start speaking (ask a question or two)
2. Observe transcription in main UI
3. In admin panel, change Whisper model (tiny → base)
4. Continue speaking
5. Verify transcription quality changes on new model
6. Change LLM model (gpt-oss → mistral) in admin
7. Observe answer generation changes

**Success Criteria:**
- ✅ Models change without server restart
- ✅ No interruption in audio streaming
- ✅ New model takes effect on next processing window
- ✅ UI updates reflect model changes

### Scenario 2: Menu Bar App Control

**Setup:**
1. Install rumps: `pip install rumps`
2. Start menu bar app: `python -m src.desktop.menu_bar_app`

**Test Steps:**
1. Verify menu bar icon appears (🎙️)
2. Click menu bar icon
3. Verify server status indicator (🟢 or 🔴)
4. Click "Start Server" if not running
5. Open Admin Panel from menu
6. Verify admin panel loads and connects
7. Use menu to swap models
8. Verify changes take effect

**Success Criteria:**
- ✅ Menu bar app appears
- ✅ Server control works (start/stop/restart)
- ✅ Admin panel links work
- ✅ Quick model swapping works from menu

### Scenario 3: Settings Management

**Setup:** Server and admin panel running

**Test Steps:**
1. Open admin panel → Settings tab
2. Change audio settings (sample rate, window size)
3. Verify change succeeds (no error message)
4. Change LLM settings (max tokens, rate limit)
5. Verify changes persist on page refresh
6. Test reset button
7. Verify settings return to defaults

**Success Criteria:**
- ✅ Settings changes don't error
- ✅ Changes persist across page reload
- ✅ Reset returns to defaults
- ✅ No server restart required

### Scenario 4: Plugin Management

**Setup:** Server and admin panel running

**Test Steps:**
1. Open admin panel → Plugin Management
2. View list of plugins
3. Check status of each plugin (should be ✅ Loaded)
4. Click reload button for a plugin
5. Verify plugin reloads without error
6. Check status still shows "Loaded"

**Success Criteria:**
- ✅ All plugins show as loaded
- ✅ Reload completes without errors
- ✅ Server continues functioning after reload

### Scenario 5: Audio Streaming Stability

**Setup:**
1. Server running: `python server_v4_pluggable.py`
2. Audio client running: `python stable_audio_client_multi_os.py --device "YOUR_DEVICE"`
3. Admin panel open
4. Watch server logs: `tail -f logs/server.log`

**Test Steps:**
1. Speak for 2-3 minutes continuously
2. Observe continuous transcription in main UI
3. While speaking, change a model in admin panel
4. Continue speaking for another 2-3 minutes
5. Listen to audio client output for glitches
6. Check server logs for errors

**Success Criteria:**
- ✅ Transcription continuous without gaps
- ✅ No audio dropouts during model swap
- ✅ No server errors in logs
- ✅ Questions detected and answers generated

### Scenario 6: Concurrent Admin Connections

**Setup:**
1. Server and admin panel running
2. Two browser windows with admin panel open

**Test Steps:**
1. In window 1, change a setting (max_output_tokens to 300)
2. In window 2, change a different setting (window_seconds to 5)
3. In both windows, click refresh/get_settings
4. Verify both changes are present in both windows
5. In window 1, swap Whisper model to "tiny"
6. In window 2, verify model change is reflected

**Success Criteria:**
- ✅ Both windows maintain independent connections
- ✅ Settings from one window visible in other
- ✅ No connection conflicts

---

## Load Testing

### Test 1: Concurrent WebSocket Connections

```bash
# Verify server handles multiple simultaneous connections
pytest tests/test_integration_phase6.py::test_concurrent_connections -v

# This test creates 5 concurrent clients making requests
# Expected: All succeed within timeout
```

**Manual Load Test (10 concurrent clients):**

```python
# tests/test_load_10_clients.py
import asyncio
import json
import websockets

async def client(client_id):
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        for i in range(10):
            await ws.send(json.dumps({
                "cmd": "get_server_status",
                "client": client_id,
                "request": i
            }))
            response = json.loads(await ws.recv())
            assert response.get("type") != "error"
        return client_id

async def main():
    tasks = [client(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"✓ Load test passed: {len(results)} clients × 10 requests")

asyncio.run(main())
```

**Run:**
```bash
python tests/test_load_10_clients.py
```

### Test 2: Rapid Model Swapping

```bash
# Swap models 10 times in quick succession and verify stability
python -c "
import asyncio
import json
import websockets

async def rapid_swap():
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        models = ['tiny', 'base', 'small', 'tiny', 'base']
        for model in models:
            await ws.send(json.dumps({
                'cmd': 'swap_whisper_model',
                'model': model
            }))
            response = json.loads(await ws.recv())
            print(f'Swapped to {model}: {response.get(\"status\", \"?\")}')

asyncio.run(rapid_swap())
"
```

### Test 3: Long-Running Transcription

```bash
# Run server for extended period (1+ hour) with continuous audio
# Monitor for:
# - Memory leaks (should stay stable)
# - CPU usage (should stay < 10%)
# - Response latency (should not degrade)

# Watch metrics:
watch -n 5 'ps aux | grep server_v4_pluggable'

# Or use more detailed monitoring:
python -m src.core.monitor_latency
```

---

## Debugging & Troubleshooting

### Enable Debug Logging

```bash
# Run server with verbose output
DEBUG=True python server_v4_pluggable.py 2>&1 | tee logs/debug.log

# Filter for specific components
python server_v4_pluggable.py 2>&1 | grep "plugin\|swap\|settings"
```

### Check Server Status

```bash
# Test connection and get full status
python -c "
import asyncio
import json
import websockets

async def check_status():
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        await ws.send(json.dumps({'cmd': 'get_server_status'}))
        status = json.loads(await ws.recv())
        import json
        print(json.dumps(status, indent=2))

asyncio.run(check_status())
"
```

### View Server Logs

```bash
# Real-time server logs
tail -f logs/server.log

# Grep for errors
grep "error\|ERROR\|failed\|FAILED" logs/server.log

# Structured JSON logs with jq (install: brew install jq)
tail -f logs/server.log | jq '.message, .error'
```

### Test Individual Endpoints

```bash
# Use websocat for raw WebSocket testing
# Install: brew install websocat

websocat ws://127.0.0.1:8123

# Then type JSON commands:
{"cmd": "get_server_status"}
{"cmd": "get_settings"}
{"cmd": "swap_whisper_model", "model": "tiny"}
```

---

## Test Reports

### Generating Test Results

```bash
# Generate HTML test report
pytest tests/test_integration_phase6.py --html=report.html

# Generate JUnit XML (for CI/CD)
pytest tests/test_integration_phase6.py --junit-xml=results.xml

# Generate coverage report
pytest tests/test_integration_phase6.py --cov=src --cov-report=html
```

### Benchmark Results Format

Example output from performance test run:

```
=== Performance Test Results ===

API Response Times:
  get_server_status    : 47.3ms
  get_settings         : 52.1ms
  get_available_models : 48.9ms
  get_plugins          : 51.2ms

Average: 49.9ms
P95:     65.2ms
P99:     72.5ms
Max:     78.3ms

Status: ✅ PASS (all < 500ms)
```

---

## Pre-Release Checklist

Before deploying to users, verify:

- [ ] All integration tests passing: `pytest tests/test_integration_phase6.py -v`
- [ ] Performance tests meet targets: `pytest -k "performance" -v`
- [ ] Manual test scenarios 1-6 all pass
- [ ] Load test with 10+ concurrent clients succeeds
- [ ] Menu bar app starts and controls server correctly
- [ ] Admin panel loads without errors
- [ ] Model swapping works without crashes
- [ ] Settings changes persist correctly
- [ ] No memory leaks after 30+ minutes of operation
- [ ] All error cases handled gracefully (no stack traces)
- [ ] Documentation updated with latest changes
- [ ] Git commits created with test results
- [ ] Logs are structured and readable

---

## Continuous Integration (CI/CD)

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt pytest pytest-asyncio
      - run: pytest tests/test_integration_phase6.py -v
      - run: pytest tests/test_integration_phase6.py -k "performance" -v
```

---

## Support

For issues with testing:
1. Check server logs: `tail -f logs/server.log`
2. Enable debug mode: `DEBUG=True python server_v4_pluggable.py`
3. Run connection test: `pytest tests/test_integration_phase6.py::test_server_connection -v -s`
4. Check requirements are met: `pip list | grep pytest`

---

**Status:** Phase 6 - Testing Infrastructure Complete
**Next:** Deploy and monitor in production environment
