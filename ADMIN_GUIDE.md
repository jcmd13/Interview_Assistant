# Interview Assistant - Admin & Configuration Guide

**Last Updated:** November 8, 2025
**Status:** Phases 1-4 Complete - Plugin System + Hot-Swapping Ready

---

## Quick Start

### 1. Start the Plugin-Aware Server

```bash
# Terminal 1: Run the new modular server with plugin support
python server_v4_pluggable.py

# Server logs will show:
# ✓ Plugin system initialized
# ✓ Transcriber ready (Whisper)
# ✓ LLM analyzer ready (Ollama)
# ✓ WebSocket listening on ws://127.0.0.1:8123
```

### 2. Access Admin Panel (Browser)

```bash
# Open in your browser
http://127.0.0.1:8123/admin.html
```

### 3. Start Menu Bar App (macOS)

```bash
# Terminal 2: Install rumps first (if needed)
pip install rumps

# Run the menu bar app
python -m src.desktop.menu_bar_app

# You'll see 🎙️ icon appear in the macOS menu bar at top-right
```

### 4. Access Main UI (Browser)

```bash
# Open in your browser
http://127.0.0.1:8123/
```

---

## Features You Can Use Right Now

### ✅ Hot-Swap Models Without Restart

**Via Admin Panel (Easiest):**
1. Open http://127.0.0.1:8123/admin.html
2. Go to "🔄 Model Swapping" panel
3. Select new model from dropdown
4. Click "Swap" button
5. ⚡ Model changes instantly - no restart needed!

**Via Menu Bar App (Quick):**
1. Click 🎙️ icon in menu bar
2. Navigate to "Quick Settings" → "Whisper Model" or "LLM Model"
3. Select new model
4. ⚡ Model changes instantly!

**Via WebSocket (Manual):**
```bash
python -c "
import asyncio, json, websockets

async def swap_model():
    async with websockets.connect('ws://127.0.0.1:8123/') as ws:
        # Swap Whisper model
        await ws.send(json.dumps({
            'cmd': 'swap_whisper_model',
            'model': 'base'  # tiny, base, small, medium, large
        }))
        response = await ws.recv()
        print('Response:', response)

asyncio.run(swap_model())
"
```

### ✅ Manage Settings in Real-Time

**Audio Settings:**
- Sample Rate (Hz)
- Window Size (seconds)
- Hop Size (seconds)
- Energy Gate threshold

**LLM Settings:**
- Max Output Tokens (controls answer length)
- Minimum Gap Between Answers (rate limiting)

**Server Settings:**
- Host and Port (require restart)
- All settings persist across restarts

### ✅ Monitor Plugin Health

In Admin Panel → "🔌 Plugin Management":
- See all loaded plugins
- Check status (✅ Loaded or ❌ Error)
- View plugin versions
- Reload plugins on-demand

### ✅ View Server Status

Real-time indicators for:
- Transcriber status
- LLM Analyzer status
- Plugin Manager status
- Settings Manager status

---

## Architecture Overview

### What Changed

**Before:** Monolithic server with direct imports
```
optimized_stt_server_v3.py (1040 lines)
├─ Direct import of WhisperModel
├─ Direct import of ImprovedLLMAnalyzer
└─ No runtime configuration
```

**After:** Plugin-based modular server
```
server_v4_pluggable.py (431 lines) ← CLEAN & MODULAR
├─ PluginTranscriber (hot-swappable)
├─ PluginLLMAnalyzer (hot-swappable)
├─ PluginManager (lifecycle control)
└─ SettingsManager (runtime config)

Admin UI (admin.html) ← BROWSER-BASED CONTROL
├─ Model swapping
├─ Settings management
└─ Plugin monitoring

Menu Bar App (menu_bar_app.py) ← macOS NATIVE
├─ Server control
├─ Status indicator
└─ Quick settings
```

### The 4 Core Systems (All Pluggable)

| System | Plugin | Status | Hot-Swap |
|--------|--------|--------|----------|
| **Audio-to-Text** | WhisperTranscriber | ✅ Ready | ✅ Yes |
| **Question Detection** | OllamaAnalyzer | ✅ Ready | ✅ Indirect |
| **LLM Response** | OllamaLLM | ✅ Ready | ✅ Yes |
| **UI Rendering** | HTML/JS (static) | ⏳ Pending | ⏳ Phase 5 |

---

## Available Models

### Whisper Transcription Models

| Model | Speed | Accuracy | Memory | Use Case |
|-------|-------|----------|--------|----------|
| **Tiny** | ⚡ Fastest | Good | ~400MB | Live interviews, real-time |
| **Base** | ⚡ Fast | Better | ~700MB | Balanced choice |
| **Small** | 🔹 Medium | Good | ~900MB | Higher accuracy needed |
| **Medium** | 🐢 Slow | Excellent | ~1.4GB | Precision required |
| **Large** | 🐢 Slowest | Best | ~2.9GB | Archive/batch |

**Recommendation:** Start with "Base" or "Small" for interviews

### LLM Models

| Model | Speed | Size | Use Case |
|-------|-------|------|----------|
| **gpt-oss:120b-cloud** | Medium | 120B params | Default, recommended |
| **mistral** | Fast | 7B params | Quick responses, low resource |
| **neural-chat** | Fast | 7B params | Conversation focused |
| **openhermes2.5-mistral** | Medium | 7B params | Creative responses |

**Recommendation:** Start with "gpt-oss:120b-cloud" (already configured)

---

## Advanced Configuration

### Server Command Reference

All commands sent as JSON via WebSocket:

```python
# Get current settings
{"cmd": "get_settings"}

# Set a setting
{"cmd": "set_setting", "key": "max_output_tokens", "value": 500}

# Swap Whisper model
{"cmd": "swap_whisper_model", "model": "base"}

# Swap LLM model
{"cmd": "swap_llm_model", "model": "mistral"}

# List all plugins
{"cmd": "get_plugins"}

# Reload a plugin
{"cmd": "reload_plugin", "name": "whisper_transcriber"}

# Get server health
{"cmd": "get_server_status"}

# Reset server state
{"cmd": "reset"}
```

### Environment-Specific Configurations

**Development:**
```bash
DEBUG=True python server_v4_pluggable.py
# Structured JSON logging enabled
# Verbose output for debugging
```

**Production:**
```bash
DEBUG=False python server_v4_pluggable.py
# Clean log output
# Only important events logged
```

### Model Requires Restart?

**No Restart Needed (Hot-Swap Works):**
- ✅ Whisper model (tiny → base → large)
- ✅ LLM model (gpt-oss → mistral)
- ✅ Audio settings (sample rate, window size)
- ✅ LLM settings (output tokens, rate limits)

**Restart Required:**
- ⚠️ Server host/port changes
- ⚠️ Major configuration changes
- ⚠️ Plugin system reload

---

## Troubleshooting

### Problem: Admin Panel Won't Connect

**Symptoms:** "Disconnected from server" message in admin panel

**Solutions:**
1. Check server is running: `python server_v4_pluggable.py`
2. Check port 8123 is available
3. Check firewall allows 127.0.0.1:8123
4. Admin panel will auto-reconnect in 3 seconds

### Problem: Model Swap Fails

**Symptoms:** "Error processing swap_whisper_model"

**Solutions:**
1. Verify model is valid (tiny, base, small, medium, large)
2. Check server logs for error details
3. Try smaller model first (memory issue?)
4. Restart server if persistent

### Problem: Menu Bar App Won't Start

**Symptoms:** "ModuleNotFoundError: No module named 'rumps'"

**Solution:**
```bash
pip install rumps
python -m src.desktop.menu_bar_app
```

### Problem: Server Crashes on Startup

**Symptoms:** Server starts but crashes immediately

**Solutions:**
1. Check Ollama is running: `ollama serve` (in separate terminal)
2. Check Ollama model exists: `ollama list`
3. Check logs for specific error
4. Fall back to original server: `python optimized_stt_server_v3.py`

---

## Performance Tips

### For Fastest Response Time

1. **Use "Tiny" Whisper model** for real-time interviews
2. **Use "mistral" LLM** for faster response generation
3. **Set max_output_tokens to 200-300** instead of 400
4. **Use window_seconds of 3-4** instead of 6

**Expected latency with these settings: ~2-3 seconds end-to-end**

### For Highest Accuracy

1. **Use "Small" or "Medium" Whisper model** for better transcription
2. **Use "gpt-oss:120b-cloud" LLM** for quality responses
3. **Set max_output_tokens to 500-600** for detailed answers
4. **Use window_seconds of 6-8** for more context

**Expected latency with these settings: ~4-5 seconds end-to-end**

### For Lower Resource Usage

1. **Use "Tiny" Whisper model** (400MB memory)
2. **Use "mistral" LLM** (7B, lighter weight)
3. **Set lower window_seconds** (3 instead of 6)
4. **Monitor memory usage** in Activity Monitor

---

## Testing Workflow

### 1. Start Everything

```bash
# Terminal 1: Server
python server_v4_pluggable.py

# Terminal 2: Menu bar app (optional)
python -m src.desktop.menu_bar_app

# Browser 1: Admin panel
http://127.0.0.1:8123/admin.html

# Browser 2: Main UI
http://127.0.0.1:8123/
```

### 2. Run Audio Client

```bash
# Terminal 3: Audio streaming
python stable_audio_client_multi_os.py --device "YOUR_DEVICE_NAME"
```

### 3. Test Hot-Swapping

In Admin Panel:
1. Change Whisper model (tiny → base)
2. Listen for transcription change
3. Change LLM model (gpt-oss → mistral)
4. Listen for answer generation change
5. Adjust settings in real-time

### 4. Verify No Downtime

- Transcription continues while swapping models
- Audio streaming doesn't disconnect
- New model takes effect on next window

---

## Files Overview

### Core Server
- **`server_v4_pluggable.py`** - New modular server (431 lines)
- **`src/server/plugin_integration.py`** - Plugin wrappers
- **`src/server/settings_api_endpoints.py`** - Settings API

### Admin Tools
- **`admin.html`** - Web admin panel (905 lines)
- **`src/desktop/menu_bar_app.py`** - macOS menu bar app (350 lines)

### Original Server (Still Available)
- **`optimized_stt_server_v3.py`** - Original monolithic server (still works)
- Can run alongside v4 for comparison/testing

---

## Next Steps (Phase 5 & 6)

### Phase 5: Pluggable Card-Based UI
- Make `index.html` dynamically loadable
- Layout presets (Interview Stealth, Phone Call, etc.)
- Drag-and-drop card repositioning
- Settings panel card

### Phase 6: Integration Testing
- End-to-end test scenarios
- Performance benchmarking
- Load testing with multiple clients
- Documentation updates

---

## Support & Debugging

### Enable Structured Logging

Server logs output structured JSON with timing data:

```json
{
  "timestamp": "2025-11-08T10:30:45.123Z",
  "level": "INFO",
  "component": "server.v4",
  "message": "transcription_result",
  "metadata": {
    "text": "What is the latency?",
    "duration": 0.34,
    "word_count": 4
  }
}
```

### View Logs in Real-Time

```bash
# Run server with pipe to grep for specific component
python server_v4_pluggable.py 2>&1 | grep "transcription\|llm\|plugin"
```

### Debug WebSocket Commands

```bash
# Use websocat to send raw commands
# Install: brew install websocat (on macOS)

websocat ws://127.0.0.1:8123

# Then type JSON commands:
{"cmd": "get_server_status"}
```

---

## Questions?

Refer to:
- **Architecture details:** `docs/ARCHITECTURE.md`
- **Deployment guide:** `docs/DEPLOYMENT.md`
- **Testing guide:** `docs/TESTING.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

**Status:** ✅ Phases 1-4 Complete | ⏳ Phases 5-6 Pending
**Last Update:** November 8, 2025
