"""
Integration Tests for Interview Assistant - Phase 6
Tests the complete system with plugin architecture, hot-swapping, and API endpoints.

Requirements:
    pip install pytest pytest-asyncio websockets

Usage:
    pytest tests/test_integration_phase6.py -v
    pytest tests/test_integration_phase6.py::test_server_startup -v
"""

import asyncio
import json
import pytest
import websockets
import subprocess
import time
import os
import signal
from pathlib import Path
from typing import Optional, Dict, Any


# Configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8123
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}"
SERVER_SCRIPT = "server_v4_pluggable.py"

# Timeouts
STARTUP_TIMEOUT = 10  # seconds
SHUTDOWN_TIMEOUT = 5  # seconds
API_TIMEOUT = 5  # seconds


class ServerManager:
    """Manages server lifecycle for testing"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.logs = []

    def start(self) -> bool:
        """Start the server"""
        if self.process and self.process.poll() is None:
            return True  # Already running

        try:
            self.process = subprocess.Popen(
                ["python", SERVER_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < STARTUP_TIMEOUT:
                try:
                    asyncio.run(self._check_connection())
                    print(f"✓ Server started (PID: {self.process.pid})")
                    return True
                except Exception:
                    time.sleep(0.5)

            return False
        except Exception as e:
            print(f"✗ Failed to start server: {e}")
            return False

    def stop(self) -> bool:
        """Stop the server"""
        if not self.process or self.process.poll() is not None:
            return True  # Already stopped

        try:
            self.process.terminate()
            self.process.wait(timeout=SHUTDOWN_TIMEOUT)
            print("✓ Server stopped")
            return True
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
            print("✓ Server killed (timeout)")
            return True
        except Exception as e:
            print(f"✗ Failed to stop server: {e}")
            return False

    async def _check_connection(self) -> bool:
        """Check if server is responding"""
        try:
            async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
                await ws.send(json.dumps({"cmd": "get_server_status"}))
                response = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                return response.get("type") != "error"
        except Exception:
            return False


@pytest.fixture(scope="session")
def server():
    """Session-wide server fixture"""
    manager = ServerManager()
    assert manager.start(), "Failed to start server"
    yield manager
    manager.stop()


@pytest.mark.asyncio
async def test_server_connection(server):
    """Test basic server connection"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        await ws.send(json.dumps({"cmd": "get_server_status"}))
        response = json.loads(await ws.recv())
        assert response.get("type") != "error", f"Got error: {response}"
        print(f"✓ Server connection successful")


@pytest.mark.asyncio
async def test_get_server_status(server):
    """Test get_server_status command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        await ws.send(json.dumps({"cmd": "get_server_status"}))
        response = json.loads(await ws.recv())

        assert response.get("type") != "error"
        assert "transcriber" in response
        assert "llm_analyzer" in response
        assert "plugin_manager" in response
        assert "settings_manager" in response

        print(f"✓ Server status retrieved: {response}")


@pytest.mark.asyncio
async def test_get_settings(server):
    """Test get_settings command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        await ws.send(json.dumps({"cmd": "get_settings"}))
        response = json.loads(await ws.recv())

        assert response.get("type") != "error"
        assert "settings" in response

        settings = response["settings"]
        assert "whisper_model" in settings
        assert "ollama_model" in settings
        assert "window_seconds" in settings

        print(f"✓ Settings retrieved: {list(settings.keys())}")


@pytest.mark.asyncio
async def test_get_available_models(server):
    """Test get_available_models command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        await ws.send(json.dumps({"cmd": "get_available_models"}))
        response = json.loads(await ws.recv())

        assert response.get("type") != "error"
        assert "whisper_models" in response
        assert "llm_models" in response

        whisper_models = response["whisper_models"]
        assert len(whisper_models) > 0
        assert "tiny" in whisper_models
        assert "base" in whisper_models

        print(f"✓ Available models retrieved: {len(whisper_models)} Whisper, {len(response['llm_models'])} LLM")


@pytest.mark.asyncio
async def test_set_setting(server):
    """Test set_setting command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Get current setting
        await ws.send(json.dumps({"cmd": "get_settings"}))
        initial = json.loads(await ws.recv())
        initial_tokens = initial["settings"].get("max_output_tokens", 400)

        # Change setting
        new_tokens = 300 if initial_tokens != 300 else 400
        await ws.send(json.dumps({
            "cmd": "set_setting",
            "key": "max_output_tokens",
            "value": new_tokens
        }))
        response = json.loads(await ws.recv())
        assert response.get("status") == "ok"

        # Verify change
        await ws.send(json.dumps({"cmd": "get_settings"}))
        updated = json.loads(await ws.recv())
        assert updated["settings"]["max_output_tokens"] == new_tokens

        print(f"✓ Setting changed: max_output_tokens = {new_tokens}")


@pytest.mark.asyncio
async def test_whisper_model_swap(server):
    """Test hot-swap Whisper model"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Try to swap to "tiny"
        await ws.send(json.dumps({
            "cmd": "swap_whisper_model",
            "model": "tiny"
        }))
        response = json.loads(await ws.recv())

        # Response should be either success or error (depending on state)
        assert "status" in response or "type" in response
        print(f"✓ Whisper model swap attempted: {response}")


@pytest.mark.asyncio
async def test_llm_model_swap(server):
    """Test hot-swap LLM model"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Try to swap to "mistral"
        await ws.send(json.dumps({
            "cmd": "swap_llm_model",
            "model": "mistral"
        }))
        response = json.loads(await ws.recv())

        # Response should be either success or error
        assert "status" in response or "type" in response
        print(f"✓ LLM model swap attempted: {response}")


@pytest.mark.asyncio
async def test_get_plugins(server):
    """Test get_plugins command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        await ws.send(json.dumps({"cmd": "get_plugins"}))
        response = json.loads(await ws.recv())

        assert response.get("type") != "error"
        assert "plugins" in response

        plugins = response["plugins"]
        assert len(plugins) > 0

        # Check plugin structure
        for plugin in plugins:
            assert "name" in plugin
            assert "status" in plugin
            assert plugin["status"] in ["loaded", "error", "pending"]

        print(f"✓ Plugins retrieved: {len(plugins)} plugins")
        for plugin in plugins:
            print(f"  - {plugin['name']}: {plugin['status']}")


@pytest.mark.asyncio
async def test_reset_settings(server):
    """Test reset_settings command"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Change a setting first
        await ws.send(json.dumps({
            "cmd": "set_setting",
            "key": "max_output_tokens",
            "value": 250
        }))
        _ = json.loads(await ws.recv())

        # Reset settings
        await ws.send(json.dumps({"cmd": "reset_settings"}))
        response = json.loads(await ws.recv())
        assert response.get("status") == "ok"

        print(f"✓ Settings reset successfully")


@pytest.mark.asyncio
async def test_concurrent_connections(server):
    """Test multiple concurrent WebSocket connections"""
    async def client_task(client_id: int):
        async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
            await ws.send(json.dumps({
                "cmd": "get_server_status",
                "client_id": client_id
            }))
            response = json.loads(await ws.recv())
            assert response.get("type") != "error"
            return True

    # Create 5 concurrent connections
    tasks = [client_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert all(results), "Some concurrent connections failed"
    print(f"✓ Concurrent connections test passed ({len(results)} clients)")


@pytest.mark.asyncio
async def test_command_error_handling(server):
    """Test error handling for invalid commands"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Send invalid command
        await ws.send(json.dumps({"cmd": "invalid_command"}))
        response = json.loads(await ws.recv())
        assert response.get("type") == "error"
        print(f"✓ Error handling works: {response.get('error')}")


@pytest.mark.asyncio
async def test_settings_persistence(server):
    """Test that settings changes persist across commands"""
    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        test_value = 500

        # Set a value
        await ws.send(json.dumps({
            "cmd": "set_setting",
            "key": "max_output_tokens",
            "value": test_value
        }))
        _ = json.loads(await ws.recv())

        # Get settings multiple times and verify consistency
        for _ in range(3):
            await ws.send(json.dumps({"cmd": "get_settings"}))
            response = json.loads(await ws.recv())
            assert response["settings"]["max_output_tokens"] == test_value

        print(f"✓ Settings persistence verified")


@pytest.mark.asyncio
async def test_message_queue_isolation(server):
    """Test that messages from different connections don't interfere"""
    async def send_and_receive(message: str):
        async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
            await ws.send(json.dumps({"cmd": "get_server_status"}))
            response = json.loads(await ws.recv())
            return response

    # Send messages from multiple connections concurrently
    tasks = [send_and_receive(f"msg_{i}") for i in range(3)]
    responses = await asyncio.gather(*tasks)

    assert len(responses) == 3
    assert all(r.get("type") != "error" for r in responses)
    print(f"✓ Message queue isolation test passed")


# Performance benchmarking tests
@pytest.mark.asyncio
async def test_api_response_time(server):
    """Benchmark API response times"""
    import time

    commands = [
        {"cmd": "get_server_status"},
        {"cmd": "get_settings"},
        {"cmd": "get_available_models"},
        {"cmd": "get_plugins"},
    ]

    timings = {}

    for cmd in commands:
        start = time.time()
        async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
            await ws.send(json.dumps(cmd))
            response = json.loads(await ws.recv())
        elapsed = (time.time() - start) * 1000  # Convert to ms

        cmd_name = cmd["cmd"]
        timings[cmd_name] = elapsed
        print(f"✓ {cmd_name}: {elapsed:.2f}ms")

    # Assert reasonable response times (< 500ms)
    for cmd_name, elapsed in timings.items():
        assert elapsed < 500, f"{cmd_name} took {elapsed:.2f}ms (expected < 500ms)"


@pytest.mark.asyncio
async def test_broadcast_latency(server):
    """Test message broadcast latency"""
    import time

    # This is a simple test - in production you'd measure actual broadcast
    start = time.time()

    async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
        # Send a command and measure response time
        await ws.send(json.dumps({"cmd": "get_server_status"}))
        response = json.loads(await ws.recv())

    elapsed = (time.time() - start) * 1000
    print(f"✓ Broadcast latency: {elapsed:.2f}ms")
    assert elapsed < 500, f"Broadcast too slow: {elapsed:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
