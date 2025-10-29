# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Interview_Assistant is a real-time AI interview assistant with three core components:
- **Server** (`optimized_stt_server_v3.py`): WebSocket server handling audio transcription via faster-whisper and AI-powered Q&A via Ollama
- **Client** (`stable_audio_client_multi_os.py`): Multi-platform audio streaming client using FFmpeg
- **UI** (`index.html`): Standalone web dashboard for monitoring transcripts and Q&A

The system uses Ollama with cloud models for privacy-focused, local AI processing. No API keys required for core functionality.

### Project Goals & Philosophy

**Primary Goal**: Fastest question → answer latency for live interviews (target: <4s end-to-end)

**Core Values**:
1. **Performance-First**: End-to-end latency is the only metric that matters
2. **Zero-Friction Setup**: Works immediately after installation with no configuration
3. **Complete Modularity**: All components designed as swappable plugins
4. **Privacy-First**: Local processing by default, explicit opt-in for any data collection
5. **Glanceable UI**: Zero interaction required during live conversations

**Target Users**: Job seekers, interview candidates, business professionals, customer success teams

**Business Model**: Freemium SaaS (free core tool, premium career services planned for future)

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# For GPU acceleration (optional, replace CPU-only PyTorch):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Running the Application
```bash
# 1. Start Ollama service (in separate terminal)
ollama serve

# 2. Pull required model
ollama pull gpt-oss:120b-cloud

# 3. Start the WebSocket server
python optimized_stt_server_v3.py

# 4. Open the UI
# Simply open index.html in a browser (no web server needed)

# 5. List available audio devices
python stable_audio_client_multi_os.py --list-devices

# 6. Start audio streaming
python stable_audio_client_multi_os.py --device "YOUR_DEVICE_NAME"
```

### Testing Individual Components
```bash
# Test Ollama connectivity
curl http://localhost:11434/api/version

# List installed Ollama models
ollama list

# Verify FFmpeg installation
ffmpeg -version

# Test audio device listing (platform-specific)
# Windows: ffmpeg -list_devices true -f dshow -i dummy
# macOS: ffmpeg -f avfoundation -list_devices true -i ""
# Linux: arecord -l
```

## Architecture

### Server Architecture (`optimized_stt_server_v3.py`)

**Core Components:**
- **Audio Pipeline**: Maintains a rolling PCM buffer (`pcm_buf`) with configurable window (`WINDOW_SECONDS=6.0`) and hop (`HOP_SECONDS=0.8`) for overlapping transcription
- **WebSocket Handler** (`handler()`): Manages client connections, differentiates between UI clients (receive broadcasts) and audio streamers (send-only)
- **Transcription Loop** (`read_and_transcribe_loop()`): Global async task that processes audio windows, runs Whisper inference, and emits new text
- **LLM Analyzer** (`ImprovedLLMAnalyzer`): Detects questions from transcript segments using Ollama, maintains seen question cache to avoid duplicates, enforces rate limiting
- **State Management**: Global state including `transcript_lines` (full conversation history), `detected` deque (detected questions), and `qa_log` (answered questions)

**Key Design Patterns:**
- Sliding window audio processing with energy gating (`ENERGY_GATE`) to skip silence
- Semaphore-based concurrency control for LLM requests (`MAX_CONCURRENT_LLM=3`)
- Deduplication via question key hashing (`_qkey()`) with TTL-based expiry
- Context mode switching: "full", "window", or "headtail" for sending transcript context to LLM
- Persona-based response sanitization for candidate voice mode

**Data Flow:**
1. Audio client streams raw PCM data → `pcm_buf`
2. Transcriber loop processes windows → faster-whisper → new text segments
3. New text → `ImprovedLLMAnalyzer.analyze_segment()` → question candidates
4. Question candidates → `generate_answer()` with full context → answers
5. All updates broadcast to UI clients via individual queues

### Client Architecture (`stable_audio_client_multi_os.py`)

**Multi-Platform Audio Capture:**
- **Platform Detection**: Automatically configures FFmpeg based on OS (dshow/Windows, avfoundation/macOS, alsa/Linux)
- **FFmpeg Integration**: Spawns subprocess for audio capture, streams raw PCM (16kHz, mono, s16le) to WebSocket
- **Connection Management** (`StableAudioStreamer`): Automatic reconnection with exponential backoff, backpressure handling, graceful shutdown

**Device Configuration:**
- Windows: Uses DirectShow format with device names like `"Microphone (Device Name)"`
- macOS: Uses AVFoundation with index-based devices like `":0"`
- Linux: Uses ALSA with hardware addresses like `"hw:0,0"`

### UI Architecture (`index.html`)

**Single-File Web Dashboard:**
- Three-panel layout: Transcript (left), Answer Detail (center), Q&A List (right)
- WebSocket client connects to `ws://127.0.0.1:8123/`
- Real-time updates via server broadcasts (transcript, detected questions, answers)
- Client-side state management with keyboard shortcuts
- Export functionality to save session as Markdown

## Configuration System

**Configuration Priority:**
1. Hardcoded defaults in Python files (current implementation)
2. Environment variables (legacy, mostly removed)
3. `.env` file (optional, see `.env.example`)

**Key Server Parameters:**
- `WHISPER_MODEL`: "tiny" (fast) to "large" (accurate)
- `OLLAMA_MODEL_CLOUD`: Model for Q&A (default: "gpt-oss:120b-cloud")
- `LLM_CONTEXT_MODE`: "full" (entire transcript), "window" (last N lines), "headtail" (head + tail)
- `TECH_INTERVIEW_MODE`: Optimizes prompts for technical interviews
- `PERSONA`: "candidate", "assistant", or "neutral" for answer tone
- `MAX_CONCURRENT_LLM`: Concurrent LLM request limit
- `ANSWERS_PER_MIN`: Rate limiting for answers

**Modifying Configuration:**
Edit variables directly in `optimized_stt_server_v3.py` at the top of the file (lines 14-61). The configuration section is clearly marked.

## Important Implementation Details

### LLM Question Detection
The analyzer uses a two-stage process:
1. **Pre-filtering**: Fast regex check for question indicators (what, how, why, etc.)
2. **LLM Analysis**: Ollama extracts questions from dialogue with JSON array output
3. **Deduplication**: Questions hashed via `_qkey()` and cached in `seen_questions` dict

### Audio Buffer Management
- Fixed-size rolling buffer prevents memory overflow
- Energy gating skips silent windows (configurable via `ENERGY_GATE`)
- Overlapping windows ensure no speech is lost between chunks
- `bytes_since_last` tracks when next processing is due

### WebSocket Message Protocol
**Client → Server:**
- Binary: Raw PCM audio data (16-bit signed, 16kHz, mono)
- JSON: `{"cmd": "hello", "client": "audio_streamer"}` - identifies as audio client
- JSON: `{"cmd": "reset"}` - clears all state

**Server → Client:**
- `{"snapshot": {...}}` - initial state on connection
- `{"transcript": "text"}` - new transcription
- `{"detected": [...]}` - question detected
- `{"answered": {...}}` - answer generated

### Ollama Integration
- Uses synchronous `ollama.chat()` wrapped in `run_in_executor()` for async compatibility
- Model specified per-call, allows mixing fast detection models with powerful answer models
- Automatic retry with cache cleanup if model fails to load
- No streaming mode currently (processes full responses)

## Common Modifications

**Changing Whisper Model:**
Edit `MODEL_NAME` in `optimized_stt_server_v3.py:22`. Options: "tiny", "base", "small", "medium", "large". Larger models are more accurate but slower.

**Switching Ollama Models:**
Edit `OLLAMA_MODEL_CLOUD` in `optimized_stt_server_v3.py:34`. Must pull model first: `ollama pull model-name`

**Adjusting Audio Processing:**
- Increase `WINDOW_SECONDS` for better context but higher latency
- Decrease `HOP_SECONDS` for more frequent updates but higher CPU usage
- Raise `ENERGY_GATE` to be more aggressive about skipping silence

**Customizing LLM Behavior:**
- Set `TECH_INTERVIEW_MODE=False` for general conversation mode
- Change `LLM_CONTEXT_MODE` to "window" for limited context (faster, less accurate)
- Adjust `MAX_OUTTOK` to control answer length
- Modify `PERSONA` to change answer tone

## Dependencies

**Core:**
- `faster-whisper`: Speech recognition (uses CTranslate2 backend)
- `ollama`: Python client for Ollama API
- `websockets`: Async WebSocket server
- `torch`, `torchvision`, `torchaudio`: PyTorch (CPU or CUDA)
- `numpy`: Array operations
- `FFmpeg`: External audio capture tool (not a Python package)

**External Services:**
- Ollama server must be running (`ollama serve`)
- Required model must be pulled (`ollama pull gpt-oss:120b-cloud`)

## Debugging

**Enable verbose output:**
Set `DEBUG=True` and `VERBOSE_BUFFER=True` in `optimized_stt_server_v3.py:60-61`

**Common issues:**
- "Ollama not accessible": Ensure `ollama serve` is running
- "Model not found": Run `ollama pull <model-name>`
- FFmpeg errors: Verify device name with `--list-devices`
- No transcription: Check `ENERGY_GATE` threshold, may be filtering speech
- Duplicate questions: Adjust `SEEN_TTL_SEC` or check `_qkey()` hashing

**Monitoring:**
- Server logs show connection events, transcription, question detection, and LLM calls
- UI displays connection status and Q&A count
- Client logs show audio streaming status and reconnection attempts

---

## Development Principles & Best Practices

### Critical Performance Metric

**THE PRIMARY PERFORMANCE INDICATOR**: End-to-end latency from question asked → usable LLM answer displayed

**Target Latency Budget**:
- Audio capture to transcription: < 500ms
- Question detection: < 100ms
- LLM response generation: < 3s (target: 1.5s)
- Term explanation (optional): < 200ms additional
- **TOTAL END-TO-END**: < 4s from question spoken to answer displayed

All architectural decisions MUST optimize for this latency chain. Measure end-to-end latency for every change.

### Priority Hierarchy

When requirements conflict, prioritize in this order:
1. **Performance** (end-to-end latency)
2. **Modularity** (plugin architecture, swappable components)
3. **Zero-Friction UX** (works out-of-box, minimal interaction)
4. **Security** (credential storage, input validation)
5. **User Experience** (glanceable UI, adaptive density)
6. **Features** (additional capabilities)

### Performance-First Decision Making

**DO:**
- ✅ Measure end-to-end latency for every change
- ✅ Use fastest available solution within cost constraints (free tier only)
- ✅ Batch LLM prompts when possible (e.g., question + term explanations in one call)
- ✅ Implement caching for term definitions, customer context
- ✅ Use async/await throughout for non-blocking I/O
- ✅ Stream LLM responses for progressive display

**DON'T:**
- ❌ Add features that increase latency >200ms without explicit justification
- ❌ Make synchronous API calls in the critical path
- ❌ Fetch data that could be cached
- ❌ Use threads when asyncio is available
- ❌ Implement features requiring paid services without free fallback

### Zero-Configuration Philosophy

**DO:**
- ✅ Auto-detect environment (audio devices, Ollama status, network) on first launch
- ✅ Select optimal defaults automatically
- ✅ Work completely offline with local-only processing
- ✅ Test that system works immediately after install (no configuration)

**DON'T:**
- ❌ Require user to pre-install dependencies manually (future: bundle Ollama)
- ❌ Require user to create accounts for core functionality
- ❌ Block core features on configuration or API keys
- ❌ Assume internet connectivity for basic operation

### Structured Logging from Day One

**DO:**
- ✅ Use structured JSON logging with timing metadata
- ✅ Log every pipeline stage with duration (audio, transcription, detection, LLM, UI)
- ✅ Include component name, log level, timestamp, message, metadata in every entry
- ✅ Provide verbose mode for detailed debugging
- ✅ Use clear, actionable error messages for users (not stack traces)

**Example Log Format:**
```json
{
  "timestamp": "2025-10-28T04:00:00.000Z",
  "level": "INFO",
  "component": "transcription.whisper_engine",
  "message": "Transcription completed",
  "metadata": {
    "audio_duration_ms": 3200,
    "processing_time_ms": 450,
    "model": "base",
    "word_count": 42,
    "confidence": 0.94,
    "request_id": "req_abc123"
  }
}
```

**DON'T:**
- ❌ Add logging as afterthought (design in from start)
- ❌ Show technical errors to users (log internally, show friendly message)
- ❌ Skip timing data in logs
- ❌ Use print() statements (use proper logging library)

### Security & Privacy from Day One

**DO:**
- ✅ Validate all user inputs and external data
- ✅ Store credentials in OS keychain (encrypted) - never plaintext
- ✅ Process everything locally by default (data stays on device)
- ✅ Require explicit opt-in for ANY data collection
- ✅ Provide easy export/deletion of all user data
- ✅ Support fully offline mode

**DON'T:**
- ❌ Store credentials in plaintext config files
- ❌ Collect data without explicit user consent
- ❌ Require cloud services for core functionality
- ❌ Add security as afterthought

### Graceful Error Handling

**DO:**
- ✅ Implement graceful degradation (continue with reduced functionality)
- ✅ Provide automatic fallbacks (cloud API fails → local model)
- ✅ Show clear, actionable error messages to users
- ✅ Log detailed errors internally for debugging
- ✅ Recover automatically when possible

**Error Message Pattern:**
```
User-Facing: "Audio device 'USB Microphone' not found."
Action: "→ Check Settings > Audio Input to select a working device."

Internal Log: Full exception details with stack trace
```

**DON'T:**
- ❌ Crash the application on errors
- ❌ Show stack traces to users
- ❌ Fail silently (always log)
- ❌ Require restart to recover

---

## Future Architecture (Planned Enhancements)

The current implementation is a foundation for a more comprehensive system. Future development will include:

### Plugin Architecture
- All components (audio, transcription, LLM, UI, CRM) as swappable plugins
- Hot-swapping plugins at runtime without restart
- Abstract interfaces for each plugin type
- Plugin registry for discovery and dependency management

### Three-Tier LLM Access
- **Tier 1 (Default)**: Local Ollama on localhost:11434, no API key, works offline
- **Tier 2 (Recommended)**: Ollama Cloud API with free tier, faster responses (~500ms)
- **Tier 3 (Premium)**: OpenAI/Anthropic with paid keys, best quality
- Graceful fallback chain: Tier 3 → Tier 2 → Tier 1

### Smart Onboarding Flow (Optional)
- **Phase 1**: LLM/API setup (optional, skippable)
- **Phase 2**: Career profile setup (optional, enhances answers with resume context)
- **Phase 3**: Session context (per-interview company/position data)
- All phases optional - system works perfectly if skipped

### User Profile & Context Management
- Local SQLite database for user profiles, interview sessions, Q&A history
- Profile-aware LLM prompts (inject resume, experience, session context)
- Session tracking for analytics and outcome monitoring
- Privacy-first: encrypted at rest, easy export/deletion

### Intelligent Term/Acronym Handling
- Auto-detect acronyms and industry jargon (SRE, CI/CD, K8s)
- Explain terms inline or via tooltip on first mention
- Session-scoped deduplication (explain each term once)
- Batch explanations with existing LLM prompts (no extra latency)
- Toggle feature on/off per session

### Card-Based Modular UI
- Grid-based layout (20rem columns x 1rem rows)
- Drag-and-drop card repositioning with snap-to-grid
- Layout presets: Interview Stealth, Phone Call, Business Meeting, Customer Call
- Adaptive density modes based on context detection
- Hotkeys for quick layout switching (Ctrl+1, Ctrl+2, etc.)

### CRM Integration (Business Use Cases)
- Salesforce and Microsoft Dynamics 365 plugins
- Auto-detect CRM-linked calls (phone/email match)
- Fetch customer context asynchronously (non-blocking)
- AI-enhanced insights: upsell opportunities, churn risk, talking points
- Context-aware LLM prompts with customer history

### Performance Monitoring
- Track latency for each pipeline stage
- Calculate p50, p95, p99 percentiles
- Enforce latency budgets with warnings
- Export metrics to CSV for analysis

### Feature Flags
- Extensible configuration for enabling/disabling features
- Future services designed but disabled by default
- Database hooks for analytics, question DB, job placement services

---

## Anti-Patterns to Avoid

### ❌ DON'T:
1. **Require configuration for core functionality** - Local-only mode must work out-of-box
2. **Collect data without explicit opt-in** - Privacy-first always
3. **Store API keys in plaintext** - Use OS keychain
4. **Add latency without measurement** - Benchmark before/after
5. **Skip structured logging** - Log all operations with timing
6. **Use unclear error messages** - Provide actionable guidance
7. **Break modularity** - Keep components loosely coupled
8. **Force user interaction during calls** - Violates zero-interaction principle
9. **Hard-code configuration** - Use configuration system
10. **Skip input validation** - Validate from day one

---

## Development Quality Gates

### Before Marking Task Complete
- ✅ End-to-end latency measured and within budget
- ✅ Structured logging with timing data implemented
- ✅ Error handling with clear user messages
- ✅ Input validation for external data
- ✅ Works without configuration (defaults tested)
- ✅ Fallback behavior works when dependencies unavailable
- ✅ Privacy controls clearly explained (if applicable)
- ✅ Documentation updated

### Before Phase Completion
- ✅ All phase tasks complete
- ✅ Performance benchmarks met (< 4s end-to-end)
- ✅ Auto-detection working for common environments
- ✅ Security audit completed
- ✅ Integration tests passing

---

## Communication Guidelines

### When Reporting Progress
- State which task is being addressed
- Report end-to-end latency impact if applicable
- Highlight deviations from spec with reasoning
- Include structured log examples for new components

### When Asking for Clarification
- Present options with performance/latency trade-offs
- Include measurements when available
- Default to fastest option maintaining modularity

### When Proposing Changes
- Explain performance impact (measure latency)
- Show how change maintains modularity
- Demonstrate zero-config still works
- Get explicit approval before major architectural changes

---

## Context Awareness

### User Background
- DevOps/IT Security professional
- Python, PowerShell, Home Assistant, N8N experience
- Building for accessibility (neurodivergent, anxious professionals)
- Values: Performance, reliability, modularity, "it just works"
- Running on Mac (M-series)

### Success Metrics
- **Critical**: End-to-end latency < 4s (p95)
- Zero interaction during meetings
- Works on fresh macOS install with minimal setup
- Memory stable, CPU < 10%
- Structured logging throughout
