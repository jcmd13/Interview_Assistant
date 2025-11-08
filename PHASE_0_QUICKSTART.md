# Phase 0 Quick Start Guide

Get Interview Assistant running in minutes with these simple steps.

## 1. Prerequisites Check

```bash
# Python 3.9+
python3 --version

# FFmpeg (for audio capture)
ffmpeg -version

# Ollama installed and running
ollama --version
```

## 2. Setup

```bash
# Clone/navigate to the project
cd /Users/john/Personal-Projects/Interview_Assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Start Services

**Terminal 1: Start Ollama Service**
```bash
# If not already running
ollama serve
```

**Terminal 2: Start WebSocket Server**
```bash
cd /Users/john/Personal-Projects/Interview_Assistant
python3 optimized_stt_server_v3.py
```

**Terminal 3: Start Audio Streaming**
```bash
cd /Users/john/Personal-Projects/Interview_Assistant
python3 stable_audio_client_multi_os.py --device "Built-in Microphone"
```

Or list devices first:
```bash
python3 stable_audio_client_multi_os.py --list-devices
```

## 4. Open the UI

```bash
# Open browser to the UI (no server needed!)
open index.html
```

Or navigate to `file:///Users/john/Personal-Projects/Interview_Assistant/index.html` in your browser.

---

## First Time Setup

### 1. Select Audio Device
- Press `~` to open Settings
- Choose your preferred microphone from "Audio Input Device"
- Close settings

### 2. Configure Models (Optional)
- Press `~` to open Settings
- Select Whisper model: `base` (balanced) or `tiny` (fast)
- Select LLM model: `gpt-oss:120b-cloud` (recommended)
- Close settings

### 3. Test Audio Levels
- Press `l` to view logs
- Check for audio capture messages
- Press `l` again to close logs
- You should see the VU meter in the transcript panel

---

## Common Workflows

### Interview Preparation
1. Open settings (`~`) and select quiet audio environment
2. Press `a` to manually ask practice questions
3. Review answers that appear in the right panel
4. Press `Shift+P` to pin important answers for review

### Live Interview Mode
1. Start the system before the interview begins
2. Keep browser window visible or minimized
3. System will auto-detect and answer questions
4. Press `Shift+P` to pin unexpected questions for later review
5. Use `p` to toggle auto-scroll if too fast

### Performance Monitoring
1. Press `m` to view latency dashboard
2. Monitor avg/p95 latency for your configuration
3. If latency > 4s, try switching to `tiny` Whisper model
4. Press `r` to reset metrics for a clean benchmark

### Reviewing Session
1. Press `l` for logs viewer
2. Search for any errors or warnings
3. Export logs to CSV for analysis
4. Press `Shift+D` to dismiss answered questions
5. Review remaining pinned answers (`Shift+P` showed pinned items earlier)

---

## Keyboard Shortcuts Quick Reference

### Most Important (Master These)
| Key | Action |
|-----|--------|
| `a` | Ask a question |
| `~` | Open settings |
| `Shift+P` | Pin current answer |
| `Shift+D` | Dismiss current answer |
| `Escape` | Close modals |

### Navigation
| Key | Action |
|-----|--------|
| `g` | Jump to top |
| `Shift+G` | Jump to end |
| `j` | Next question |
| `k` | Previous question |

### Views & Monitoring
| Key | Action |
|-----|--------|
| `l` | Logs viewer |
| `m` | Latency dashboard |
| `h` | Help (keyboard shortcuts) |

### Display Options
| Key | Action |
|-----|--------|
| `p` | Toggle auto-scroll |
| `f` | Toggle follow mode |
| `r` | Reset view |
| `s` | Save snapshot |

---

## Troubleshooting

### "Connection failed" or "Cannot connect to server"
```bash
# Check if server is running
curl http://localhost:8123

# If error, restart the server
python3 optimized_stt_server_v3.py
```

### "No audio" or "Audio device not found"
```bash
# List available devices
python3 stable_audio_client_multi_os.py --list-devices

# Start with the first device in list
python3 stable_audio_client_multi_os.py --device "Built-in Microphone"
```

### "Ollama model not found"
```bash
# Check installed models
ollama list

# Pull the required model
ollama pull gpt-oss:120b-cloud

# Or try a smaller model
ollama pull mistral
```

### High Latency (>4 seconds)
1. Switch to `tiny` Whisper model in Settings
2. Try `mistral` instead of `gpt-oss:120b-cloud` in Settings
3. Ensure no other heavy applications running
4. Check internet connection (some models require cloud)

### UI shows blank or not updating
1. Check browser console for errors (Cmd+Option+J on Mac)
2. Try refreshing the page
3. Check server logs for Python errors
4. Restart the WebSocket server

---

## Performance Expectations

### Latency
- Question asked → First partial answer: **0.5-1.5s**
- Full answer visible: **1.5-3.5s** (p95)
- Should never exceed: **4.0s**

### CPU Usage
- Idle: **<2%**
- Streaming: **25-35%**
- If higher, reduce Whisper model to `tiny`

### Memory
- Server startup: **~180MB**
- During streaming: **~300-400MB**
- Should not exceed: **500MB**

---

## Tips & Tricks

### Faster Response
- Use `tiny` Whisper model for speed
- Use `mistral` LLM instead of `gpt-oss:120b-cloud`
- Both are still very capable for interview questions

### Better Accuracy
- Use `small` or `base` Whisper model
- Use `gpt-oss:120b-cloud` for detailed answers
- Trade-off: accuracy vs latency

### Batch Questions
- Write down questions that appear too quickly
- Use `j`/`k` to navigate and review later
- Pin important ones with `Shift+P`

### Export Session
- Press `l` for logs viewer
- Click "Export" to save all logs as CSV
- All pinned answers auto-save to `~/.interview-assistant/answers.json`

### Check Settings Anytime
- Press `~` to open settings
- No need to restart server for changes
- Models load on-demand

---

## File Locations

- **Settings & Answers**: `~/.interview-assistant/answers.json`
- **Logs**: Terminal output (also visible in `l` panel)
- **Configuration**: Currently hardcoded in `optimized_stt_server_v3.py`
- **UI**: `index.html` (single standalone file)

---

## Getting Help

1. **Keyboard Shortcuts**: Press `h` in the app
2. **Logs**: Press `l` to see real-time system activity
3. **Status**: Check header for connection/audio status
4. **Documentation**: See `PHASE_0_COMPLETION.md` for detailed info

---

## Next Steps

Once Phase 0 is working:

1. **Practice Sessions**: Run several mock interviews to test latency
2. **Model Experimentation**: Try different Whisper/Ollama models
3. **Settings Optimization**: Find your speed/accuracy sweet spot
4. **Answer Review**: Use pin/dismiss to curate learning materials

---

## Ready to Go!

You should now have Interview Assistant running and ready for interview prep.

**Key Reminders:**
- Server must be running for UI to work
- Audio client must be started separately
- Browser can reload without restarting server
- Settings persist via WebSocket updates
- Answers auto-save to disk

Good luck with your interviews! 🚀

---

**For detailed technical info**, see `PHASE_0_COMPLETION.md`
**For development setup**, see `CLAUDE.md`
**For long-term roadmap**, see `ROADMAP.md`
