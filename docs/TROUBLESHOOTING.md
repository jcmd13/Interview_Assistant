# Troubleshooting Guide

**Last Updated**: November 8, 2025
**Status**: Comprehensive Guide

---

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Installation Issues](#installation-issues)
3. [Audio Problems](#audio-problems)
4. [Transcription Issues](#transcription-issues)
5. [Question Detection Problems](#question-detection-problems)
6. [Answer Generation Issues](#answer-generation-issues)
7. [UI/WebSocket Issues](#uiwebsocket-issues)
8. [Performance Problems](#performance-problems)
9. [System Issues](#system-issues)
10. [Getting Help](#getting-help)

---

## Quick Diagnosis

### System Health Check

Run this to diagnose your system:

```bash
#!/bin/bash
echo "=== Interview Assistant System Health Check ==="

# Python
echo -n "Python: "
python --version

# Virtual environment
echo -n "Venv: "
[ -d venv ] && echo "✅ Found" || echo "❌ Not found"

# Dependencies
echo -n "Dependencies: "
pip list | grep websockets > /dev/null && echo "✅ Installed" || echo "❌ Missing"

# FFmpeg
echo -n "FFmpeg: "
ffmpeg -version > /dev/null 2>&1 && echo "✅ Installed" || echo "❌ Not found"

# Ollama
echo -n "Ollama: "
curl -s http://localhost:11434/api/version > /dev/null && echo "✅ Running" || echo "❌ Not responding"

# Server
echo -n "Server: "
curl -s http://localhost:8123 > /dev/null && echo "✅ Running" || echo "❌ Not responding"

echo ""
echo "Health Check Complete!"
```

### Server Log Analysis

```bash
# Watch logs in real-time
tail -f logs/interview_assistant.log | jq .

# Find errors
grep '"level":"ERROR"' logs/interview_assistant.log | jq .

# Find warnings
grep '"level":"WARNING"' logs/interview_assistant.log | jq .

# Search for specific component
grep 'transcription' logs/interview_assistant.log | jq .
```

---

## Installation Issues

### Problem: Python Version Mismatch

**Symptoms**:
```
SyntaxError: invalid syntax
/venv/bin/python: bad interpreter
```

**Cause**: Python 3.8 or older

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.9+

# If wrong version, specify explicitly
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: Module Import Errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'websockets'
ImportError: cannot import name 'TransformError'
```

**Cause**: Dependencies not installed or venv not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or: .\venv\Scripts\activate  # Windows

# Reinstall all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep websockets
```

---

### Problem: FFmpeg Not Found

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Cause**: FFmpeg not installed or not in PATH

**Solution**:

**macOS**:
```bash
brew install ffmpeg
ffmpeg -version  # Verify
```

**Windows**:
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH environment variable
```

**Linux**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
ffmpeg -version  # Verify
```

---

### Problem: Pip Dependencies Conflict

**Symptoms**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages
torch/numpy version conflict
```

**Cause**: Conflicting dependency versions

**Solution**:
```bash
# Clean install
rm -rf venv/
python -m venv venv
source venv/bin/activate

# Install from scratch
pip install --upgrade pip setuptools
pip install -r requirements.txt

# If still failing, try with specific Python version
python3.9 -m venv venv39
source venv39/bin/activate
pip install -r requirements.txt
```

---

## Audio Problems

### Problem: No Audio Devices Found

**Symptoms**:
```
No audio devices found
List the available devices with --list-devices
```

**Cause**: Audio device not detected or permissions issue

**Solution**:

```bash
# List available devices
python stable_audio_client_multi_os.py --list-devices

# macOS: List AVFoundation devices
ffmpeg -f avfoundation -list_devices true -i ""

# Windows: List DirectShow devices
ffmpeg -list_devices true -f dshow -i dummy

# Linux: List ALSA devices
arecord -l
```

If no devices appear:

**macOS**:
```bash
# Check microphone permissions
System Preferences → Security & Privacy → Microphone

# Try USB microphone
python stable_audio_client_multi_os.py --device "USB Audio"
```

**Windows**:
```bash
# Check audio input in Settings
Settings → Sound → Volume and device preferences

# Restart audio service
Net Stop AudioSrv
Net Start AudioSrv
```

**Linux**:
```bash
# Check ALSA status
alsamixer

# Unmute microphone
amixer set Capture 100%
```

---

### Problem: "Broken Pipe" Errors in Audio Stream

**Symptoms**:
```
BrokenPipeError: [Errno 32] Broken pipe
Audio stream disconnected
```

**Cause**: Server stopped or network issue

**Solution**:
```bash
# Verify server is running
curl http://localhost:8123

# Check server logs
tail -f logs/interview_assistant.log

# Restart both client and server
# Terminal 1: Kill existing server
pkill -f optimized_stt_server

# Terminal 1: Start fresh server
python optimized_stt_server_v3.py

# Terminal 2: Start fresh client
python stable_audio_client_multi_os.py --device "Your Microphone"
```

---

### Problem: Audio is Very Quiet or Silent

**Symptoms**:
- Transcription shows: "[BLANK]" or random characters
- No recognition of spoken words
- Audio levels in other apps work fine

**Cause**: Microphone level too low or audio format issue

**Solution**:

```bash
# 1. Check microphone level
# macOS: System Preferences → Sound → Input
# Windows: Settings → Sound → Volume and device preferences
# Linux: alsamixer → Capture slider

# 2. Test with FFmpeg directly
ffmpeg -f avfoundation -i ":0" -t 5 test.wav  # macOS
ffmpeg -list_devices true -f dshow -i dummy   # Windows audio test

# 3. Increase ENERGY_GATE threshold (allows quieter audio)
# In optimized_stt_server_v3.py:
ENERGY_GATE = -60  # More sensitive (was -40)

# 4. Reduce WINDOW_SECONDS (process smaller chunks)
WINDOW_SECONDS = 3.0  # Instead of 6.0
```

---

### Problem: Microphone Feedback Loop

**Symptoms**:
- Loud noise or howling from speakers
- Microphone picking up its own output

**Cause**: Output audio being captured by input

**Solution**:
```bash
# 1. Use USB microphone instead of built-in
python stable_audio_client_multi_os.py --device "USB Microphone"

# 2. Mute speakers or use headphones
# 3. Reduce WINDOW_SECONDS to minimize buffering
WINDOW_SECONDS = 2.0

# 4. Use noise gate to suppress loud noise
# In optimized_stt_server_v3.py:
ENERGY_GATE = -30  # More aggressive noise filtering
```

---

## Transcription Issues

### Problem: Transcription Very Inaccurate

**Symptoms**:
- Words replaced with gibberish
- Homophones confused (to/too/two)
- Technical terms wrong (sre → "sir", k8s → "kate's")

**Cause**: Wrong Whisper model or poor audio quality

**Solution**:

**Step 1**: Improve audio quality
```bash
# Check audio levels (should be -20dB to -10dB range)
# Speak clearly and loud enough
# Reduce background noise (close windows, turn off fans)
```

**Step 2**: Use larger Whisper model
```python
# In optimized_stt_server_v3.py:
WHISPER_MODEL = "small"  # Instead of "tiny" or "base"
# or:
WHISPER_MODEL = "medium"  # Best accuracy, slower

# Trade-off: Latency increases
# tiny: 50-150ms  → base: 150-300ms → small: 300-500ms → medium: 500-1000ms
```

**Step 3**: Provide context
```python
# In optimized_stt_server_v3.py:
# Add domain-specific vocabulary to system prompt
# This helps Whisper understand technical terms
```

---

### Problem: Whisper Model Not Found

**Symptoms**:
```
RuntimeError: Model whisper-large not found
FileNotFoundError: [Errno 2] No such file or directory: '.../whisper/model.pt'
```

**Cause**: Model file corrupted or download incomplete

**Solution**:
```bash
# 1. Check model directory
ls ~/.cache/whisper/  # Should have model files

# 2. Clear cache and re-download
rm -rf ~/.cache/whisper/

# 3. Run transcription to trigger download
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

# 4. Verify file exists
ls -lh ~/.cache/whisper/model.bin  # Should be ~150MB+
```

---

### Problem: Transcription Timeout or Hangs

**Symptoms**:
```
TimeoutError: Transcription timed out
Process hung/frozen
```

**Cause**: System overload or GPU issue

**Solution**:
```bash
# 1. Use smaller model
WHISPER_MODEL = "tiny"

# 2. Increase window size (fewer transcriptions per minute)
WINDOW_SECONDS = 10.0
HOP_SECONDS = 2.0

# 3. Check system resources
top  # Watch CPU/memory

# 4. Disable GPU if causing issues
# Force CPU-only mode in code:
# model = WhisperModel("base", device="cpu", compute_type="float32")

# 5. Increase timeout in code
# From: result = model.transcribe(audio, language="en")
# To: result = model.transcribe(audio, language="en", condition_on_previous_text=False)
```

---

## Question Detection Problems

### Problem: Questions Not Being Detected

**Symptoms**:
- Valid questions not showing in Q&A panel
- Only detecting obvious questions
- Missing rhetorical questions

**Cause**: LLM not running or question detection threshold too high

**Solution**:

```bash
# 1. Verify Ollama is running
curl http://localhost:11434/api/version

# 2. Check if model is loaded
ollama list

# 3. Pull model if missing
ollama pull gpt-oss:120b-cloud

# 4. Test LLM directly
curl http://localhost:11434/api/generate -d '{"model": "gpt-oss:120b-cloud", "prompt": "What is AI?", "stream": false}'
```

Code changes:

```python
# In optimized_stt_server_v3.py:

# Lower the question detection confidence threshold
QUESTION_CONFIDENCE_THRESHOLD = 0.5  # Instead of 0.7

# Increase detection frequency
HOP_SECONDS = 0.5  # Instead of 0.8, check for questions more often

# Add debug logging
DEBUG = True
VERBOSE_BUFFER = True
```

---

### Problem: Too Many False Positives

**Symptoms**:
- Every statement detected as a question
- Non-question text marked as questions
- Noisy/unclear speech flagged as questions

**Cause**: Question detection threshold too low or LLM model not discriminating

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Raise detection confidence threshold
QUESTION_CONFIDENCE_THRESHOLD = 0.9  # More strict

# Increase buffer size (more context = better detection)
WINDOW_SECONDS = 8.0  # Instead of 6.0

# Reduce detection frequency (fewer false positives)
HOP_SECONDS = 1.5  # Instead of 0.8

# Use faster model for pre-filtering
PRE_FILTER_REGEX_ONLY = True  # Only detect obvious question patterns
```

---

### Problem: Question Cache Growing Too Large

**Symptoms**:
- Memory usage increasing
- Same questions detected multiple times
- System slowing down

**Cause**: Question deduplication cache not cleaning old entries

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Clear question cache periodically (add to main loop)
seen_questions.clear()  # Daily

# Or reduce TTL
SEEN_TTL_SEC = 3600  # 1 hour instead of 24 hours

# Or limit cache size
MAX_SEEN_QUESTIONS = 100  # Keep only most recent 100
```

---

## Answer Generation Issues

### Problem: No Answers Being Generated

**Symptoms**:
- Questions detected but no answers appear
- "Waiting for answer..." message persists
- No errors in logs

**Cause**: Ollama down, rate limiting, or answer generation disabled

**Solution**:

```bash
# 1. Check Ollama status
curl http://localhost:11434/api/version

# 2. Check if answer generation is enabled
grep "MAX_CONCURRENT_LLM" optimized_stt_server_v3.py

# 3. Increase LLM timeout
# In code: timeout=30 (instead of 10)

# 4. Check for rate limiting
grep "ANSWERS_PER_MIN" optimized_stt_server_v3.py  # Default: 3

# 5. Increase answer generation parallelism
MAX_CONCURRENT_LLM = 5  # Instead of 3
```

---

### Problem: Answers Very Short or Incomplete

**Symptoms**:
- Answer cut off mid-sentence
- Single word responses
- No explanation or context

**Cause**: Token limit too low or model generating brief responses

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Increase maximum output tokens
MAX_OUTTOK = 1000  # Instead of 500

# Increase temperature (more creative)
TEMPERATURE = 0.8  # Instead of 0.7

# Use larger/better model
OLLAMA_MODEL_CLOUD = "mistral"  # Better responses
# or:
OLLAMA_MODEL_CLOUD = "neural-chat:7b"  # More conversational

# Provide more context
LLM_CONTEXT_MODE = "full"  # Use entire transcript

# Increase response time budget
# Reduce ANSWERS_PER_MIN to allow longer answers
ANSWERS_PER_MIN = 2  # Instead of 3
```

---

### Problem: Answers Taking Too Long (>4 seconds)

**Symptoms**:
- Long delay before answer appears
- User impatient waiting
- End-to-end latency > 4s

**Cause**: Model too large or network latency

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Use faster model
OLLAMA_MODEL_CLOUD = "neural-chat:7b"  # Fast and reasonable quality
# or:
OLLAMA_MODEL_CLOUD = "orca-mini"  # Very fast, basic quality

# Reduce output length
MAX_OUTTOK = 200  # Shorter answers

# Reduce context window
LLM_CONTEXT_MODE = "window"  # Instead of "full"

# Reduce batch size (answer fewer questions in parallel)
MAX_CONCURRENT_LLM = 1
```

---

### Problem: Answers Repetitive or Low Quality

**Symptoms**:
- Same answer for different questions
- Hallucinated information
- Generic or irrelevant responses

**Cause**: Wrong persona or model quality

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Switch persona
PERSONA = "assistant"  # Instead of "candidate"
# or try: "neutral"

# Use better model
OLLAMA_MODEL_CLOUD = "mistral"  # Best quality

# Provide system prompt
SYSTEM_PROMPT = """You are an expert interview coach helping a job candidate.
Provide specific, detailed answers with examples.
Keep responses under 100 words."""

# Increase temperature (more variety)
TEMPERATURE = 0.9  # Instead of 0.7

# Vary response length
MAX_OUTTOK = 300  # Medium length
```

---

## UI/WebSocket Issues

### Problem: UI Shows "Connecting..." or Connection Fails

**Symptoms**:
- UI loading spinner never stops
- "Connection failed" error
- WebSocket connection refused

**Cause**: Server not running or port blocked

**Solution**:

```bash
# 1. Check if server is running
curl http://localhost:8123

# 2. Check port 8123 is open
netstat -tuln | grep 8123  # Linux/macOS
netstat -aon | findstr :8123  # Windows

# 3. Start server if not running
python optimized_stt_server_v3.py

# 4. If port already in use
lsof -i :8123  # Find process
kill -9 <PID>  # Kill it

# 5. Check firewall
# macOS: System Preferences → Security & Privacy → Firewall
# Windows: Windows Defender Firewall → Allow app

# 6. Try different port (if 8123 blocked)
# In optimized_stt_server_v3.py:
PORT = 8124  # Instead of 8123
# Then update UI: ws://localhost:8124
```

---

### Problem: UI Disconnects After Short Time

**Symptoms**:
- Connection drops after 1-2 minutes
- Need to refresh page
- Transcript history lost

**Cause**: WebSocket timeout or connection reset

**Solution**:

```python
# In optimized_stt_server_v3.py:

# Increase connection timeout
WEBSOCKET_TIMEOUT = 300  # 5 minutes instead of 30s

# Add ping/pong to keep connection alive
# (Already implemented, but check logs)

# Increase buffer size
BUFFER_SIZE = 262144  # 256KB instead of 128KB
```

In UI (`index.html`):

```javascript
// Increase reconnection timeout
const RECONNECT_TIMEOUT = 10000;  // 10 seconds

// Add more aggressive reconnection
ws.onclose = () => {
    setTimeout(() => {
        console.log("Reconnecting...");
        connectWebSocket();
    }, RECONNECT_TIMEOUT);
};
```

---

### Problem: UI Doesn't Update or Shows Old Data

**Symptoms**:
- Transcript not updating
- Answers not appearing in UI
- Stale Q&A list

**Cause**: WebSocket message not received or browser cache

**Solution**:

```bash
# 1. Hard refresh UI
Cmd+Shift+R  # macOS
Ctrl+Shift+R  # Windows/Linux

# 2. Clear browser cache
# Chrome/Edge: Ctrl+Shift+Delete
# Safari: Develop → Empty Caches

# 3. Check WebSocket messages
# Open Browser DevTools → Network → WS
# Look for incoming/outgoing messages

# 4. Check server logs
tail -f logs/interview_assistant.log | grep "broadcast\|broadcast"
```

---

## Performance Problems

### Problem: High Latency (>4 seconds)

**Symptoms**:
- Question asked → Long wait for answer
- System feels slow/sluggish
- p95 latency > 4 seconds

**Cause**: System overload, large models, or network issues

**Solution**:

See [Performance Tuning](PERFORMANCE.md) for detailed optimization.

Quick fixes:
```python
# Reduce buffer size
WINDOW_SECONDS = 3.0  # Instead of 6.0

# Use faster models
WHISPER_MODEL = "tiny"
OLLAMA_MODEL_CLOUD = "neural-chat:7b"

# Reduce output length
MAX_OUTTOK = 200

# Increase parallelism
MAX_CONCURRENT_LLM = 5
```

---

### Problem: High CPU Usage (>80%)

**Symptoms**:
- System hot/fan loud
- Other apps slow
- Battery drains fast

**Cause**: Model inference using CPU, large buffer, or transcription loop

**Solution**:

```python
# Use GPU if available
DEVICE = "cuda"  # Enable GPU

# Or reduce workload
WHISPER_MODEL = "tiny"
WINDOW_SECONDS = 10.0  # Fewer transcriptions per minute
HOP_SECONDS = 2.0
MAX_CONCURRENT_LLM = 1
```

---

### Problem: Memory Leak (Increasing Memory Over Time)

**Symptoms**:
- Memory usage grows continuously
- Program slows down after running hours
- Eventually runs out of memory

**Cause**: Unbounded buffer or cache

**Solution**:

```bash
# Monitor memory
watch -n 1 'ps aux | grep python | grep -v grep'

# Check for leaks
pip install memory-profiler
python -m memory_profiler optimized_stt_server_v3.py
```

In code:

```python
# Cap buffer size
BUFFER_SIZE = 131072  # Fixed size (not unbounded)

# Clear caches periodically
if question_count > 1000:
    seen_questions.clear()  # Every 1000 questions

# Limit metrics collection
MAX_METRIC_POINTS = 10000  # Not unlimited
```

---

## System Issues

### Problem: "Cannot allocate memory"

**Symptoms**:
```
MemoryError: unable to allocate X GiB for an array
OSError: Cannot allocate memory
```

**Cause**: System out of memory

**Solution**:

```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory  # Windows

# Close other applications

# Reduce model size
WHISPER_MODEL = "tiny"  # Instead of "large"

# Reduce buffer
WINDOW_SECONDS = 2.0
BUFFER_SIZE = 65536  # Half size

# Reduce concurrent LLM requests
MAX_CONCURRENT_LLM = 1
```

---

### Problem: "Port already in use"

**Symptoms**:
```
OSError: [Errno 48] Address already in use: ('0.0.0.0', 8123)
AddressInUseError
```

**Cause**: Another process on port 8123

**Solution**:

```bash
# Find process using port
lsof -i :8123  # macOS/Linux
netstat -aon | findstr :8123  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
# In optimized_stt_server_v3.py:
PORT = 8124
```

---

### Problem: Segmentation Fault or Core Dump

**Symptoms**:
```
Segmentation fault (core dumped)
Illegal instruction
Floating point exception
```

**Cause**: Native library crash (Whisper, Torch, etc.)

**Solution**:

```bash
# 1. Downgrade problematic library
pip install torch==2.0.0  # Instead of latest

# 2. Use CPU instead of GPU
# In code: device="cpu"

# 3. Reinstall PyTorch cleanly
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 4. Check for CUDA/driver issues
nvidia-smi

# 5. Update system libraries
sudo apt-get update && sudo apt-get upgrade  # Linux
brew update && brew upgrade  # macOS
```

---

## Getting Help

### Before Reporting an Issue

1. **Check this guide** - Most common issues are covered above
2. **Review logs** - Check `logs/interview_assistant.log` for errors
3. **Try quick fixes** - Restart server/client, clear cache, etc.
4. **Gather system info**:
   ```bash
   python --version
   ffmpeg -version
   pip list
   curl http://localhost:11434/api/version  # Ollama
   ```
5. **Reproduce issue** - Make sure you can consistently reproduce it

### Report an Issue

Visit: https://github.com/jcmd13/Interview_Assistant/issues

Include:

```
Title: [Brief description]

System:
- OS: (macOS/Windows/Linux)
- Python: (version)
- GPU: (Yes/No, what model)

Steps to reproduce:
1. ...
2. ...
3. ...

Expected behavior:
...

Actual behavior:
...

Logs:
[Paste relevant log section]
```

### Get Support

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and discuss
- **Documentation**: Check [README](../README.md) and other docs

---

## Performance Tuning Guides

- For **low-latency** scenarios, see [Performance.md](PERFORMANCE.md)
- For **high-accuracy** scenarios, see [Configuration.md](CONFIGURATION.md)
- For **deployment**, see [Deployment.md](DEPLOYMENT.md)

---

*Last updated: November 8, 2025*
*Need additional help? Check the [FAQ](FAQ.md)*
