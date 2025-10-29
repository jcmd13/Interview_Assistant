# Interview Assistant - Master Implementation Roadmap

**Version**: 1.0
**Created**: 2025-10-28
**Timeline**: 17 weeks (Aggressive)
**Strategy**: Foundation-First, Incremental Evolution with Feature Flags

---

## Executive Summary

This roadmap transforms Interview_Assistant from a functional MVP prototype into a production-ready, modular system with plugin architecture, card-based UI, advanced audio features, and comprehensive performance monitoring. The plan prioritizes architectural quality while maintaining backward compatibility through feature flags.

**Current State**: Monolithic prototype (~25% of vision complete)
**Target State**: Modular, testable, production-ready system (~85% of vision complete)

**Core Principles**:
- Foundation before features (logging, testing, plugins first)
- Incremental refactoring (never break existing functionality)
- Test-during development (add tests as we refactor)
- Feature flags for migration (old and new coexist)
- Performance-first (<4s end-to-end latency maintained)
- Enterprise-ready groundwork (without over-engineering)

---

## Timeline Overview

```
Weeks 1-4:   Phase 1 - Foundation & Infrastructure
Weeks 5-8:   Phase 2 - Plugin Architecture Core
Weeks 9-13:  Phase 3 - UI Refactor & Advanced Audio Features
Weeks 14-17: Phase 4 - Performance Monitoring & Production Polish
```

**Total Duration**: 17 weeks (aggressive timeline)
**Commitment**: Full-time focus, daily progress
**Success Metric**: End-to-end latency <4s (p95) maintained throughout

---

## Phase 1: Foundation & Infrastructure (Weeks 1-4)

**Goal**: Establish production-grade foundation without breaking existing functionality

### Week 1: Structured Logging & Configuration

#### Tasks

**1.1 Implement Structured Logging System** (Days 1-3)
- [ ] Install logging library (`structlog` or custom JSON logger)
- [ ] Create `src/core/logger.py` with structured logger factory
- [ ] Define log schema: `{timestamp, level, component, message, metadata}`
- [ ] Add component-specific loggers (transcription, llm, websocket, audio)
- [ ] Add timing decorators for latency tracking
- [ ] Implement log level configuration (DEBUG, INFO, WARNING, ERROR)
- [ ] Add request ID tracking for tracing requests end-to-end

**Success Criteria**:
- All `print()` statements in server replaced with structured logs
- Every log entry includes timing metadata
- Can filter logs by component/level
- Request tracing works end-to-end

**Files Created**:
- `src/core/logger.py` - Structured logging system
- `src/core/timing.py` - Latency tracking decorators

**Example Log Output**:
```json
{
  "timestamp": "2025-10-28T10:30:45.123Z",
  "level": "INFO",
  "component": "transcription.whisper",
  "message": "Transcription completed",
  "metadata": {
    "audio_duration_ms": 3200,
    "processing_time_ms": 450,
    "model": "base",
    "word_count": 42,
    "request_id": "req_abc123"
  }
}
```

---

**1.2 Build Configuration Management System** (Days 4-5)
- [ ] Create `src/core/config.py` with config loader
- [ ] Implement priority hierarchy: hardcoded defaults → .env → env vars → runtime
- [ ] Add pydantic schemas for type-safe configuration
- [ ] Load `.env` file using `python-dotenv`
- [ ] Add validation for all config values (ranges, types, dependencies)
- [ ] Create `ConfigManager` singleton for runtime access
- [ ] Document all configuration options in `.env.example`
- [ ] Add config hot-reload mechanism (for development)

**Success Criteria**:
- `.env.example` actually works when copied to `.env`
- All hardcoded constants moved to config system
- Invalid configs rejected with clear error messages
- Can override any config via environment variable
- Config changes logged at startup

**Files Created**:
- `src/core/config.py` - Configuration management
- `src/core/schemas.py` - Pydantic config schemas

**Example Config Schema**:
```python
class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(8123, ge=1024, le=65535)

class WhisperConfig(BaseModel):
    model_name: str = Field("base", pattern="^(tiny|base|small|medium|large)$")
    device: str = Field("cpu", pattern="^(cpu|cuda)$")
    compute_type: str = "int8"

class OllamaConfig(BaseModel):
    host: str = "http://localhost:11434"
    model_cloud: str = "gpt-oss:120b-cloud"
    timeout: int = Field(30, ge=5, le=300)
```

---

**1.3 Project Structure Reorganization** (Day 6)
- [ ] Create modular directory structure:
  ```
  src/
    core/           # Shared infrastructure
      __init__.py
      logger.py
      config.py
      schemas.py
      timing.py
    transcription/  # Transcription components
      __init__.py
      whisper.py    # Whisper implementation (future plugin)
    llm/            # LLM components
      __init__.py
      ollama.py     # Ollama implementation (future plugin)
      analyzer.py   # Question detection logic
    audio/          # Audio processing
      __init__.py
      buffer.py     # Audio buffer management
      processor.py  # Audio quality/preprocessing (Phase 3)
    server/         # WebSocket server
      __init__.py
      handlers.py   # WebSocket handlers
      state.py      # Global state management
    client/         # Audio client (stays standalone for now)
    ui/             # Web UI (stays standalone for now)
    plugins/        # Plugin system (Phase 2)
  tests/            # Test suite
    unit/
    integration/
  scripts/          # Utility scripts
  ```
- [ ] Move `optimized_stt_server_v3.py` logic into modular structure
- [ ] Create `server.py` entry point that imports from `src/`
- [ ] Keep `optimized_stt_server_v3.py` as legacy entry point (feature flag)
- [ ] Update import paths throughout
- [ ] Add `__init__.py` files for proper package structure

**Success Criteria**:
- Old entry point still works: `python optimized_stt_server_v3.py`
- New entry point works: `python server.py`
- Both use same underlying code (no duplication)
- Imports follow clean hierarchy (no circular dependencies)

**Files Created**:
- Entire `src/` directory structure
- `server.py` - New modular entry point
- `src/core/__init__.py` - Core package init

---

**1.4 Testing Infrastructure Setup** (Day 7)
- [ ] Install pytest, pytest-asyncio, pytest-cov, pytest-mock
- [ ] Create `tests/` directory structure
- [ ] Set up `pytest.ini` configuration
- [ ] Create `conftest.py` with common fixtures
- [ ] Add GitHub Actions workflow for CI (optional but recommended)
- [ ] Create `Makefile` with common commands (test, lint, run)
- [ ] Write first smoke tests (imports work, config loads, logger initializes)

**Success Criteria**:
- `make test` runs all tests successfully
- `make coverage` shows coverage report
- CI runs on every push (if GitHub Actions configured)
- Coverage baseline established (starting point for improvement)

**Files Created**:
- `tests/conftest.py` - Pytest fixtures
- `pytest.ini` - Pytest configuration
- `Makefile` - Development shortcuts
- `.github/workflows/ci.yml` - CI pipeline (optional)
- `tests/unit/test_config.py` - Config tests
- `tests/unit/test_logger.py` - Logger tests

**Example Makefile**:
```makefile
.PHONY: test coverage lint run clean

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/

run:
	python server.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov
```

---

### Week 2: State Management & Error Handling

#### Tasks

**2.1 Encapsulate Global State** (Days 1-2)
- [ ] Create `src/server/state.py` with `ApplicationState` class
- [ ] Move global variables into state manager:
  - `transcript_lines` → `state.transcript`
  - `detected` → `state.detected_questions`
  - `qa_log` → `state.answered_questions`
  - `ws_clients` → `state.websocket_clients`
- [ ] Add state access methods (getters/setters)
- [ ] Implement state persistence hooks (for future database)
- [ ] Add state snapshot/restore for testing
- [ ] Add thread-safe locking for state mutations
- [ ] Create state observers pattern for UI updates

**Success Criteria**:
- No global state variables in server code
- All state accessed through `ApplicationState` instance
- State can be serialized to JSON
- Multiple state instances can coexist (for testing)
- State mutations are thread-safe

**Files Created**:
- `src/server/state.py` - State management
- `tests/unit/test_state.py` - State tests

**Example State Manager**:
```python
class ApplicationState:
    def __init__(self):
        self._transcript: List[str] = []
        self._detected: deque = deque(maxlen=50)
        self._qa_log: List[Dict] = []
        self._lock = asyncio.Lock()
        self._observers: List[Callable] = []

    async def add_transcript_line(self, text: str):
        async with self._lock:
            self._transcript.append(text)
            await self._notify_observers("transcript", text)

    def snapshot(self) -> Dict:
        """Serialize state for persistence"""
        return {
            "transcript": self._transcript,
            "detected": list(self._detected),
            "qa_log": self._qa_log
        }
```

---

**2.2 Implement Error Handling Framework** (Days 3-4)
- [ ] Create `src/core/errors.py` with custom exception hierarchy
- [ ] Define exception types:
  - `TranscriptionError` - Whisper failures
  - `LLMError` - Ollama failures
  - `AudioError` - Audio buffer/streaming issues
  - `ConfigError` - Configuration validation failures
- [ ] Add error context (request_id, timestamp, component)
- [ ] Create error handlers with retry logic
- [ ] Implement circuit breaker pattern for external services
- [ ] Add user-friendly error messages (separate from technical logs)
- [ ] Create error recovery strategies (fallback models, skip, retry)

**Success Criteria**:
- All exceptions inherit from custom base exception
- Every error includes context (component, request_id, timestamp)
- Circuit breaker prevents cascading Ollama failures
- User sees actionable messages, not stack traces
- Errors logged with full technical details

**Files Created**:
- `src/core/errors.py` - Exception hierarchy
- `src/core/circuit_breaker.py` - Circuit breaker pattern
- `src/core/retry.py` - Retry decorators
- `tests/unit/test_errors.py` - Error handling tests

**Example Error Hierarchy**:
```python
class InterviewAssistantError(Exception):
    """Base exception with context"""
    def __init__(self, message: str, component: str, request_id: str = None):
        self.message = message
        self.component = component
        self.request_id = request_id
        self.timestamp = datetime.utcnow()

    def user_message(self) -> str:
        """User-friendly message"""
        return self.message

    def log_context(self) -> Dict:
        """Structured log context"""
        return {
            "error_type": self.__class__.__name__,
            "component": self.component,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat()
        }

class LLMError(InterviewAssistantError):
    def user_message(self) -> str:
        return "AI service temporarily unavailable. Retrying..."
```

---

**2.3 Add Input Validation** (Day 5)
- [ ] Create `src/core/validation.py` with validators
- [ ] Validate WebSocket messages (JSON schema)
- [ ] Validate audio data (format, sample rate, size limits)
- [ ] Validate configuration values (pydantic already handles this)
- [ ] Add rate limiting for WebSocket connections
- [ ] Sanitize transcript text (XSS prevention for future web features)
- [ ] Add max payload size limits

**Success Criteria**:
- Invalid WebSocket messages rejected with clear error
- Malformed audio data doesn't crash server
- Rate limiting prevents abuse
- All user inputs validated before processing

**Files Created**:
- `src/core/validation.py` - Input validators
- `src/server/rate_limiter.py` - Rate limiting
- `tests/unit/test_validation.py` - Validation tests

---

**2.4 Dependency Injection Preparation** (Days 6-7)
- [ ] Create abstract base classes (protocols) for future plugins:
  - `TranscriberProtocol` - Abstract transcription interface
  - `LLMProviderProtocol` - Abstract LLM interface
  - `AudioSourceProtocol` - Abstract audio source interface
  - `AudioProcessorProtocol` - Abstract audio preprocessing interface (Phase 3)
  - `StorageProtocol` - Abstract storage interface
- [ ] Refactor existing implementations to match protocols
- [ ] Create dependency container (`src/core/container.py`)
- [ ] Pass dependencies via constructor (not hardcoded imports)
- [ ] Add factory functions for creating configured instances

**Success Criteria**:
- All external dependencies accessed via protocols
- No hardcoded `import ollama` in business logic
- Can swap implementations for testing (mocks)
- Dependency graph is explicit and documented

**Files Created**:
- `src/core/protocols.py` - Abstract interfaces
- `src/core/container.py` - Dependency injection container
- `tests/unit/test_container.py` - DI tests

**Example Protocol**:
```python
from typing import Protocol, List

class TranscriberProtocol(Protocol):
    async def transcribe(self, audio: bytes) -> str:
        """Transcribe audio bytes to text"""
        ...

    @property
    def model_name(self) -> str:
        """Return model identifier"""
        ...

class AudioProcessorProtocol(Protocol):
    async def process(self, audio: bytes) -> bytes:
        """Process/clean audio (noise reduction, normalization)"""
        ...

class WhisperTranscriber:
    """Concrete implementation"""
    def __init__(self, model_name: str, device: str):
        self.model = WhisperModel(model_name, device=device)
        self._model_name = model_name

    async def transcribe(self, audio: bytes) -> str:
        # Implementation
        ...

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### Week 3: Component Extraction & Testing

#### Tasks

**3.1 Extract Transcription Component** (Days 1-2)
- [ ] Move Whisper logic to `src/transcription/whisper.py`
- [ ] Implement `TranscriberProtocol` interface
- [ ] Extract audio buffer logic to `src/audio/buffer.py`
- [ ] Add configuration for transcription (model, device, window size)
- [ ] Create unit tests with mocked Whisper model
- [ ] Add integration tests with real Whisper (small model)
- [ ] Measure and log transcription latency

**Success Criteria**:
- Transcription logic fully independent from server
- Can instantiate transcriber in tests without WebSocket
- Audio buffer tested separately (unit tests)
- Transcription latency logged on every request
- Test coverage >80% for transcription module

**Files Created**:
- `src/transcription/whisper.py` - Whisper implementation
- `src/audio/buffer.py` - Audio buffer management
- `tests/unit/test_transcription.py` - Transcription tests
- `tests/integration/test_whisper_integration.py` - Full Whisper tests

---

**3.2 Extract LLM Component** (Days 3-4)
- [ ] Move Ollama logic to `src/llm/ollama.py`
- [ ] Implement `LLMProviderProtocol` interface
- [ ] Extract question analyzer to `src/llm/analyzer.py`
- [ ] Add retry logic with exponential backoff
- [ ] Create mock LLM for testing
- [ ] Add unit tests for question detection logic
- [ ] Add integration tests with real Ollama
- [ ] Measure and log LLM latency

**Success Criteria**:
- LLM logic fully independent from server
- Can test question detection without Ollama running
- Mock LLM returns deterministic responses for tests
- LLM latency logged on every request
- Test coverage >80% for LLM module

**Files Created**:
- `src/llm/ollama.py` - Ollama implementation
- `src/llm/analyzer.py` - Question detection
- `src/llm/base.py` - Base LLM provider class
- `tests/unit/test_llm.py` - LLM tests
- `tests/integration/test_ollama_integration.py` - Full Ollama tests
- `tests/fixtures/mock_llm.py` - Mock LLM for testing

---

**3.3 Extract WebSocket Server Component** (Days 5-6)
- [ ] Move WebSocket handlers to `src/server/handlers.py`
- [ ] Separate client management to `src/server/clients.py`
- [ ] Extract broadcast logic to `src/server/broadcast.py`
- [ ] Add WebSocket protocol documentation
- [ ] Create WebSocket client mock for testing
- [ ] Add unit tests for message handling
- [ ] Add integration tests for full WebSocket flow

**Success Criteria**:
- WebSocket logic fully independent
- Can test handlers without running server
- Mock WebSocket client for automated testing
- Protocol fully documented
- Test coverage >80% for server module

**Files Created**:
- `src/server/handlers.py` - WebSocket handlers
- `src/server/clients.py` - Client management
- `src/server/broadcast.py` - Broadcast logic
- `tests/unit/test_server.py` - Server tests
- `tests/fixtures/mock_websocket.py` - Mock WebSocket client

---

**3.4 Integration Testing & Documentation** (Day 7)
- [ ] Create end-to-end integration test (audio → answer)
- [ ] Measure baseline performance (latency p50, p95, p99)
- [ ] Document new architecture in `docs/ARCHITECTURE.md`
- [ ] Create dependency graph diagram
- [ ] Update CLAUDE.md to reflect current implementation
- [ ] Add developer onboarding guide

**Success Criteria**:
- End-to-end test passes consistently
- Baseline performance documented (<4s end-to-end p95)
- New developers can understand architecture from docs
- Architecture diagram generated and committed

**Files Created**:
- `tests/integration/test_end_to_end.py` - Full system test
- `docs/ARCHITECTURE.md` - Architecture documentation
- `docs/DEVELOPER_GUIDE.md` - Developer onboarding
- `docs/diagrams/architecture.png` - Architecture diagram
- `docs/PERFORMANCE_BASELINE.md` - Performance benchmarks

---

### Week 4: Feature Flags & Legacy Migration

#### Tasks

**4.1 Implement Feature Flag System** (Days 1-2)
- [ ] Create `src/core/features.py` with feature flag manager
- [ ] Add flags for:
  - `USE_NEW_ARCHITECTURE` - Use modular components
  - `USE_STRUCTURED_LOGGING` - JSON logs vs print
  - `USE_STATE_MANAGER` - State class vs globals
  - `ENABLE_PERFORMANCE_TRACKING` - Latency monitoring
  - `ENABLE_AUDIO_PREPROCESSING` - Advanced audio features (Phase 3)
- [ ] Load flags from environment variables
- [ ] Add runtime flag toggling (for development)
- [ ] Create flag documentation

**Success Criteria**:
- Can run server with old or new architecture via flag
- Flags configurable via environment variables
- Flag state logged at startup
- Gradual migration path clear

**Files Created**:
- `src/core/features.py` - Feature flag system
- `docs/FEATURE_FLAGS.md` - Flag documentation

---

**4.2 Migrate Server to New Architecture** (Days 3-5)
- [ ] Update `server.py` to use new modular components
- [ ] Implement dependency injection in main entry point
- [ ] Wire up all components via container
- [ ] Add feature flag checks for gradual rollout
- [ ] Test both old and new entry points
- [ ] Verify performance parity (new ≤ old latency)
- [ ] Fix any regressions

**Success Criteria**:
- `python server.py` works with new architecture
- `python optimized_stt_server_v3.py` still works (legacy)
- Performance identical or better
- All features working (transcription, Q&A, UI updates)

**Files Modified**:
- `server.py` - New modular entry point
- `optimized_stt_server_v3.py` - Legacy entry point (minimal changes)

---

**4.3 Database Schema Design** (Days 6-7)
- [ ] Design database schema for future persistence:
  - `users` - User profiles (for future multi-user)
  - `sessions` - Interview sessions
  - `transcripts` - Full transcript history
  - `questions` - Detected questions log
  - `answers` - Generated answers log
  - `performance_metrics` - Latency tracking
  - `audio_quality_metrics` - Audio quality stats (Phase 3)
- [ ] Create SQLAlchemy models in `src/storage/models.py`
- [ ] Add multi-tenancy support in schema (user_id foreign keys)
- [ ] Create migration system (Alembic)
- [ ] Add `StorageProtocol` implementation for SQLite
- [ ] Keep in-memory storage as default (feature flag)

**Success Criteria**:
- Schema supports current features + future multi-user
- Migration system set up and documented
- SQLite storage works behind feature flag
- In-memory storage still default (no breaking changes)

**Files Created**:
- `src/storage/models.py` - Database models
- `src/storage/sqlite.py` - SQLite implementation
- `src/storage/memory.py` - In-memory implementation
- `alembic/versions/001_initial_schema.py` - Initial migration
- `alembic.ini` - Alembic configuration
- `docs/DATABASE.md` - Schema documentation

**Example Schema (Multi-Tenant Ready)**:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    metadata = Column(JSON)

class AudioQualityMetric(Base):
    __tablename__ = "audio_quality_metrics"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    noise_level_db = Column(Float)
    signal_quality = Column(Float)
    sample_rate = Column(Integer)
```

---

### Phase 1 Deliverables

**Completed by End of Week 4**:
- ✅ Structured JSON logging throughout
- ✅ Configuration management system (loads .env, validates)
- ✅ Modular project structure (src/ directory)
- ✅ Testing infrastructure (pytest, CI, coverage)
- ✅ Encapsulated state management
- ✅ Error handling framework with circuit breakers
- ✅ Input validation and security hardening
- ✅ Dependency injection via protocols
- ✅ Extracted components (transcription, LLM, server)
- ✅ Feature flag system for migration
- ✅ Database schema designed (not yet used)
- ✅ Documentation (architecture, developer guide)
- ✅ Performance baseline established

**Success Metrics**:
- End-to-end latency maintained <4s (p95)
- Test coverage >80%
- Legacy server still works
- New modular server works
- Zero data loss during migration

---

## Phase 2: Plugin Architecture Core (Weeks 5-8)

**Goal**: Build plugin system with hot-swapping, registry, and example plugins

### Week 5: Plugin System Foundation

#### Tasks

**5.1 Design Plugin Architecture** (Days 1-2)
- [ ] Create plugin specification document
- [ ] Define plugin lifecycle (load, init, start, stop, unload)
- [ ] Design plugin metadata format (JSON/YAML manifest)
- [ ] Create plugin base class (`src/plugins/base.py`)
- [ ] Define plugin categories:
  - `TranscriberPlugin` - Speech-to-text implementations
  - `LLMPlugin` - Language model providers
  - `AudioSourcePlugin` - Audio input sources
  - `AudioProcessorPlugin` - Audio preprocessing (Phase 3)
  - `StoragePlugin` - Persistence backends
  - `UIPlugin` - UI extensions (future)
- [ ] Document plugin API

**Success Criteria**:
- Plugin specification documented
- Base plugin class provides lifecycle hooks
- Plugin categories clearly defined
- API stable and versioned

**Files Created**:
- `src/plugins/base.py` - Base plugin class
- `src/plugins/registry.py` - Plugin registry (Day 2)
- `docs/PLUGIN_DEVELOPMENT.md` - Plugin development guide
- `docs/PLUGIN_SPEC.md` - Plugin specification

**Example Plugin Manifest**:
```json
{
  "name": "whisper-transcriber",
  "version": "1.0.0",
  "category": "transcriber",
  "author": "Interview Assistant Team",
  "description": "faster-whisper based transcription",
  "entry_point": "whisper.WhisperPlugin",
  "dependencies": {
    "faster-whisper": ">=0.10.0"
  },
  "config_schema": {
    "model_name": {"type": "string", "default": "base"},
    "device": {"type": "string", "default": "cpu"}
  }
}
```

---

**5.2 Build Plugin Registry & Loader** (Days 3-4)
- [ ] Create plugin discovery mechanism (scan `plugins/` directory)
- [ ] Implement plugin loader with dependency validation
- [ ] Add plugin versioning and compatibility checks
- [ ] Create plugin instance cache
- [ ] Add plugin health checks (is plugin responsive?)
- [ ] Implement plugin unload/reload without server restart

**Success Criteria**:
- Plugins auto-discovered on server start
- Invalid plugins rejected with clear errors
- Plugin dependencies validated
- Can reload plugins without restart

**Files Created**:
- `src/plugins/loader.py` - Plugin loading logic
- `src/plugins/discovery.py` - Plugin discovery
- `tests/unit/test_plugins.py` - Plugin system tests

---

**5.3 Implement Hot-Swapping** (Days 5-6)
- [ ] Add plugin swap mechanism (stop old, start new)
- [ ] Ensure graceful handoff (no dropped requests)
- [ ] Add plugin configuration hot-reload
- [ ] Create plugin management API (list, enable, disable, reload)
- [ ] Add WebSocket API for plugin management (for future UI)

**Success Criteria**:
- Can swap LLM plugin without stopping server
- No in-flight requests lost during swap
- Configuration changes applied without restart
- Plugin management API fully functional

**Files Created**:
- `src/plugins/manager.py` - Plugin lifecycle management
- `src/server/plugin_api.py` - Plugin management endpoints
- `tests/integration/test_plugin_swapping.py` - Hot-swap tests

---

**5.4 Create Example Plugins** (Day 7)
- [ ] Convert existing Whisper implementation to plugin
- [ ] Convert existing Ollama implementation to plugin
- [ ] Create mock/stub plugins for testing
- [ ] Add plugin templates for developers
- [ ] Test plugin loading and swapping

**Success Criteria**:
- WhisperPlugin loads and works
- OllamaPlugin loads and works
- MockTranscriberPlugin works for testing
- Plugin template documented

**Files Created**:
- `src/plugins/transcriber/whisper_plugin.py` - Whisper plugin
- `src/plugins/llm/ollama_plugin.py` - Ollama plugin
- `src/plugins/templates/transcriber_template.py` - Template
- `tests/fixtures/plugins/mock_transcriber.py` - Mock plugin

---

### Week 6: Additional Plugins & Storage

#### Tasks

**6.1 Build Storage Plugin System** (Days 1-2)
- [ ] Create `StoragePlugin` base class
- [ ] Implement `MemoryStoragePlugin` (current behavior)
- [ ] Implement `SQLiteStoragePlugin` (uses schema from Week 4)
- [ ] Add storage plugin configuration
- [ ] Add data migration tools (memory → SQLite)
- [ ] Keep memory storage as default

**Success Criteria**:
- Storage backend swappable via config
- SQLite storage persists sessions/transcripts
- Data migration works correctly
- Memory storage still default (no breaking changes)

**Files Created**:
- `src/plugins/storage/memory_plugin.py` - Memory storage
- `src/plugins/storage/sqlite_plugin.py` - SQLite storage
- `src/storage/migration.py` - Data migration utilities
- `tests/integration/test_storage_plugins.py` - Storage tests

---

**6.2 Build Audio Source Plugin System** (Days 3-4)
- [ ] Create `AudioSourcePlugin` base class
- [ ] Implement `FFmpegAudioPlugin` (wraps existing client)
- [ ] Create `FileAudioPlugin` for testing (reads from audio file)
- [ ] Add audio source selection in config
- [ ] Test audio source swapping

**Success Criteria**:
- Audio source swappable via config
- FileAudioPlugin allows testing without microphone
- FFmpegAudioPlugin maintains compatibility with existing client

**Files Created**:
- `src/plugins/audio/ffmpeg_plugin.py` - FFmpeg audio source
- `src/plugins/audio/file_plugin.py` - File-based audio source
- `tests/integration/test_audio_plugins.py` - Audio source tests

---

**6.3 Add OpenAI/Anthropic LLM Plugins (Groundwork)** (Days 5-6)
- [ ] Create `OpenAIPlugin` with API key configuration
- [ ] Create `AnthropicPlugin` with API key configuration
- [ ] Implement credential storage in OS keychain (macOS: Keychain, Linux: Secret Service)
- [ ] Add LLM fallback chain configuration
- [ ] Test OpenAI/Anthropic plugins (if user has keys)
- [ ] Keep Ollama as default (no required API keys)

**Success Criteria**:
- OpenAI plugin works with valid API key
- Anthropic plugin works with valid API key
- API keys stored securely (not in .env or code)
- Fallback chain works (Cloud API fails → Ollama)
- No API keys required for default setup

**Files Created**:
- `src/plugins/llm/openai_plugin.py` - OpenAI integration
- `src/plugins/llm/anthropic_plugin.py` - Anthropic integration
- `src/core/credentials.py` - Secure credential storage
- `tests/integration/test_llm_plugins.py` - LLM plugin tests

**Example Credential Storage**:
```python
import keyring

class CredentialManager:
    SERVICE_NAME = "interview-assistant"

    def set_api_key(self, provider: str, api_key: str):
        """Store API key in OS keychain"""
        keyring.set_password(self.SERVICE_NAME, f"{provider}_api_key", api_key)

    def get_api_key(self, provider: str) -> str | None:
        """Retrieve API key from OS keychain"""
        return keyring.get_password(self.SERVICE_NAME, f"{provider}_api_key")
```

---

**6.4 Plugin Documentation & Testing** (Day 7)
- [ ] Complete plugin development guide
- [ ] Add plugin examples to documentation
- [ ] Create plugin testing guide
- [ ] Add plugin contribution guidelines
- [ ] Test all plugins end-to-end

**Success Criteria**:
- Developer can create new plugin from guide
- All plugins tested and working
- Plugin testing documented
- Contribution guidelines clear

**Files Updated**:
- `docs/PLUGIN_DEVELOPMENT.md` - Complete guide
- `docs/PLUGIN_EXAMPLES.md` - Example plugins
- `docs/CONTRIBUTING.md` - Contribution guide

---

### Week 7: Performance Monitoring Foundation

#### Tasks

**7.1 Build Performance Tracking System** (Days 1-3)
- [ ] Create `src/core/metrics.py` with metrics collector
- [ ] Track latency for each pipeline stage:
  - Audio capture → transcription
  - Transcription → question detection
  - Question detection → LLM call
  - LLM call → answer displayed
  - **Total end-to-end latency**
  - Audio preprocessing latency (Phase 3)
- [ ] Calculate percentiles (p50, p95, p99)
- [ ] Add rolling window statistics (last 100 requests)
- [ ] Create metrics export (JSON, CSV, Prometheus format)
- [ ] Add real-time metrics WebSocket stream (for UI)

**Success Criteria**:
- Every request tracked end-to-end
- Latency percentiles calculated accurately
- Metrics exportable to file
- Real-time metrics stream works

**Files Created**:
- `src/core/metrics.py` - Metrics collection
- `src/core/percentiles.py` - Percentile calculations
- `src/server/metrics_api.py` - Metrics API endpoints
- `tests/unit/test_metrics.py` - Metrics tests

**Example Metrics**:
```json
{
  "timestamp": "2025-10-28T10:30:45Z",
  "request_id": "req_abc123",
  "pipeline_stages": {
    "audio_capture_ms": 50,
    "audio_preprocessing_ms": 30,
    "transcription_ms": 450,
    "question_detection_ms": 80,
    "llm_generation_ms": 2100,
    "total_end_to_end_ms": 2710
  },
  "metadata": {
    "model": "gpt-oss:120b-cloud",
    "audio_duration_ms": 3200,
    "word_count": 42
  }
}
```

---

**7.2 Add Latency Budgets & Alerts** (Days 4-5)
- [ ] Define latency budgets per component:
  - Audio preprocessing: <50ms (Phase 3)
  - Transcription: <500ms
  - Question detection: <100ms
  - LLM generation: <3s
  - End-to-end: <4s (p95)
- [ ] Add budget violation detection
- [ ] Log warnings when budgets exceeded
- [ ] Create performance report generation
- [ ] Add performance regression detection (compare to baseline)

**Success Criteria**:
- Latency budgets enforced
- Violations logged with context
- Performance reports generated
- Regressions detected automatically

**Files Created**:
- `src/core/budgets.py` - Latency budget enforcement
- `src/core/reports.py` - Performance reporting
- `docs/PERFORMANCE.md` - Performance documentation

---

**7.3 Resource Monitoring** (Days 6-7)
- [ ] Track CPU usage per component
- [ ] Track memory usage (current, peak)
- [ ] Track GPU usage (if CUDA available)
- [ ] Monitor Ollama connection health
- [ ] Add system health endpoint (`/health`)
- [ ] Create health check CLI tool

**Success Criteria**:
- Resource usage tracked and logged
- Health endpoint returns system status
- Can diagnose bottlenecks from metrics
- Health checks automated

**Files Created**:
- `src/core/resources.py` - Resource monitoring
- `src/server/health.py` - Health endpoint
- `scripts/health_check.py` - CLI health checker
- `tests/integration/test_health.py` - Health tests

---

### Week 8: Performance Optimization & Phase 2 Review

#### Tasks

**8.1 Identify & Fix Bottlenecks** (Days 1-3)
- [ ] Analyze metrics from Phase 2 development
- [ ] Profile slow components (cProfile, py-spy)
- [ ] Optimize hot paths identified in profiling
- [ ] Reduce memory allocations in audio buffer
- [ ] Optimize LLM prompt building (reduce token count)
- [ ] Add caching where appropriate (term definitions, etc.)

**Success Criteria**:
- Latency maintained or improved vs Phase 1
- No memory leaks detected
- Bottlenecks identified and addressed
- Performance improvements measured

---

**8.2 End-to-End Performance Testing** (Days 4-5)
- [ ] Create performance test suite with real audio
- [ ] Measure latency under various conditions:
  - Different Whisper models (tiny, base, small)
  - Different LLM models (cloud vs local)
  - Different audio durations
  - Multiple concurrent sessions
- [ ] Generate performance report comparing configurations
- [ ] Update performance baseline

**Success Criteria**:
- Performance test suite automated
- Latency measured for all configurations
- Optimal configuration identified
- Performance report generated

**Files Created**:
- `tests/performance/test_latency.py` - Performance tests
- `tests/performance/audio_samples/` - Test audio files
- `docs/PERFORMANCE_REPORT.md` - Performance report

---

**8.3 Plugin System Documentation & Examples** (Day 6)
- [ ] Create complete plugin tutorial
- [ ] Add video/screencast of plugin development (optional)
- [ ] Create plugin gallery (README with all available plugins)
- [ ] Add plugin contribution guidelines
- [ ] Create plugin template repository (cookiecutter)

**Success Criteria**:
- External developer can create plugin from tutorial
- Plugin gallery showcases available plugins
- Template repository works (cookiecutter)

**Files Created**:
- `docs/PLUGIN_TUTORIAL.md` - Step-by-step tutorial
- `docs/PLUGIN_GALLERY.md` - Available plugins
- `cookiecutter-interview-assistant-plugin/` - Template repo

---

**8.4 Phase 2 Review & Planning** (Day 7)
- [ ] Review all Phase 2 deliverables
- [ ] Test backward compatibility with Phase 1
- [ ] Measure performance vs baseline
- [ ] Update CLAUDE.md with current state
- [ ] Plan Phase 3 priorities based on learnings

**Success Criteria**:
- All Phase 2 deliverables complete
- Performance maintained <4s end-to-end
- Backward compatibility verified
- Phase 3 plan ready

---

### Phase 2 Deliverables

**Completed by End of Week 8**:
- ✅ Plugin system with hot-swapping
- ✅ Plugin registry and loader
- ✅ Transcriber plugins (Whisper)
- ✅ LLM plugins (Ollama, OpenAI, Anthropic)
- ✅ Storage plugins (Memory, SQLite)
- ✅ Audio source plugins (FFmpeg, File)
- ✅ Secure credential storage (OS keychain)
- ✅ Performance monitoring system
- ✅ Latency tracking and budgets
- ✅ Resource monitoring
- ✅ Health checks and status API
- ✅ Plugin development guide and templates

**Success Metrics**:
- End-to-end latency <4s (p95)
- Plugin swap <1s with no dropped requests
- Test coverage >80%
- 5+ working plugins
- Performance regression detection working

---

## Phase 3: UI Refactor & Advanced Audio Features (Weeks 9-13)

**Goal**: Build card-based modular UI with drag-and-drop, layout presets, and implement advanced audio features (speaker detection, noise cancellation, quality monitoring)

### Week 9: UI Architecture Design

#### Tasks

**9.1 Design Card-Based UI System** (Days 1-2)
- [ ] Design card component architecture
- [ ] Define card types:
  - `TranscriptCard` - Live transcript stream
  - `AnswerDetailCard` - Selected Q&A detail view
  - `QAListCard` - Questions & answers list
  - `PerformanceCard` - Real-time performance metrics
  - `AudioQualityCard` - Audio quality monitoring (new)
  - `ConfigCard` - Runtime configuration (future)
  - `PluginCard` - Plugin management (future)
- [ ] Design grid layout system (20rem columns × 1rem rows)
- [ ] Design drag-and-drop interaction model
- [ ] Create layout preset specifications:
  - **Interview Stealth** - Minimal, high-density
  - **Phone Call** - Mobile-optimized, large text
  - **Business Meeting** - Balanced, professional
  - **Customer Call** - CRM context + transcript
  - **Audio Debug** - Focus on audio quality metrics (new)
- [ ] Document UI architecture

**Success Criteria**:
- Card system designed and documented
- Layout presets defined
- Interaction model clear
- Architecture documented

**Files Created**:
- `docs/UI_ARCHITECTURE.md` - UI design document
- `docs/CARD_SPECIFICATION.md` - Card component spec
- `docs/LAYOUT_PRESETS.md` - Layout preset definitions

---

**9.2 Set Up Modern UI Build System** (Days 3-4)
- [ ] Decision: Vanilla JS with Web Components (recommended for zero deps)
- [ ] Set up build tooling (optional):
  - Vite for dev server + bundling (optional)
  - TypeScript for type safety (optional)
- [ ] Create component structure:
  ```
  src/ui/
    components/
      cards/
        transcript-card.js
        answer-card.js
        qa-list-card.js
        performance-card.js
        audio-quality-card.js  # New
      layout/
        grid-layout.js
        card-container.js
    core/
      websocket-client.js
      state-manager.js
      event-bus.js
    styles/
      base.css
      cards.css
      layout.css
  ```
- [ ] Create development environment

**Success Criteria**:
- UI build system working (if applicable)
- Component structure created
- Dev server running with hot reload
- Decision documented (vanilla vs framework)

**Files Created**:
- `src/ui/package.json` - UI dependencies (if needed)
- `src/ui/vite.config.js` - Build config (if using Vite)
- `docs/UI_DEVELOPMENT.md` - UI development guide

---

**9.3 Build Grid Layout System** (Days 5-7)
- [ ] Implement CSS Grid-based layout engine
- [ ] Add 20rem column × 1rem row grid
- [ ] Implement responsive breakpoints
- [ ] Add card positioning logic (x, y, width, height in grid units)
- [ ] Add layout serialization (save to localStorage)
- [ ] Add layout restoration on page load
- [ ] Test layout on different screen sizes

**Success Criteria**:
- Grid layout renders correctly
- Cards snap to grid
- Layout persists across page reloads
- Responsive on mobile/tablet/desktop

**Files Created**:
- `src/ui/components/layout/grid-layout.js` - Grid system
- `src/ui/core/layout-storage.js` - Layout persistence
- `src/ui/styles/layout.css` - Grid styles
- `tests/ui/test_layout.html` - Layout tests

---

### Week 10: Card Components & Drag-and-Drop

#### Tasks

**10.1 Build Card Base Component** (Days 1-2)
- [ ] Create base card web component
- [ ] Add card header (title, minimize/maximize, close)
- [ ] Add card resize handles
- [ ] Add card styling (borders, shadows, themes)
- [ ] Add card state management (minimized, maximized, normal)
- [ ] Add card animations (smooth transitions)

**Success Criteria**:
- Base card renders correctly
- Card interactions work (minimize, maximize, close)
- Card resizable via handles
- Animations smooth

**Files Created**:
- `src/ui/components/cards/base-card.js` - Base card component
- `src/ui/styles/cards.css` - Card styles

---

**10.2 Implement Drag-and-Drop** (Days 3-4)
- [ ] Add drag handles to cards
- [ ] Implement drag start/move/end logic
- [ ] Add snap-to-grid behavior
- [ ] Add collision detection (prevent overlap)
- [ ] Add drop preview (show where card will land)
- [ ] Add touch support (mobile drag-and-drop)
- [ ] Optimize performance (use requestAnimationFrame)

**Success Criteria**:
- Cards draggable via handles
- Snap-to-grid works smoothly
- No card overlap allowed
- Touch drag works on mobile
- Performance smooth (60fps)

**Files Created**:
- `src/ui/core/drag-drop.js` - Drag-and-drop logic
- `src/ui/core/collision.js` - Collision detection
- `tests/ui/test_drag_drop.html` - D&D tests

---

**10.3 Build Transcript Card** (Days 5-6)
- [ ] Port transcript display from old UI
- [ ] Add auto-scroll toggle
- [ ] Add search/filter functionality
- [ ] Add export button (save transcript)
- [ ] Add speaker labels (for Phase 3 speaker detection)
- [ ] Add timestamps
- [ ] Test with live WebSocket data

**Success Criteria**:
- Transcript card displays live data
- Auto-scroll works
- Search/filter functional
- Export works
- Performance good with 1000+ lines

**Files Created**:
- `src/ui/components/cards/transcript-card.js` - Transcript card
- `tests/ui/test_transcript_card.html` - Card tests

---

**10.4 Build Q&A List Card** (Day 7)
- [ ] Port Q&A list from old UI
- [ ] Add question selection logic
- [ ] Add keyboard shortcuts (j/k navigation)
- [ ] Add Q&A export
- [ ] Add filtering (answered/unanswered)
- [ ] Test with live WebSocket data

**Success Criteria**:
- Q&A list displays live data
- Selection works
- Keyboard shortcuts work
- Export functional

**Files Created**:
- `src/ui/components/cards/qa-list-card.js` - Q&A list card
- `tests/ui/test_qa_list_card.html` - Card tests

---

### Week 11: Performance Card & Answer Card

#### Tasks

**11.1 Build Performance Monitoring Card** (Days 1-3)
- [ ] Create real-time performance dashboard card
- [ ] Display current latency (end-to-end)
- [ ] Display percentiles (p50, p95, p99)
- [ ] Display resource usage (CPU, memory, GPU)
- [ ] Add latency timeline chart (last 100 requests)
- [ ] Add component breakdown (transcription, audio preprocessing, LLM, etc.)
- [ ] Add health status indicators
- [ ] Add export performance report button

**Success Criteria**:
- Performance card displays real-time metrics
- Charts update smoothly
- Component breakdown visible
- Export works

**Files Created**:
- `src/ui/components/cards/performance-card.js` - Performance card
- `src/ui/core/charts.js` - Charting utilities (or use lightweight lib)
- `tests/ui/test_performance_card.html` - Card tests

---

**11.2 Build Answer Detail Card** (Days 4-5)
- [ ] Port answer detail view from old UI
- [ ] Add markdown rendering (for formatted answers)
- [ ] Add copy button (copy answer to clipboard)
- [ ] Add regenerate button (ask LLM again)
- [ ] Add answer rating (thumbs up/down for future learning)
- [ ] Test with various answer formats

**Success Criteria**:
- Answer detail displays correctly
- Markdown renders properly
- Copy/regenerate work
- Rating captured

**Files Created**:
- `src/ui/components/cards/answer-card.js` - Answer detail card
- `src/ui/core/markdown.js` - Markdown rendering
- `tests/ui/test_answer_card.html` - Card tests

---

**11.3 Implement Layout Presets** (Days 6-7)
- [ ] Create layout preset system
- [ ] Implement presets:
  - **Interview Stealth**: Minimal UI, high density, small cards
  - **Phone Call**: Mobile-optimized, large fonts, essential cards only
  - **Business Meeting**: Balanced layout, professional appearance
  - **Performance Debug**: Focus on metrics, detailed performance view
  - **Audio Debug**: Focus on audio quality monitoring (new)
- [ ] Add preset selector UI (dropdown or buttons)
- [ ] Add custom preset saving (save current layout as preset)
- [ ] Add preset import/export (share layouts)

**Success Criteria**:
- All 5 presets work
- Preset switching smooth (<500ms)
- Custom presets saveable
- Import/export functional

**Files Created**:
- `src/ui/core/presets.js` - Layout preset system
- `src/ui/data/presets.json` - Default presets
- `src/ui/components/preset-selector.js` - Preset UI
- `docs/LAYOUT_PRESETS.md` - Preset documentation

**Example Preset Definition**:
```json
{
  "name": "Audio Debug",
  "description": "Focus on audio quality and preprocessing metrics",
  "cards": [
    {
      "type": "audio-quality",
      "position": {"x": 0, "y": 0, "width": 10, "height": 15},
      "minimized": false
    },
    {
      "type": "performance",
      "position": {"x": 10, "y": 0, "width": 10, "height": 15},
      "minimized": false
    },
    {
      "type": "transcript",
      "position": {"x": 0, "y": 15, "width": 20, "height": 10},
      "minimized": false,
      "config": {"showSpeakerLabels": true}
    }
  ]
}
```

---

### Week 12: Advanced Audio Features - Part 1

#### Tasks

**12.1 Implement Audio Quality Monitoring** (Days 1-2)
- [ ] Create `src/audio/quality.py` for audio analysis
- [ ] Implement audio quality metrics:
  - Signal-to-noise ratio (SNR)
  - Audio level/volume monitoring
  - Clipping detection
  - Sample rate verification
  - Frequency spectrum analysis
- [ ] Add real-time quality metrics to WebSocket stream
- [ ] Create audio quality alerts (low SNR, clipping, etc.)
- [ ] Log audio quality metrics to database (if storage enabled)

**Success Criteria**:
- Audio quality calculated in real-time
- Metrics exposed via WebSocket
- Alerts triggered for quality issues
- Quality data logged

**Files Created**:
- `src/audio/quality.py` - Audio quality analysis
- `tests/unit/test_audio_quality.py` - Quality tests
- `tests/integration/test_audio_monitoring.py` - Integration tests

**Example Quality Metrics**:
```python
class AudioQualityMetrics:
    noise_level_db: float      # Background noise level
    signal_level_db: float     # Speech signal level
    snr_db: float              # Signal-to-noise ratio
    clipping_detected: bool    # Audio clipping detected
    sample_rate: int           # Actual sample rate
    is_acceptable: bool        # Overall quality assessment
```

---

**12.2 Build Audio Quality Monitoring Card (UI)** (Days 3-4)
- [ ] Create `AudioQualityCard` UI component
- [ ] Display real-time audio quality metrics:
  - SNR gauge with color coding (green/yellow/red)
  - Audio level meter (VU meter style)
  - Clipping indicator
  - Quality score (0-100)
  - Quality alerts/warnings
- [ ] Add audio quality timeline chart
- [ ] Add troubleshooting tips (when quality is poor)
- [ ] Test with various audio inputs

**Success Criteria**:
- Audio quality card displays real-time data
- Visual indicators clear and actionable
- Charts update smoothly
- Troubleshooting tips helpful

**Files Created**:
- `src/ui/components/cards/audio-quality-card.js` - Audio quality card
- `src/ui/core/audio-meters.js` - Audio meter components
- `tests/ui/test_audio_quality_card.html` - Card tests

---

**12.3 Implement Noise Reduction (Basic)** (Days 5-7)
- [ ] Research noise reduction libraries (noisereduce, RNNoise binding)
- [ ] Create `AudioProcessorPlugin` base class (if not done in Phase 2)
- [ ] Implement `NoiseReductionPlugin`:
  - Use `noisereduce` library or RNNoise
  - Configurable noise reduction strength
  - Real-time processing with minimal latency
- [ ] Add noise reduction configuration (on/off, strength)
- [ ] Add feature flag for noise reduction
- [ ] Test with noisy audio samples
- [ ] Measure latency impact (<50ms target)

**Success Criteria**:
- Noise reduction plugin works
- Configurable strength (off, light, medium, aggressive)
- Latency impact <50ms
- Audio quality improved on noisy inputs
- Feature flag allows disabling

**Files Created**:
- `src/plugins/audio/noise_reduction_plugin.py` - Noise reduction
- `src/audio/processor.py` - Audio preprocessing pipeline
- `tests/unit/test_noise_reduction.py` - Unit tests
- `tests/integration/test_audio_preprocessing.py` - Integration tests
- `docs/AUDIO_PREPROCESSING.md` - Audio preprocessing guide

**Example Configuration**:
```python
class NoiseReductionConfig(BaseModel):
    enabled: bool = True
    strength: str = Field("medium", pattern="^(off|light|medium|aggressive)$")
    stationary: bool = True  # Assume stationary noise
```

---

### Week 13: Advanced Audio Features - Part 2

#### Tasks

**13.1 Implement Speaker Detection/Diarization** (Days 1-3)
- [ ] Research speaker diarization libraries:
  - pyannote.audio (popular, accurate, requires model download)
  - speechbrain (alternative)
  - Simple VAD-based approach (faster but less accurate)
- [ ] Create `SpeakerDetectionPlugin`
- [ ] Implement speaker detection:
  - Assign speaker labels (Speaker 1, Speaker 2, etc.)
  - Track speaker changes in transcript
  - Add speaker labels to transcript data
- [ ] Add speaker detection configuration (on/off, model)
- [ ] Add feature flag for speaker detection
- [ ] Test with multi-speaker audio
- [ ] Measure latency impact

**Success Criteria**:
- Speaker detection plugin works
- Speaker labels accurate (>80%)
- Latency impact acceptable (<200ms)
- Speaker labels in transcript
- Feature flag allows disabling

**Files Created**:
- `src/plugins/audio/speaker_detection_plugin.py` - Speaker detection
- `src/audio/diarization.py` - Diarization utilities
- `tests/unit/test_speaker_detection.py` - Unit tests
- `tests/integration/test_speaker_diarization.py` - Integration tests
- `docs/SPEAKER_DETECTION.md` - Speaker detection guide

**Example Speaker Labels in Transcript**:
```json
{
  "timestamp": "2025-10-28T10:30:45Z",
  "speaker": "Speaker 1",
  "text": "What is your experience with Kubernetes?",
  "confidence": 0.92
}
```

---

**13.2 Update Transcript Card with Speaker Labels** (Days 4-5)
- [ ] Update `TranscriptCard` to display speaker labels
- [ ] Add speaker color coding (each speaker different color)
- [ ] Add speaker filtering (show only one speaker)
- [ ] Add speaker renaming (change "Speaker 1" to "Interviewer")
- [ ] Add speaker export (include in transcript export)
- [ ] Test with speaker detection enabled

**Success Criteria**:
- Speaker labels displayed in transcript
- Color coding clear and consistent
- Filtering works
- Renaming persists
- Export includes speakers

**Files Updated**:
- `src/ui/components/cards/transcript-card.js` - Add speaker support
- `tests/ui/test_transcript_card.html` - Test speaker features

---

**13.3 Implement Multiple Audio Sources** (Days 6-7)
- [ ] Extend audio architecture to support multiple simultaneous sources
- [ ] Create `MultiAudioSourceManager`
- [ ] Support use cases:
  - **Interview**: System audio (interviewer) + microphone (candidate)
  - **Meeting**: Multiple microphones
  - **Call Recording**: Different tracks for different speakers
- [ ] Add multi-source configuration
- [ ] Combine/merge audio streams intelligently
- [ ] Test with multiple audio inputs

**Success Criteria**:
- Can capture from multiple sources simultaneously
- Sources configurable
- Audio merged correctly
- Latency maintained
- Speaker detection works with multiple sources

**Files Created**:
- `src/audio/multi_source.py` - Multi-source management
- `tests/integration/test_multi_audio.py` - Multi-source tests
- `docs/MULTI_AUDIO.md` - Multi-audio guide

**Example Multi-Source Configuration**:
```yaml
audio_sources:
  - name: "interviewer"
    device: "System Audio"
    type: "system"
  - name: "candidate"
    device: "Microphone (USB)"
    type: "microphone"
```

---

### Phase 3 Deliverables

**Completed by End of Week 13**:
- ✅ Card-based modular UI
- ✅ Drag-and-drop card repositioning
- ✅ Grid layout system (20rem × 1rem)
- ✅ 6 card types (transcript, Q&A list, answer detail, performance, audio quality, config)
- ✅ 5 layout presets (Interview Stealth, Phone Call, Business Meeting, Performance Debug, Audio Debug)
- ✅ Custom preset saving/loading
- ✅ Performance monitoring dashboard
- ✅ Audio quality monitoring
- ✅ Noise reduction plugin
- ✅ Speaker detection/diarization
- ✅ Multiple audio sources support
- ✅ Speaker labels in transcript
- ✅ Audio quality card

**Success Metrics**:
- UI renders at 60fps consistently
- Card drag-and-drop smooth (<16ms latency)
- Layout switching instant (<500ms)
- Audio preprocessing latency <50ms
- Speaker detection accuracy >80%
- End-to-end latency still <4s (p95)

---

## Phase 4: Performance Monitoring & Production Polish (Weeks 14-17)

**Goal**: Comprehensive performance monitoring, optimization, and production readiness

### Week 14: Advanced Performance Monitoring

#### Tasks

**14.1 Build Performance Analytics Dashboard** (Days 1-3)
- [ ] Create performance analytics backend
- [ ] Track historical performance data (30 days)
- [ ] Calculate trend analysis (improving/degrading)
- [ ] Identify performance anomalies
- [ ] Generate daily/weekly performance reports
- [ ] Add performance comparison (different configs)
- [ ] Export analytics to CSV/JSON

**Success Criteria**:
- Historical data tracked and queryable
- Trends visualized
- Anomalies detected automatically
- Reports generated

**Files Created**:
- `src/core/analytics.py` - Analytics engine
- `src/server/analytics_api.py` - Analytics API
- `tests/unit/test_analytics.py` - Analytics tests

---

**14.2 Add Performance Regression Detection** (Days 4-5)
- [ ] Define performance regression thresholds
- [ ] Implement regression detection algorithm
- [ ] Add CI integration (fail if regression detected)
- [ ] Create regression alerts
- [ ] Add regression reporting
- [ ] Test regression detection

**Success Criteria**:
- Regressions detected in CI
- Alerts sent when regression occurs
- Can bisect commits to find regression cause

**Files Created**:
- `src/core/regression.py` - Regression detection
- `.github/workflows/performance.yml` - Performance CI
- `tests/performance/test_regression.py` - Regression tests

---

**14.3 Build Performance Profiling Tools** (Days 6-7)
- [ ] Add cProfile integration (optional profiling mode)
- [ ] Create flame graph generation
- [ ] Add memory profiling (tracemalloc)
- [ ] Create profiling CLI tool
- [ ] Add profiling to performance card (live view)
- [ ] Document profiling workflow

**Success Criteria**:
- Can profile production workloads
- Flame graphs generated
- Memory leaks detectable
- Profiling documented

**Files Created**:
- `src/core/profiler.py` - Profiling utilities
- `scripts/profile.py` - Profiling CLI tool
- `docs/PROFILING.md` - Profiling guide

---

### Week 15: UI Polish & Accessibility

#### Tasks

**15.1 Add Keyboard Shortcuts & Accessibility** (Days 1-2)
- [ ] Implement keyboard shortcuts:
  - `Ctrl+1/2/3/4/5` - Switch presets
  - `Ctrl+P` - Performance card toggle
  - `Ctrl+A` - Audio quality card toggle
  - `Ctrl+S` - Save current layout
  - `Ctrl+E` - Export session
  - `j/k` - Navigate Q&A list
  - `Space` - Play/pause audio (future)
  - `?` - Show keyboard shortcuts help
- [ ] Add ARIA labels for screen readers
- [ ] Add keyboard navigation (tab through cards)
- [ ] Add focus indicators
- [ ] Test with screen reader

**Success Criteria**:
- All keyboard shortcuts work
- Screen reader usable
- Keyboard navigation complete
- Focus indicators visible

**Files Created**:
- `src/ui/core/keyboard.js` - Keyboard shortcut system
- `src/ui/components/help-modal.js` - Keyboard help
- `docs/KEYBOARD_SHORTCUTS.md` - Shortcut documentation

---

**15.2 Add Dark Mode & Themes** (Days 3-4)
- [ ] Implement theme system
- [ ] Create light theme
- [ ] Create dark theme
- [ ] Create high-contrast theme (accessibility)
- [ ] Add theme selector
- [ ] Persist theme preference
- [ ] Add automatic theme (follow OS preference)

**Success Criteria**:
- 3 themes available
- Theme switching instant
- Preference persisted
- Auto theme works

**Files Created**:
- `src/ui/core/themes.js` - Theme system
- `src/ui/styles/theme-light.css` - Light theme
- `src/ui/styles/theme-dark.css` - Dark theme
- `src/ui/styles/theme-high-contrast.css` - High contrast

---

**15.3 UI Performance Optimization** (Days 5-7)
- [ ] Optimize rendering (virtual scrolling for long transcripts)
- [ ] Reduce reflows (batch DOM updates)
- [ ] Optimize WebSocket message handling (debounce updates)
- [ ] Lazy load cards (only render visible)
- [ ] Add loading states (skeleton screens)
- [ ] Profile UI performance (Chrome DevTools)
- [ ] Fix any jank (60fps target)

**Success Criteria**:
- UI smooth at 60fps
- Large transcripts don't slow UI
- WebSocket updates don't block rendering
- Loading states provide feedback

---

### Week 16: Production Hardening

#### Tasks

**16.1 Security Audit & Hardening** (Days 1-2)
- [ ] Audit all input validation
- [ ] Add rate limiting per client IP
- [ ] Add WebSocket authentication (for future multi-user)
- [ ] Add CORS configuration
- [ ] Audit dependencies for vulnerabilities (`safety` tool)
- [ ] Add security headers
- [ ] Document security features

**Success Criteria**:
- All inputs validated
- Rate limiting works
- No known vulnerabilities in dependencies
- Security documented

**Files Created**:
- `src/server/auth.py` - Authentication (groundwork)
- `src/server/rate_limit.py` - Enhanced rate limiting
- `docs/SECURITY.md` - Security documentation

---

**16.2 Error Recovery & Resilience** (Days 3-4)
- [ ] Test all error scenarios (Ollama down, Whisper crash, etc.)
- [ ] Add automatic restart for failed components
- [ ] Implement circuit breakers for all external services
- [ ] Add graceful degradation strategies
- [ ] Test recovery under load
- [ ] Document error handling

**Success Criteria**:
- System recovers from all tested failures
- Circuit breakers prevent cascading failures
- Degraded mode works (e.g., transcription only, no Q&A)
- Recovery tested

**Files Updated**:
- `src/core/circuit_breaker.py` - Enhanced circuit breaker
- `tests/integration/test_error_recovery.py` - Recovery tests

---

**16.3 Deployment & Installation Improvements** (Days 5-7)
- [ ] Create Docker image (optional, for easy deployment)
- [ ] Create docker-compose.yml (server + Ollama)
- [ ] Add installation script (auto-install dependencies)
- [ ] Create systemd service file (Linux)
- [ ] Create launchd plist (macOS)
- [ ] Test installation on fresh systems (Mac, Linux, Windows)
- [ ] Document deployment options

**Success Criteria**:
- Docker image works
- Installation script automates setup
- Service files work correctly
- Tested on all platforms

**Files Created**:
- `Dockerfile` - Docker image
- `docker-compose.yml` - Docker composition
- `scripts/install.sh` - Installation script
- `deploy/interview-assistant.service` - systemd service
- `deploy/com.interview-assistant.plist` - launchd plist
- `docs/DEPLOYMENT.md` - Deployment guide

---

### Week 17: Documentation & Release

#### Tasks

**17.1 Complete Documentation Overhaul** (Days 1-3)
- [ ] Rewrite README.md (updated for new architecture)
- [ ] Create comprehensive user guide
- [ ] Create developer onboarding guide
- [ ] Document all APIs (REST, WebSocket, Plugin)
- [ ] Add architecture diagrams
- [ ] Add video tutorials (optional)
- [ ] Create FAQ

**Success Criteria**:
- Documentation complete and accurate
- New user can install and run from README
- New developer can contribute from guide
- All APIs documented

**Files Updated**:
- `README.md` - Complete rewrite
- `docs/USER_GUIDE.md` - User documentation
- `docs/DEVELOPER_GUIDE.md` - Developer documentation
- `docs/API.md` - API documentation
- `docs/FAQ.md` - Frequently asked questions

---

**17.2 Comprehensive Testing & Bug Fixes** (Days 4-5)
- [ ] Test all features end-to-end
- [ ] Test on all platforms (Mac, Linux, Windows)
- [ ] Test with different configurations
- [ ] Test with multiple concurrent users
- [ ] Load testing (stress test)
- [ ] Test upgrade path (v1 → v2)
- [ ] Fix all discovered bugs

**Success Criteria**:
- All features working on all platforms
- No critical bugs
- Load tested successfully
- Upgrade path verified

**Files Created**:
- `tests/e2e/test_full_system.py` - E2E tests
- `tests/load/test_load.py` - Load tests
- `docs/TEST_REPORT.md` - Test results

---

**17.3 Performance Benchmarking & Final Optimization** (Days 6-7)
- [ ] Run comprehensive performance benchmarks
- [ ] Compare with Phase 1 baseline
- [ ] Identify any regressions
- [ ] Optimize critical paths
- [ ] Generate final performance report
- [ ] Verify <4s end-to-end latency (p95)

**Success Criteria**:
- Performance meets all targets
- No regressions vs baseline
- Final report generated
- Optimizations documented

**Files Created**:
- `docs/FINAL_PERFORMANCE_REPORT.md` - Performance results
- `benchmarks/results_v2.json` - Benchmark data

---

**17.4 Release Preparation** (Day 7+)
- [ ] Version bump to v2.0.0
- [ ] Write changelog (all changes since v1.0)
- [ ] Create release notes
- [ ] Tag release in git
- [ ] Build release artifacts (Docker image, pip package)
- [ ] Update CLAUDE.md to reflect completion
- [ ] Celebrate!

**Success Criteria**:
- Release tagged
- Artifacts built
- Documentation updated
- Ready for users

**Files Created**:
- `CHANGELOG.md` - Complete changelog
- `RELEASE_NOTES.md` - v2.0.0 release notes

---

### Phase 4 Deliverables

**Completed by End of Week 17**:
- ✅ Advanced performance monitoring
- ✅ Performance regression detection
- ✅ Profiling tools
- ✅ Keyboard shortcuts & accessibility
- ✅ Dark mode & themes
- ✅ UI performance optimized (60fps)
- ✅ Security hardening
- ✅ Error recovery & resilience
- ✅ Docker deployment
- ✅ Installation automation
- ✅ Complete documentation
- ✅ End-to-end testing
- ✅ Load testing
- ✅ Final performance report
- ✅ v2.0.0 release

**Success Metrics**:
- End-to-end latency <4s (p95) ✅
- Test coverage >80% ✅
- Zero critical bugs ✅
- Documentation complete ✅
- Production-ready ✅

---

## Beyond Phase 4: Future Enhancements (Post-v2.0)

**These features are deferred but documented for future development**:

### Term/Acronym Detection & Explanation
- Auto-detect jargon (SRE, CI/CD, K8s, etc.)
- Inline explanations or tooltips
- Session-scoped deduplication
- Batch explanations with LLM prompts

### Smart Onboarding Flow
- Interactive setup wizard
- Career profile creation
- Session context (company, position)
- All phases optional

### CRM Integration
- Salesforce plugin
- Dynamics 365 plugin
- Customer context fetching
- AI-enhanced insights (upsell, churn, talking points)

### Multi-User / SaaS Features
- User authentication
- Multi-tenancy
- Team collaboration
- Billing integration
- Cloud deployment

### Advanced LLM Features
- Conversation summarization
- Follow-up question suggestions
- Context-aware responses
- Fine-tuned models

---

## Success Metrics & KPIs

### Performance Metrics (Critical)
- **End-to-end latency (p95)**: <4s ✅ Target
- **Audio preprocessing latency**: <50ms
- **Transcription latency**: <500ms
- **LLM generation latency**: <3s
- **UI render latency**: <100ms
- **Plugin swap latency**: <1s

### Quality Metrics
- **Test coverage**: >80%
- **Bug density**: <1 bug per 1000 lines
- **Code review coverage**: 100%
- **Documentation coverage**: 100% (all public APIs)

### Usability Metrics
- **Installation time**: <10 minutes (fresh system)
- **Time to first answer**: <5 minutes (after install)
- **Keyboard shortcut coverage**: 100% (all actions accessible)
- **Accessibility score**: >90 (Lighthouse)

### Audio Quality Metrics (New)
- **Speaker detection accuracy**: >80%
- **Noise reduction effectiveness**: >60% noise floor reduction
- **Audio quality detection**: >90% accuracy

---

## Risk Management

### Technical Risks

**Risk**: Performance regression during refactoring
**Mitigation**: Continuous performance testing, regression detection in CI

**Risk**: Breaking changes during migration
**Mitigation**: Feature flags, backward compatibility testing

**Risk**: Plugin system complexity
**Mitigation**: Start simple, iterate based on real needs

**Risk**: Advanced audio features add latency
**Mitigation**: Strict latency budgets, make features optional

**Risk**: Speaker detection accuracy issues
**Mitigation**: Multiple detection models, user override options

### Schedule Risks

**Risk**: Underestimating audio feature complexity
**Mitigation**: Buffer time in Phase 3, can defer if needed

**Risk**: Scope creep during development
**Mitigation**: Strict phase boundaries, defer features to post-v2.0

**Risk**: Dependency issues (Ollama, Whisper, pyannote updates)
**Mitigation**: Pin versions, test upgrades carefully

---

## Tools & Infrastructure

### Development Tools
- **Editor**: VSCode, PyCharm, or preferred
- **Python**: 3.10+ (required)
- **Git**: Version control
- **Make**: Task automation

### Testing Tools
- **pytest**: Unit and integration testing
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking
- **locust**: Load testing (optional)

### Performance Tools
- **cProfile**: CPU profiling
- **py-spy**: Sampling profiler
- **tracemalloc**: Memory profiling
- **Flamegraph**: Visualization

### Code Quality Tools
- **ruff**: Linting
- **black**: Code formatting
- **mypy**: Type checking
- **safety**: Dependency security

### Audio Processing Libraries (Phase 3)
- **noisereduce**: Noise reduction
- **pyannote.audio**: Speaker diarization
- **librosa**: Audio analysis
- **soundfile**: Audio I/O

---

## Conclusion

This roadmap transforms Interview_Assistant from a functional MVP into a production-ready, modular system over 17 weeks. The plan prioritizes:

1. **Foundation** (Weeks 1-4): Logging, config, testing, state management
2. **Plugin Architecture** (Weeks 5-8): Core plugin system, multiple plugins
3. **UI & Audio** (Weeks 9-13): Card-based UI, advanced audio features
4. **Production Polish** (Weeks 14-17): Monitoring, security, deployment, docs

**Key Success Factors**:
- Maintain <4s end-to-end latency throughout
- Never break existing functionality (feature flags)
- Test during refactoring (not after)
- Document as you go
- Ship incrementally

**End State**: A production-ready, plugin-based interview assistant with:
- Modular architecture
- Comprehensive performance monitoring
- Card-based drag-and-drop UI
- Advanced audio features (noise reduction, speaker detection, quality monitoring)
- 80%+ test coverage
- Complete documentation
- Docker deployment
- CLI tool
- Ready for open source or SaaS

Let's build this! 🚀
