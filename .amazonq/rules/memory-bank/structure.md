# Project Structure

## Directory Organization

```
Interview_Assistant/
├── .amazonq/rules/memory-bank/    # Amazon Q documentation
├── .kiro/                          # Kiro AI specifications
│   ├── specs/                      # Feature specifications
│   └── steering/                   # Project steering docs
├── src/                            # Source code modules
│   ├── audio/                      # Audio processing components
│   └── interfaces/                 # Interface definitions
├── optimized_stt_server_v3.py     # Main WebSocket server
├── stable_audio_client_multi_os.py # Audio streaming client
├── index.html                      # Web UI dashboard
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
├── README.md                       # Project documentation
└── LICENSE                         # MIT License
```

## Core Components

### 1. WebSocket Server (`optimized_stt_server_v3.py`)
**Purpose**: Central hub for audio processing, transcription, and AI inference

**Responsibilities**:
- Receives raw audio streams via WebSocket
- Performs real-time speech-to-text using faster-whisper
- Detects questions from transcript using LLM
- Generates contextual answers via Ollama
- Broadcasts transcript and Q&A to connected clients
- Manages session state and conversation context

**Key Features**:
- Asynchronous WebSocket handling
- Audio windowing with configurable overlap
- Energy-based voice activity detection
- Rate limiting and backpressure management
- Concurrent LLM request handling
- Session reset and state management

### 2. Audio Client (`stable_audio_client_multi_os.py`)
**Purpose**: Cross-platform audio capture and streaming

**Responsibilities**:
- Captures microphone input using FFmpeg
- Converts audio to required format (16kHz, mono, PCM)
- Streams audio chunks to WebSocket server
- Handles connection stability and reconnection
- Provides device discovery and listing

**Key Features**:
- Multi-OS support (Windows, macOS, Linux)
- Automatic device detection
- Configurable audio parameters
- Robust error handling and reconnection
- Platform-specific audio device naming

### 3. Web UI (`index.html`)
**Purpose**: Real-time visualization and interaction dashboard

**Responsibilities**:
- Displays live transcript with timestamps
- Shows detected questions and generated answers
- Provides session controls (reset, save, manual questions)
- Manages WebSocket connection to server
- Exports session data to Markdown

**Key Features**:
- Zero-dependency standalone HTML
- Three-panel responsive layout
- Real-time WebSocket updates
- Keyboard shortcuts
- Auto-scroll and follow modes
- Session export functionality

## Architectural Patterns

### Client-Server Architecture
- **Server**: Centralized processing hub (WebSocket server)
- **Clients**: Audio client (streams audio) + Web UI (displays results)
- **Protocol**: WebSocket for bidirectional real-time communication

### Message Flow
```
Audio Client → [Audio Stream] → Server
Server → [Transcription] → Web UI
Server → [Q&A Pairs] → Web UI
Web UI → [Commands] → Server
```

### Data Processing Pipeline
```
Microphone → FFmpeg → Audio Client → WebSocket
    ↓
Server: Audio Buffer → Whisper → Transcript
    ↓
Server: Transcript → LLM (Question Detection) → Questions
    ↓
Server: Questions + Context → LLM (Answer Gen) → Answers
    ↓
WebSocket → Web UI → Display
```

### Asynchronous Processing
- Server uses Python asyncio for concurrent operations
- Non-blocking WebSocket communication
- Parallel LLM inference with semaphore-based rate limiting
- Async audio processing with windowed buffering

### State Management
- Server maintains session state (transcript, Q&A history)
- Context window management for LLM prompts
- Client-side UI state (selected question, scroll position)
- Stateless audio client (streaming only)

## Component Relationships

### Server Dependencies
- **faster-whisper**: Speech-to-text engine
- **Ollama**: LLM inference (question detection + answer generation)
- **websockets**: Real-time communication
- **torch**: ML framework for Whisper
- **numpy**: Audio data processing

### Client Dependencies
- **FFmpeg**: Audio capture and format conversion
- **websockets**: Server communication
- **Python standard library**: Async I/O, subprocess management

### UI Dependencies
- **None**: Pure HTML/CSS/JavaScript
- **Browser WebSocket API**: Server communication

## Configuration System

### Environment-Based Configuration
- `.env.example` provides template for all settings
- Server reads environment variables with fallback defaults
- Configuration categories:
  - Ollama settings (model, base URL)
  - Server settings (host, port)
  - Whisper settings (model size, compute type)
  - Audio processing (sample rate, window size)
  - LLM behavior (persona, context mode, rate limits)
  - Debug options

### Runtime Configuration
- Most settings have sensible defaults
- No configuration required for basic usage
- Advanced users can tune performance/accuracy tradeoffs

## Extension Points

### Model Swapping
- Easy Ollama model switching via configuration
- Whisper model size selection for speed/accuracy balance
- Support for custom Ollama models

### Audio Sources
- FFmpeg supports various input devices
- Extensible to file-based audio processing
- Potential for network audio streams

### UI Customization
- Single-file HTML for easy modification
- CSS variables for theming
- JavaScript event handlers for custom behaviors

### LLM Prompts
- Configurable persona and context modes
- Technical interview mode optimization
- Custom prompt engineering via code modification
