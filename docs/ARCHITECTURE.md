# Architecture Documentation

**Last Updated**: November 8, 2025
**Status**: Production Ready (v1.0)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Plugin System](#plugin-system)
5. [Performance Model](#performance-model)
6. [Concurrency & Threading](#concurrency--threading)
7. [Configuration System](#configuration-system)
8. [Logging & Monitoring](#logging--monitoring)
9. [Error Handling](#error-handling)
10. [Security Architecture](#security-architecture)

---

## System Overview

Interview Assistant is built on a **three-tier architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Web UI (index.html)                         │   │
│  │  • Vanilla JavaScript, zero dependencies            │   │
│  │  • Real-time WebSocket connection                   │   │
│  │  • Responsive grid layout with keyboard shortcuts   │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Application Server Layer                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    optimized_stt_server_v3.py (WebSocket Server)    │   │
│  │  • Handles all transcription and LLM orchestration   │   │
│  │  • Manages concurrent client connections            │   │
│  │  • Broadcasts state updates to all UI clients       │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Plugin Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Transcription│  │   LLM        │  │  Audio       │      │
│  │  Plugins     │  │  Plugins     │  │  Plugins     │      │
│  │              │  │              │  │              │      │
│  │ • Whisper    │  │ • Ollama     │  │ • Effects    │      │
│  │ • Azure STT  │  │ • OpenAI     │  │ • Filters    │      │
│  │ • Google STT │  │ • Claude     │  │ • Compressor │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Audio Client Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  stable_audio_client_multi_os.py                    │   │
│  │  • Platform-specific audio capture (FFmpeg)         │   │
│  │  • WebSocket streaming to server                    │   │
│  │  • Automatic reconnection & backpressure handling   │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   Core Services Layer                         │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Plugin System  │  │ Configuration  │  │ Structured   │  │
│  │                │  │ Management     │  │ Logging      │  │
│  ├────────────────┤  ├────────────────┤  ├──────────────┤  │
│  │ State Manager  │  │ Error Handler  │  │ Metrics      │  │
│  │                │  │                │  │ Collection   │  │
│  ├────────────────┤  ├────────────────┤  ├──────────────┤  │
│  │ Credential Mgr │  │ Rate Limiter   │  │ Input        │  │
│  │                │  │                │  │ Validation   │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Server (`optimized_stt_server_v3.py`)

**Responsibilities**:
- Listen for WebSocket connections (UI clients and audio streamers)
- Buffer incoming audio data
- Run transcription pipeline asynchronously
- Detect questions from transcript
- Generate answers using LLM
- Broadcast updates to all connected UI clients

**Key Data Structures**:
```python
pcm_buf: bytes                          # Rolling audio buffer
transcript_lines: List[str]             # Full conversation history
detected: deque[str]                    # Queue of detected questions
qa_log: Dict[str, Dict]                 # Question → Answer mapping
seen_questions: Dict[str, float]        # Question dedup cache
```

**Main Loops**:
1. **Connection Handler** - Handles new WebSocket connections
2. **Transcription Loop** - Processes audio windows continuously
3. **LLM Analysis Task** - Detects questions (async)
4. **Answer Generation Task** - Generates answers (async)

### 2. Audio Client (`stable_audio_client_multi_os.py`)

**Responsibilities**:
- Detect and initialize audio device
- Stream raw PCM audio to server
- Handle reconnection automatically
- Provide backpressure feedback

**Audio Specifications**:
- **Format**: PCM (raw audio)
- **Sample Rate**: 16,000 Hz
- **Bit Depth**: 16-bit signed little-endian
- **Channels**: Mono (1)
- **Buffer Size**: 4,096 samples (256ms at 16kHz)

**Reconnection Strategy**:
- Exponential backoff: 0.1s → 0.5s → 2s → 10s → 30s
- Reset on successful connection

### 3. Web UI (`index.html`)

**Responsibilities**:
- Display live transcript
- Show detected questions
- Display answers with context
- Provide keyboard shortcuts
- Export session to Markdown

**Architecture**:
- Single HTML file with embedded CSS and JavaScript
- WebSocket client connects to `ws://127.0.0.1:8123/`
- Three-panel layout (Transcript | Answer Detail | Q&A List)
- Event-driven updates from server

---

## Data Flow

### Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────┐
│ User speaks a question into microphone                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Audio Client (stable_audio_client_multi_os.py)             │
│  1. Capture 256ms of audio (4,096 samples)                 │
│  2. Convert to PCM 16-bit mono                              │
│  3. Stream via WebSocket to server                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ (Binary data, ~128KB/s)
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Server - Audio Input Handler                                │
│  1. Receive PCM chunks                                       │
│  2. Append to rolling buffer (pcm_buf)                      │
│  3. Check if window ready (WINDOW_SECONDS elapsed)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Transcription Pipeline                                       │
│  1. Extract audio window from buffer                         │
│  2. Apply energy gating (skip silence)                       │
│  3. Run faster-whisper (Whisper.AI)                         │
│  4. Parse transcript → add to transcript_lines              │
│  5. Latency: 100-400ms (GPU: 50-200ms)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ (e.g., "What's your experience with...")
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Broadcast Transcription to UI                               │
│  JSON: {"transcript": "What's your experience with..."}    │
└─────────────────────┬───────────────────────────────────────┘
                      │
           ┌──────────┼──────────┐
           ↓                      ↓
    ┌────────────┐        ┌─────────────────────────────────┐
    │ UI Updates │        │ Question Detection (Async Task)│
    │ Transcript │        └──────────┬──────────────────────┘
    └────────────┘                   │
                                     │ (LLM Analysis)
                                     ↓
                        ┌─────────────────────────────────┐
                        │ Is this a question?             │
                        │  1. Pre-filter: regex check     │
                        │  2. LLM analysis: Ollama call   │
                        │  3. Hash for deduplication      │
                        │  4. Add to detected queue       │
                        │  5. Latency: 50-200ms           │
                        └──────────┬────────────────────────┘
                                   │
                        ┌──────────────────┐
                        │ Question Detected?
                        └────┬─────────────┘
                             │
                 ┌───────────┬┴────────────┐
                 │           │             │
              YES │        NO │             │
                 ↓           ↓             │
        ┌─────────────┐   (continue       │
        │Answer       │    listening)     │
        │Generation   │                   │
        │(Async Task) │                   │
        │             │                   │
        │1. Build     │                   │
        │  prompt with│                   │
        │  full       │                   │
        │  context    │                   │
        │2. Call      │                   │
        │  Ollama     │                   │
        │3. Stream    │                   │
        │  response   │                   │
        │4. Latency:  │                   │
        │  1.5-3s     │                   │
        └──────┬──────┘                   │
               │                          │
               └──────────┬───────────────┘
                          │
                          ↓
        ┌──────────────────────────────────┐
        │ Broadcast to UI                  │
        │ JSON: {                          │
        │   "detected": "question text",   │
        │   "answered": {                  │
        │     "question": "...",           │
        │     "answer": "..."              │
        │   }                              │
        │ }                                │
        └──────────────┬───────────────────┘
                       │
                       ↓
        ┌──────────────────────────────────┐
        │ UI Update                        │
        │ 1. Add to Q&A list              │
        │ 2. Show answer in detail panel   │
        │ 3. Update counter               │
        │ 4. Highlight new item           │
        └──────────────────────────────────┘
```

---

## Plugin System

### Architecture

The plugin system provides extensibility at three levels:

```
┌────────────────────────────────────────────────┐
│         Plugin Registry (src/core/plugins.py)  │
│  • Central registration point                  │
│  • Load/unload/reload support                  │
│  • Dependency management                       │
│  • Hot-swap capability                         │
└──────────┬───────────────────────────────────┘
           │
    ┌──────┴────────┬─────────────┬──────────┐
    ↓               ↓             ↓          ↓
┌─────────────────────────────────────────────────────────────┐
│               Plugin Interfaces (Base Classes)              │
├─────────────────────────────────────────────────────────────┤
│ • TranscriptionBackend (src/transcription/base.py)        │
│ • StreamingTranscriptionBackend                            │
│ • LLMBackend (src/llm/base.py)                            │
│ • AudioProcessor (src/audio/base.py)                      │
│ • ChainedAudioProcessor                                    │
└──────────┬──────────────────┬─────────────┬────────────────┘
           │                  │             │
    ┌──────▼───────┐  ┌──────▼──────┐  ┌───▼──────────┐
    │ Transcription │  │     LLM     │  │ Audio Effects │
    │ Implementations   │ Implementations   │ Implementations│
    │                  │             │
    │ • WhisperTr   │  │ • OllamaLLM │  │ • NoiseGate    │
    │ • StreamWhisp │  │ • OllamaAna │  │ • HighPassFilt │
    │ • [Extensible]│  │ • [Extensib]│  │ • VoiceEnhance │
    │                  │             │  │ • Compressor   │
    │                  │             │  │ • SpectralNR   │
    └──────────────┘  └─────────────┘  └────────────────┘
```

### How Plugins Work

1. **Registration** (at startup):
```python
# In src/plugins/__init__.py
register_builtin_plugins()  # Registers all built-in plugins
```

2. **Loading**:
```python
# At runtime
plugin_registry.load_plugin(
    "whisper_transcriber",
    config={"model": "base"}
)
```

3. **Usage**:
```python
transcriber = get_plugin("whisper_transcriber")
result = transcriber.transcribe(audio_data)
```

4. **Plugin Structure**:
```python
class MyPlugin(PluginInterface):
    def initialize(self, config):
        """Setup plugin with configuration"""
        pass

    def shutdown(self):
        """Cleanup resources"""
        pass

    def is_ready(self) -> bool:
        """Check if plugin is ready to use"""
        pass
```

### Built-in Plugins

| Category | Plugin | File | Status |
|----------|--------|------|--------|
| **Transcription** | WhisperTranscriber | `src/transcription/whisper.py` | ✅ Active |
| | StreamingWhisperTranscriber | `src/transcription/whisper.py` | ✅ Active |
| **LLM** | OllamaLLM | `src/llm/ollama.py` | ✅ Active |
| | OllamaAnalyzer | `src/llm/ollama.py` | ✅ Active |
| **Audio Effects** | NoiseGate | `src/audio/effects.py` | ✅ Active |
| | HighPassFilter | `src/audio/effects.py` | ✅ Active |
| | VoiceEnhancer | `src/audio/effects.py` | ✅ Active |
| | DynamicCompressor | `src/audio/effects.py` | ✅ Active |
| | SpectralNoiseReducer | `src/audio/effects.py` | ✅ Active |

---

## Performance Model

### Latency Budget

The system targets **<4 seconds end-to-end** from question asked to answer displayed.

```
┌──────────────────────────────────────────────────┐
│ Total Budget: 4000ms (p95)                        │
├──────────────────────────────────────────────────┤
│ Audio Capture          │ ████░░░░░░░░│ ~100ms    │
│ Transcription (Whisper)│ ██████░░░░░░│ ~300ms    │
│ Question Detection     │ ██░░░░░░░░░░│ ~100ms    │
│ Answer Generation      │ ███████████░│ ~2500ms   │
│ Network & UI           │ ██░░░░░░░░░░│ ~100ms    │
├──────────────────────────────────────────────────┤
│ TOTAL                  │ ████████████│ ~3100ms   │
│ Buffer (Contingency)   │ ░░░░░░░░░░  │ ~900ms    │
└──────────────────────────────────────────────────┘
```

### Latency Components

| Stage | Min | Typical | Max | Notes |
|-------|-----|---------|-----|-------|
| **Audio Capture** | 50ms | 100ms | 200ms | Platform dependent |
| **Buffer accumulation** | 0ms | 200ms | 1000ms | Configurable window |
| **Whisper (CPU)** | 200ms | 400ms | 800ms | Model dependent |
| **Whisper (GPU)** | 50ms | 150ms | 300ms | With CUDA |
| **Question Detection** | 30ms | 75ms | 150ms | With caching |
| **Answer Generation** | 1000ms | 2000ms | 3500ms | Model size dependent |
| **Network Round-trip** | 10ms | 30ms | 100ms | Local network |
| **UI Rendering** | 50ms | 100ms | 200ms | Browser dependent |

### Throughput

- **Audio Stream**: 128 KB/s (16kHz × 2 bytes × 1 channel)
- **Question Detection**: 1-5 questions per minute (user dependent)
- **Answer Generation**: 1-3 concurrent requests (configurable)

---

## Concurrency & Threading

### Threading Model

```
┌────────────────────────────────────────────────┐
│         Main Thread (Event Loop)               │
│  • Handles WebSocket connections               │
│  • Dispatches async tasks                      │
│  • Broadcasts updates to clients               │
└────────────┬─────────────────────────────────┘
             │
      ┌──────┴──────┬────────────┬──────────┐
      ↓             ↓            ↓          ↓
 ┌─────────┐ ┌────────────┐ ┌────────┐ ┌──────┐
 │Audio    │ │Transcribe  │ │LLM Ana │ │State │
 │Buffer   │ │(Executor)  │ │(Execut)│ │Mgmt  │
 │(Thread  │ │            │ │        │ │(Lock)│
 │Safe)    │ │Process &   │ │Async   │ │      │
 │         │ │Analyze    │ │Task    │ │      │
 └─────────┘ └────────────┘ └────────┘ └──────┘
```

### Concurrency Controls

1. **RLock (Reentrant Lock)**:
   - Protects: Audio buffer, transcript, state
   - Prevents: Race conditions in read/write

2. **Semaphore**:
   - Limits: MAX_CONCURRENT_LLM requests
   - Default: 3 simultaneous LLM calls

3. **Async/Await**:
   - Transcription: `run_in_executor()` for CPU-bound
   - LLM: `asyncio.create_task()` for I/O-bound
   - WebSocket: Native async handling

### Thread Safety Guarantees

- ✅ Transcript buffer: Protected by lock
- ✅ Question cache: Protected by lock
- ✅ Answer log: Protected by lock
- ✅ WebSocket broadcasts: Serialized by event loop
- ✅ Metrics collection: Thread-safe with locks

---

## Configuration System

### Configuration Hierarchy

```
┌─────────────────────────────────────────────┐
│ Program Defaults (src/core/config.py)      │
│  • Fallback values if nothing else provided │
│  • Conservative settings for stability     │
└──────────────┬──────────────────────────────┘
               │ (Overridden by...)
               ↓
┌─────────────────────────────────────────────┐
│ Environment Variables (.env)               │
│  • Application settings                    │
│  • API keys & credentials                  │
└──────────────┬──────────────────────────────┘
               │ (Overridden by...)
               ↓
┌─────────────────────────────────────────────┐
│ Code Settings (optimized_stt_server_v3.py) │
│  • Runtime configuration                   │
│  • High-priority settings                  │
└─────────────────────────────────────────────┘
```

### Configuration Sections

| Section | Purpose | File |
|---------|---------|------|
| **Audio** | Mic, sample rate, buffer size | server config |
| **Transcription** | Whisper model, language | server config |
| **LLM** | Model, temperature, context mode | server config |
| **Performance** | Window size, hop, thresholds | server config |
| **Behavior** | Tech interview mode, persona | server config |
| **System** | Logging, debug, verbosity | config module |

---

## Logging & Monitoring

### Structured Logging

All logs are JSON with consistent schema:

```json
{
  "timestamp": "2025-11-08T12:34:56.789Z",
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

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Detailed tracing | "Buffer position: 512000" |
| **INFO** | Normal operations | "Transcription completed" |
| **WARNING** | Recoverable issues | "Latency exceeded threshold" |
| **ERROR** | Error conditions | "Ollama not responding" |

### Metrics Collection

Located in `src/core/metrics.py`:

- **MetricsCollector**: Central metrics registry
- **LatencyTracker**: Context manager for timing
- **MetricStats**: Percentile calculations (p50, p95, p99)
- **Thread-safe**: Protected by RLock

**Tracked Metrics**:
- Component latencies (transcription, LLM, network)
- Throughput (requests/second)
- Error rates
- System resource usage (memory, CPU)

---

## Error Handling

### Exception Hierarchy

```
Exception
├── CustomException (src/core/errors.py)
│   ├── TranscriptionError
│   │   ├── WhisperError
│   │   └── ModelNotFoundError
│   ├── LLMError
│   │   ├── OllamaNotAvailableError
│   │   └── ModelResponseError
│   ├── AudioError
│   │   ├── DeviceNotFoundError
│   │   └── AudioCaptureError
│   └── ConfigurationError
│       └── InvalidConfigError
└── [Built-in exceptions]
```

### Error Recovery Strategies

| Error | Detection | Recovery | Fallback |
|-------|-----------|----------|----------|
| **Ollama Down** | Connection error | Retry with backoff | Disable answers |
| **Bad Audio** | Empty buffer | Skip window | Continue listening |
| **OOM** | Memory error | Clear caches | Reduce buffer size |
| **Device Lost** | I/O error | Reconnect audio | Stop streaming |

### Graceful Degradation

```
Service Degradation Chain:
────────────────────────

1. ALL WORKING (Normal)
   ✅ Transcription ✅ Questions ✅ Answers

2. LLM UNAVAILABLE (Degraded)
   ✅ Transcription ⚠️ Questions (cached) ❌ Answers
   → Show: Transcript only, no Q&A

3. TRANSCRIPTION POOR (Degraded)
   ⚠️ Transcription ⚠️ Questions (low conf) ❌ Answers
   → Show: Uncertain transcript, few questions

4. AUDIO LOST (Severe)
   ❌ Transcription ❌ Questions ❌ Answers
   → Show: "Waiting for audio connection..."
```

---

## Security Architecture

### Input Validation

All external inputs are validated before processing:

```python
# Audio validation
InputValidator.validate_audio(data, max_size=10_000_000)

# JSON validation
InputValidator.validate_json(data, max_size=1_000_000)

# Text sanitization
InputValidator.sanitize_text(user_input, max_length=100_000)

# Filename validation
InputValidator.validate_filename(filename)
```

### Rate Limiting

Three strategies available:

1. **Token Bucket** (default):
   - Allows bursts up to limit
   - Gradually refills tokens
   - Good for variable traffic

2. **Sliding Window**:
   - Strict rate enforcement
   - No burst allowance
   - Good for strict quotas

3. **Leaky Bucket**:
   - Smooth rate limiting
   - Prevents burst spikes
   - Good for stable output

### Credential Management

```python
# Store credential securely
credential_manager.store("api_key", "sk-...")

# Retrieve when needed
key = credential_manager.retrieve("api_key")

# Delete sensitive data
credential_manager.delete("api_key")
```

**Security Features**:
- ✅ Credentials never logged in plaintext
- ✅ Hash-based logging for audit
- ✅ Thread-safe access
- ✅ Extensible for encryption

### Network Security

- **Local-Only**: Server bound to localhost by default
- **WebSocket**: No authentication needed (local network assumption)
- **CORS**: Can be configured for specific origins
- **Rate Limiting**: Per-IP rate limits available

---

## Deployment Architectures

### Single Machine (Default)

```
┌─────────────────────────────┐
│   Developer's Laptop        │
├─────────────────────────────┤
│ Audio Client                │
│ WebSocket Server (8123)     │
│ Whisper (faster-whisper)    │
│ Ollama (localhost:11434)    │
│ Web UI (Browser)            │
└─────────────────────────────┘
```

### Multi-Machine (LAN)

```
┌──────────────────┐        ┌──────────────────┐
│ Developer Laptop │        │   GPU Server     │
├──────────────────┤        ├──────────────────┤
│ Audio Client     │─────→  │ WebSocket Server │
│ Web UI (Browser) │←─────  │ Whisper (GPU)    │
│                  │        │ Ollama           │
└──────────────────┘        └──────────────────┘
```

### Docker (Production)

```
┌─────────────────────────────────┐
│    Docker Container             │
├─────────────────────────────────┤
│ Server (Port 8123)              │
│ Whisper                         │
│ Ollama (Via mounted volume)     │
│ Logging to stdout               │
│ Metrics endpoint (/metrics)     │
└─────────────────────────────────┘
```

---

## Scalability Considerations

### Vertical Scaling (More Powerful Hardware)

- ✅ Increase `MAX_CONCURRENT_LLM` for more answers
- ✅ Reduce `WINDOW_SECONDS` for faster transcription
- ✅ Use larger Whisper model for better accuracy
- ✅ Use faster LLM model for quicker responses

### Horizontal Scaling (Multiple Servers)

**Not currently designed for** but possible:
- Stateless server design (no persistent state per client)
- Session state could be moved to Redis
- Multiple servers behind load balancer
- Shared Ollama instance (or per-server)

### Resource Limits

| Resource | Single Server | Recommended |
|----------|---------------|-------------|
| **CPU Cores** | 2+ | 4+ |
| **Memory** | 2GB | 4-8GB |
| **GPU VRAM** | - | 4GB+ (for GPU inference) |
| **Concurrent LLM Requests** | 1-3 | 3-5 |
| **Connected Clients** | 10+ | 50+ |

---

## Monitoring & Observability

### Key Metrics to Monitor

```
Real-Time Dashboard:
────────────────────

Latency Metrics (p50, p95, p99):
  • Transcription latency
  • Question detection latency
  • Answer generation latency
  • End-to-end latency

Throughput Metrics:
  • Questions per minute
  • Answers per minute
  • Audio chunks processed per second

Resource Metrics:
  • Memory usage
  • CPU usage
  • GPU utilization (if available)

Error Metrics:
  • Transcription errors
  • LLM failures
  • Connection failures
```

### Health Checks

```python
# Server health endpoint
GET /health
→ {
    "status": "healthy",
    "transcription": "available",
    "ollama": "available",
    "uptime_seconds": 3600
  }
```

---

## Development Guidelines

### Adding a New Plugin

1. Create a class implementing the appropriate interface
2. Register in `src/plugins/__init__.py`
3. Add tests in `tests/`
4. Update documentation
5. Follow coding standards (type hints, docstrings)

### Performance Tuning

For each change:
1. Measure end-to-end latency
2. Check resource usage
3. Verify no regressions
4. Document trade-offs

### Testing Requirements

- Unit tests for components
- Integration tests for workflows
- Performance tests for latency
- Edge case tests for error handling

---

## Conclusion

Interview Assistant's architecture is designed for:
- **Performance**: <4s end-to-end latency
- **Modularity**: Plugin-based, swappable components
- **Reliability**: Graceful degradation, error recovery
- **Privacy**: Local-first, extensible for cloud integration
- **Maintainability**: Structured logging, clear interfaces

The system achieves these goals through thoughtful separation of concerns, async/await concurrency, and a flexible plugin architecture that allows customization without modifications to core code.

---

*For questions or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md)*
