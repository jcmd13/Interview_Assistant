"""
Interview Assistant - Native macOS Menu Bar App

A lightweight menu bar application that:
- Displays server status in the macOS menu bar
- Provides quick access to start/stop/restart server
- Shows current models in use
- Links to main UI and admin panel
- Monitors server health with visual indicators

Requirements:
    pip install rumps

Usage:
    python -m src.desktop.menu_bar_app
"""

import asyncio
import json
import os
import subprocess
import threading
import time
from typing import Optional, Dict, Any

try:
    import rumps
except ImportError:
    print("ERROR: rumps not installed. Install with: pip install rumps")
    exit(1)

import websockets

from src.core.logger import get_logger

logger = get_logger("menu_bar_app")

# Configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8123
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}"
ADMIN_UI_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/admin.html"
MAIN_UI_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/"

# Process management
server_process: Optional[subprocess.Popen] = None
server_process_lock = threading.Lock()


class InterviewAssistantApp(rumps.App):
    """Menu bar application for Interview Assistant"""

    def __init__(self):
        super().__init__("Interview Assistant")
        self.icon = "🎙️"
        self.menu_update_interval = 3  # Update status every 3 seconds

        # State
        self.server_running = False
        self.server_status: Dict[str, Any] = {}
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

        # Build menu
        self.menu = [
            rumps.MenuItem("Server Status: Checking...", callback=None),
            rumps.separator,
            rumps.MenuItem("🟢 Start Server", callback=self.start_server),
            rumps.MenuItem("🛑 Stop Server", callback=self.stop_server),
            rumps.MenuItem("🔄 Restart Server", callback=self.restart_server),
            rumps.separator,
            rumps.MenuItem(
                "🌐 Open Main UI",
                callback=lambda _: self.open_url(MAIN_UI_URL)
            ),
            rumps.MenuItem(
                "⚙️ Open Admin Panel",
                callback=lambda _: self.open_url(ADMIN_UI_URL)
            ),
            rumps.separator,
            rumps.MenuItem("Quick Settings", [
                rumps.MenuItem("Whisper Model ▶", [
                    rumps.MenuItem("Tiny (Fast)", callback=self.set_whisper_model("tiny")),
                    rumps.MenuItem("Base", callback=self.set_whisper_model("base")),
                    rumps.MenuItem("Small", callback=self.set_whisper_model("small")),
                    rumps.MenuItem("Medium", callback=self.set_whisper_model("medium")),
                    rumps.MenuItem("Large (Accurate)", callback=self.set_whisper_model("large")),
                ]),
                rumps.MenuItem("LLM Model ▶", [
                    rumps.MenuItem("GPT-OSS 120B", callback=self.set_llm_model("gpt-oss:120b-cloud")),
                    rumps.MenuItem("Mistral", callback=self.set_llm_model("mistral")),
                    rumps.MenuItem("Neural Chat", callback=self.set_llm_model("neural-chat")),
                    rumps.MenuItem("OpenHermes 2.5", callback=self.set_llm_model("openhermes2.5-mistral")),
                ]),
            ]),
            rumps.separator,
            rumps.MenuItem("Preferences...", callback=self.show_preferences),
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

        # Start status update thread
        self.status_thread = threading.Thread(target=self.status_update_loop, daemon=True)
        self.status_thread.start()

        # Auto-start server if configured
        self.check_and_start_server()

    def status_update_loop(self):
        """Periodically update server status"""
        while True:
            try:
                self.update_server_status()
                time.sleep(self.menu_update_interval)
            except Exception as e:
                logger.error("status_update_error", error=str(e))
                time.sleep(self.menu_update_interval)

    def update_server_status(self):
        """Check server status and update menu"""
        try:
            # Try to connect and get status
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            status = loop.run_until_complete(self._get_server_status())
            loop.close()

            if status:
                self.server_running = True
                self.server_status = status
                self.update_menu_title(status)
            else:
                self.server_running = False
                self.update_menu_title(None)

        except Exception as e:
            self.server_running = False
            logger.warning("could_not_reach_server", error=str(e))

    async def _get_server_status(self) -> Optional[Dict[str, Any]]:
        """Get server status via WebSocket"""
        try:
            async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
                await ws.send(json.dumps({"cmd": "get_server_status"}))
                response = json.loads(await ws.recv())
                return response
        except Exception:
            return None

    def update_menu_title(self, status: Optional[Dict[str, Any]]):
        """Update menu bar title with status"""
        if status:
            # Green indicator for running
            title = f"Interview Assistant 🟢"
            status_text = "Server Status: 🟢 Running"
        else:
            # Red indicator for stopped
            title = f"Interview Assistant 🔴"
            status_text = "Server Status: 🔴 Stopped"

        self.title = title
        if self.menu and len(self.menu) > 0:
            self.menu[0].title = status_text

    def check_and_start_server(self):
        """Check if server is running, start if not"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            status = loop.run_until_complete(self._get_server_status())
            loop.close()

            if not status:
                # Server not running, offer to start
                response = rumps.alert(
                    "Interview Assistant server is not running.",
                    "Would you like to start it now?",
                    ok="Start Server"
                )
                if response:
                    self.start_server(None)
        except Exception as e:
            logger.error("startup_check_failed", error=str(e))

    def start_server(self, sender):
        """Start the server process"""
        global server_process

        with server_process_lock:
            if server_process and server_process.poll() is None:
                rumps.alert("Server is already running")
                return

            try:
                # Find server script
                server_script = "server_v4_pluggable.py"
                if not os.path.exists(server_script):
                    rumps.alert(
                        "Error",
                        f"Could not find {server_script}. Make sure it exists in the project root."
                    )
                    return

                logger.info("starting_server")

                # Start server process
                server_process = subprocess.Popen(
                    ["python", server_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Give server time to start
                time.sleep(2)

                # Check if it started successfully
                if server_process.poll() is None:
                    rumps.alert("✅ Server started successfully!")
                    self.server_running = True
                    logger.info("server_started", pid=server_process.pid)
                else:
                    rumps.alert("❌ Failed to start server. Check logs.")
                    logger.error("server_start_failed")

            except Exception as e:
                logger.error("start_server_error", error=str(e))
                rumps.alert("Error", f"Failed to start server: {str(e)}")

    def stop_server(self, sender):
        """Stop the server process"""
        global server_process

        with server_process_lock:
            if not server_process or server_process.poll() is not None:
                rumps.alert("Server is not running")
                return

            try:
                logger.info("stopping_server", pid=server_process.pid)

                # Terminate gracefully
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    server_process.kill()
                    server_process.wait()

                rumps.alert("✅ Server stopped")
                self.server_running = False
                logger.info("server_stopped")

            except Exception as e:
                logger.error("stop_server_error", error=str(e))
                rumps.alert("Error", f"Failed to stop server: {str(e)}")

    def restart_server(self, sender):
        """Restart the server"""
        self.stop_server(sender)
        time.sleep(1)
        self.start_server(sender)

    def set_whisper_model(self, model: str):
        """Return callback for setting Whisper model"""
        def callback(sender):
            self.send_command({"cmd": "swap_whisper_model", "model": model})
            rumps.alert(f"✅ Whisper model changed to: {model}")
        return callback

    def set_llm_model(self, model: str):
        """Return callback for setting LLM model"""
        def callback(sender):
            self.send_command({"cmd": "swap_llm_model", "model": model})
            rumps.alert(f"✅ LLM model changed to: {model}")
        return callback

    def send_command(self, cmd: Dict[str, Any]):
        """Send command to server"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_command_async(cmd))
            loop.close()
        except Exception as e:
            logger.error("send_command_error", error=str(e))
            rumps.alert("Error", f"Failed to send command: {str(e)}")

    async def _send_command_async(self, cmd: Dict[str, Any]):
        """Send command to server (async)"""
        try:
            async with websockets.connect(SERVER_URL, ping_interval=None) as ws:
                await ws.send(json.dumps(cmd))
                response = json.loads(await ws.recv())
                if response.get("type") == "error":
                    raise Exception(response.get("error", "Unknown error"))
        except Exception as e:
            raise

    def open_url(self, url: str):
        """Open URL in default browser"""
        def callback(sender):
            try:
                subprocess.Popen(["open", url])
                logger.info("opened_url", url=url)
            except Exception as e:
                logger.error("open_url_error", error=str(e))
                rumps.alert("Error", f"Failed to open URL: {str(e)}")
        return callback

    def show_preferences(self, sender):
        """Show preferences dialog"""
        rumps.alert(
            "Interview Assistant Preferences",
            f"""
Server: {SERVER_HOST}:{SERVER_PORT}
Admin Panel: {ADMIN_UI_URL}
Main UI: {MAIN_UI_URL}

To configure advanced settings, use the admin panel.
            """
        )

    def quit_app(self, sender):
        """Quit application"""
        global server_process

        # Ask if user wants to stop server
        response = rumps.alert(
            "Stop server before quitting?",
            "Would you like to stop the Interview Assistant server?",
            ok="Stop Server",
            cancel="Just Quit"
        )

        if response:
            self.stop_server(None)

        logger.info("app_quit")
        rumps.quit_app()


def main():
    """Main entry point"""
    logger.info("menu_bar_app_starting")
    app = InterviewAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
