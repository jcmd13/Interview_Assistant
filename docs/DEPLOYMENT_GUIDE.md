# Interview Assistant - Deployment Guide

**Status:** Phase 6 Complete - Ready for Production
**Last Updated:** November 8, 2025

---

## Table of Contents

1. [Quick Deploy](#quick-deploy)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Upgrade Guide](#upgrade-guide)

---

## Quick Deploy

**For existing users:** 5-minute setup

```bash
# 1. Start Ollama (separate terminal)
ollama serve

# 2. Pull required model (first time only)
ollama pull gpt-oss:120b-cloud

# 3. Start the plugin-aware server
python server_v4_pluggable.py

# 4. In another terminal, start the menu bar app (macOS)
pip install rumps  # First time only
python -m src.desktop.menu_bar_app

# 5. Open admin panel in browser
open http://127.0.0.1:8123/admin.html

# 6. Open main UI in another tab
open http://127.0.0.1:8123/
```

**For new users:** 15-minute complete setup

Follow [Installation Steps](#installation-steps) below.

---

## System Requirements

### Minimum Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 8GB | 16GB+ |
| **Disk** | 10GB free | 20GB+ |
| **OS** | macOS 10.12+ / Ubuntu 18.04+ | macOS 12+ / Ubuntu 20.04+ |

### Required Software

- Python 3.8+
- Ollama 0.1.0+ (for LLM)
- FFmpeg 4.0+ (for audio capture)
- pip (Python package manager)

### Required Python Packages

See `requirements.txt` for full list. Key packages:
- `faster-whisper` - Speech recognition
- `websockets` - Real-time communication
- `torch` - Neural network computation
- `ollama` - LLM interface

### Optional (for macOS Menu Bar)

- `rumps` - Native menu bar integration

### Optional (for admin features)

- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support

---

## Installation Steps

### Step 1: Install Prerequisites

**macOS:**
```bash
# Install FFmpeg
brew install ffmpeg

# Install Python 3.9+ if needed
brew install python@3.11

# Install Ollama
brew install ollama

# (Optional) Install websocat for debugging
brew install websocat
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y ffmpeg python3.9 python3-pip

# Install Ollama
curl https://ollama.ai/install.sh | sh

# (Optional) Install websocat
cargo install websocat  # requires Rust
```

**Windows (WSL2 Recommended):**
```bash
# Use Windows Subsystem for Linux for best experience
wsl --install

# Then follow Ubuntu/Debian steps above
# Or use native installers:
# - FFmpeg: https://ffmpeg.org/download.html
# - Python: https://www.python.org/downloads/
# - Ollama: https://ollama.ai
```

### Step 2: Clone or Download Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/Interview_Assistant.git
cd Interview_Assistant

# Or if you have a ZIP file
unzip Interview_Assistant.zip
cd Interview_Assistant
```

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate   # Windows

# Verify activation (you should see (venv) in prompt)
python --version  # Should be 3.8+
```

#### Reset Virtual Environment (Start Over)

If you need to remove the venv and start completely fresh:

**IMPORTANT: Make sure you are in the project directory!**

```bash
# Step 1: Navigate to project directory
cd /path/to/Interview_Assistant

# Step 2: If venv is ACTIVE (you see (venv) in prompt), deactivate it
# ONLY type this if your prompt shows (venv):
deactivate

# Step 3: Remove the entire venv directory
# macOS/Linux:
rm -rf venv

# Windows (PowerShell):
Remove-Item -Recurse -Force venv

# Windows (Command Prompt):
rmdir /s /q venv

# Step 4: Verify it's gone
ls -la | grep venv  # macOS/Linux - should return nothing
dir | findstr venv  # Windows - should return nothing

# Step 5: Create a FRESH venv from scratch
python3 -m venv venv

# Step 6: ACTIVATE the new venv (choose your platform)
# macOS/Linux - type exactly this:
source venv/bin/activate

# Windows PowerShell - type exactly this:
.\venv\Scripts\Activate.ps1

# Windows Command Prompt - type exactly this:
venv\Scripts\activate.bat

# You should now see (venv) at the start of your terminal prompt

# Step 7: Continue with Step 4 of installation
pip install --upgrade pip
pip install -r requirements.txt
```

**How to tell if activation worked:**
Your terminal prompt should show `(venv)` at the beginning.

**Troubleshooting:**
- If you get "command not found", make sure you're in the project directory
- Copy-paste the activation command exactly (don't type it manually)
- On macOS/Linux, use `source` not `bash` or `.`

### Step 4: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# (Optional) For GPU acceleration, replace PyTorch
# For CUDA 11.8:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# (Optional) For admin features
pip install pytest pytest-asyncio

# (Optional) For macOS menu bar
pip install rumps
```

### Step 5: Verify Installation

```bash
# Test Python packages
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import faster_whisper; print('Whisper: OK')"
python -c "import ollama; print('Ollama client: OK')"

# Test FFmpeg
ffmpeg -version | head -1

# Test Ollama connectivity
ollama list  # Should show installed models, or "ERROR" if Ollama not running
```

### Step 6: Start Ollama Service

Ollama must be running separately before the server starts.

```bash
# Start Ollama server (separate terminal)
ollama serve

# In another terminal, verify it's working
ollama list

# Pull the required LLM model (this may take 5-10 minutes first time)
ollama pull gpt-oss:120b-cloud

# Verify it's installed
ollama list | grep gpt-oss
```

---

## Configuration

### Server Configuration

Edit `server_v4_pluggable.py` at the top of the file (lines 1-50):

```python
# Core Configuration
WHISPER_MODEL = "base"              # tiny, base, small, medium, large
OLLAMA_MODEL = "gpt-oss:120b-cloud" # LLM model to use
OLLAMA_HOST = "http://localhost:11434"  # Ollama server address

# Audio Processing
WINDOW_SECONDS = 6.0    # Audio window size for transcription
HOP_SECONDS = 0.8       # Time between transcription attempts
ENERGY_GATE = 0.02      # Skip silent frames (0.0-1.0)

# LLM Settings
MAX_OUTPUT_TOKENS = 400      # Answer max length
MIN_GAP_BETWEEN_ANSWERS = 2  # Rate limiting (seconds)

# Server
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8123

# Logging
DEBUG = False  # Set to True for verbose logging
```

### Audio Client Configuration

Edit `stable_audio_client_multi_os.py` at the top:

```python
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8123
SAMPLE_RATE = 16000    # Hz
AUDIO_FORMAT = "s16"   # 16-bit signed
CHANNELS = 1           # Mono
```

### Admin Settings (Runtime Configuration)

After starting the server, use the Admin Panel to change settings without restart:

1. Open `http://127.0.0.1:8123/admin.html`
2. Go to Settings tab
3. Change any setting
4. Click Save

Changes take effect immediately without restart.

---

## Running the System

### Standard Startup (3 Terminals)

**Terminal 1: Start Ollama**
```bash
ollama serve
# Keep this running - it's required for LLM to work
```

**Terminal 2: Start Server**
```bash
source venv/bin/activate  # Activate Python environment
python server_v4_pluggable.py

# Server output:
# ✓ Plugin system initialized
# ✓ WebSocket listening on ws://127.0.0.1:8123
# Ready for connections
```

**Terminal 3: Start Audio Client**
```bash
source venv/bin/activate
python stable_audio_client_multi_os.py --device "YOUR_DEVICE_NAME"

# To list devices:
python stable_audio_client_multi_os.py --list-devices
```

**Browser 1: Open Admin Panel**
```
http://127.0.0.1:8123/admin.html
```

**Browser 2: Open Main UI**
```
http://127.0.0.1:8123/
```

### macOS Menu Bar Startup (Optional)

Replace Terminal 3 above with:

```bash
source venv/bin/activate
python -m src.desktop.menu_bar_app

# Menu bar icon appears (🎙️)
# Click to start/stop server and open admin panel
```

### One-Command Startup (Experimental)

```bash
# Use the launch script (if available)
bash launch.sh

# This automatically starts:
# 1. Ollama (background)
# 2. Server (background)
# 3. Audio client (background)
# 4. Opens browser windows
```

---

## Monitoring & Maintenance

### Check System Health

```bash
# Real-time server logs
tail -f logs/server.log

# Check memory usage
ps aux | grep server_v4_pluggable | grep -v grep

# List running processes
lsof -i :8123  # Shows what's using port 8123
```

### Performance Monitoring

```bash
# Monitor latency in real-time
while true; do
  python -c "
import asyncio, json, websockets, time
async def test():
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        start = time.time()
        await ws.send(json.dumps({'cmd': 'get_server_status'}))
        await ws.recv()
        print(f'Latency: {(time.time()-start)*1000:.1f}ms')
asyncio.run(test())
  "
  sleep 5
done
```

### Structured Logs

Server outputs JSON-structured logs with timing:

```json
{
  "timestamp": "2025-11-08T10:30:45.123Z",
  "level": "INFO",
  "component": "server.v4",
  "message": "transcription_result",
  "metadata": {
    "text": "What is the latency?",
    "duration_ms": 340,
    "word_count": 4
  }
}
```

### Memory Management

For long-running sessions (1+ hours):

```bash
# Monitor memory usage
watch -n 5 'ps aux | grep server_v4_pluggable'

# If memory grows unbounded:
# 1. Check debug logs for leaks
# 2. Restart server (graceful shutdown)
# 3. Check for audio buffer overflow
```

### Graceful Shutdown

```bash
# Method 1: Ctrl+C in server terminal
# Server will:
# 1. Reject new connections
# 2. Close existing connections gracefully
# 3. Flush logs
# 4. Exit cleanly

# Method 2: Send SIGTERM signal
kill -TERM <server_pid>

# Method 3: Menu bar app
# Click menu bar icon → "Stop Server"
```

---

## Troubleshooting

### Issue: "Ollama not accessible"

**Symptoms:** Server fails to start, error about Ollama

**Solution:**
```bash
# Make sure Ollama is running in separate terminal
ollama serve

# Check connectivity
curl http://localhost:11434/api/version

# If that fails, restart Ollama
brew services restart ollama  # macOS
# or
systemctl restart ollama      # Linux
```

### Issue: "Model not found"

**Symptoms:** Server starts but LLM requests fail

**Solution:**
```bash
# List installed models
ollama list

# Pull the model
ollama pull gpt-oss:120b-cloud

# Or use a smaller model that's faster to install
ollama pull mistral
```

### Issue: "Port 8123 already in use"

**Symptoms:** Error "Address already in use"

**Solution:**
```bash
# Find what's using port 8123
lsof -i :8123

# Kill the process
kill -9 <PID>

# Or use a different port (edit server_v4_pluggable.py)
SERVER_PORT = 8124  # Change this
```

### Issue: No audio input detected

**Symptoms:** Audio client can't find device

**Solution:**
```bash
# List available devices
python stable_audio_client_multi_os.py --list-devices

# Start with exact device name
python stable_audio_client_multi_os.py --device "Built-in Microphone"

# On macOS, try:
python stable_audio_client_multi_os.py --device ":0"

# Check FFmpeg audio devices
ffmpeg -f avfoundation -list_devices true -i ""  # macOS
ffmpeg -list_devices true -f dshow -i dummy       # Windows
arecord -l                                         # Linux
```

### Issue: High CPU usage

**Symptoms:** CPU stays at 80%+ constantly

**Solution:**
1. Check Whisper model size: larger models use more CPU
   ```bash
   # Use faster model
   WHISPER_MODEL = "tiny"  # Instead of "large"
   ```

2. Check transcription window:
   ```bash
   # Use shorter window
   WINDOW_SECONDS = 4.0  # Instead of 6.0
   ```

3. Monitor individual components:
   ```bash
   python server_v4_pluggable.py 2>&1 | grep "WARNING\|ERROR"
   ```

### Issue: Server crashes randomly

**Symptoms:** Server stops without error message

**Solution:**
```bash
# Run with debug logging
DEBUG=True python server_v4_pluggable.py 2>&1 | tee debug.log

# Check for out-of-memory errors
ps aux | grep server_v4 | head -1

# Check system resources
free -h     # Linux
top         # macOS/Linux
tasklist    # Windows
```

### Issue: WebSocket connection refused

**Symptoms:** Can't connect to admin panel

**Solution:**
1. Verify server is running:
   ```bash
   netstat -an | grep 8123  # macOS/Linux
   # Should show: tcp ... 127.0.0.1:8123 LISTEN
   ```

2. Check firewall:
   ```bash
   # macOS: System Preferences → Security & Privacy → Firewall
   # Linux: sudo ufw allow 8123
   # Windows: firewall settings for port 8123
   ```

3. Try direct connection:
   ```bash
   websocat ws://127.0.0.1:8123
   ```

---

## Upgrade Guide

### From v3 to v4 (Latest)

v4 uses the new plugin architecture. v3 is still available as a fallback.

```bash
# Step 1: Backup current configuration
cp src/server/settings.json src/server/settings.json.backup

# Step 2: Pull latest code
git pull origin main

# Step 3: Install new dependencies (if any)
pip install -r requirements.txt

# Step 4: Start new server (v3 is still available)
python server_v4_pluggable.py

# Step 5: Test all workflows
pytest tests/test_integration_phase6.py -v

# If issues, rollback to v3:
python optimized_stt_server_v3.py
```

### Minor Version Upgrade

```bash
# Get latest code
git pull origin main

# No server restart needed - just refresh browser
# Server will auto-reload changes on next connection
```

### Database Migration

No database migration needed - all data is stored locally in `logs/` and browser localStorage.

---

## Production Checklist

Before going live with users:

- [ ] Server starts without errors
- [ ] All plugins load successfully
- [ ] Transcription works with audio input
- [ ] LLM analysis and answer generation work
- [ ] Admin panel connects and controls settings
- [ ] Model swapping works without crashes
- [ ] No memory leaks after 1+ hour of operation
- [ ] Error messages are user-friendly
- [ ] Logs are structured and readable
- [ ] Performance meets latency targets (< 4s end-to-end)
- [ ] Documentation is current
- [ ] Team trained on operation and troubleshooting

---

## Support & Resources

### Logs & Debugging

- Server logs: `logs/server.log`
- Audio client logs: `logs/audio_client.log`
- Full debug output: `DEBUG=True python server_v4_pluggable.py`

### Documentation

- Architecture: `docs/ARCHITECTURE.md`
- Admin Guide: `ADMIN_GUIDE.md`
- Testing Guide: `docs/TESTING_GUIDE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md` (this document, troubleshooting section)

### Community

- GitHub Issues: [Report bugs here]
- Discussions: [Community forum]
- Discord: [Community chat]

---

**Deployment Status:** ✅ Ready for Production
**Last Verified:** November 8, 2025
**Next Review:** November 15, 2025
