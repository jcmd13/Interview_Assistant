# Development Guidelines

## Code Quality Standards

### Import Organization
- Group imports logically: standard library, third-party, local modules
- Use compact comma-separated imports for related modules: `import asyncio, json, os, time, re, hashlib, shutil`
- Place type hints imports separately: `from typing import Set, Optional, List, Dict, Any`
- Import only what's needed from modules

### Code Formatting
- Use 4-space indentation consistently
- Keep lines under 120 characters where practical
- Use inline comments sparingly, prefer self-documenting code
- Separate logical sections with comment headers using `# ===` style
- Use Windows line endings (CRLF) for cross-platform compatibility

### Naming Conventions
- **Variables**: snake_case for all variables (`transcript_lines`, `bytes_since_last`)
- **Constants**: UPPER_SNAKE_CASE for configuration (`SAMPLE_RATE`, `LLM_ENABLED`)
- **Functions**: snake_case with descriptive names (`build_llm_context_text`, `get_platform_config`)
- **Classes**: PascalCase with descriptive names (`StableAudioStreamer`, `ImprovedLLMAnalyzer`)
- **Private helpers**: Prefix with underscore (`_norm`, `_qkey`, `_gen`)
- **Dataclasses**: Use for structured data with type hints

### Documentation Standards
- Use docstrings for public functions and classes
- Keep docstrings concise (1-2 lines for simple functions)
- Use inline comments for complex logic or non-obvious decisions
- Document configuration sections with clear headers
- Include usage examples in module-level docstrings

## Structural Conventions

### Configuration Management
- Hardcode sensible defaults directly in code
- Group related configuration in clearly marked sections
- Use descriptive variable names that explain purpose
- Provide inline comments for non-obvious settings
- Example pattern:
```python
# ========================
# Configuration
# ========================
HOST = "127.0.0.1"  # Hardcoded, removed os.getenv
PORT = 8123
SAMPLE_RATE = 16000
```

### Error Handling
- Use try-except blocks for external operations (file I/O, network, subprocess)
- Catch specific exceptions when possible
- Provide informative error messages with context
- Use DEBUG flags to control error verbosity
- Graceful degradation: disable features rather than crash
- Example pattern:
```python
try:
    import ollama
    ollama.list()
    print(f"[llm] ✅ Ready (model={OLLAMA_MODEL_CLOUD})")
except Exception as e:
    print(f"[llm] ❌ Ollama error: {e}")
    self.enabled = False
```

### Logging Patterns
- Use prefixed print statements: `[module]`, `[llm]`, `[stt]`, `[ws]`
- Include emoji for visual clarity: ✅ (success), ❌ (error), ⚠️ (warning), 🎤 (audio)
- Respect DEBUG flags for verbose output
- Log important state changes and errors
- Example: `print(f"[ws] Client connected from {ws.remote_address}")`

### Async/Await Patterns
- Use `async def` for all I/O-bound operations
- Prefer `asyncio.create_task()` for background tasks
- Use `asyncio.Queue` for producer-consumer patterns
- Implement proper cleanup in `finally` blocks
- Use `asyncio.Semaphore` for rate limiting
- Example pattern:
```python
async def handler(ws):
    client = ClientState(ws=ws, queue=asyncio.Queue(maxsize=100))
    client.sender_task = asyncio.create_task(_client_sender(client))
    try:
        async for msg in ws:
            # Process messages
    finally:
        if client.sender_task:
            client.sender_task.cancel()
```

## Semantic Patterns

### Dataclass Usage
- Use `@dataclass` for structured data with multiple fields
- Include type hints for all fields
- Provide default values using `field()` or direct assignment
- Example:
```python
@dataclass
class QuestionCandidate:
    question: str
    context: str
    timestamp: float
    confidence: float = 0.7
    urgency: str = "medium"
    topic_area: str = "general"
```

### State Management
- Use global variables for shared server state
- Protect shared state with `asyncio.Lock`
- Use `deque` with `maxlen` for bounded collections
- Clear state in dedicated reset functions
- Example:
```python
audio_lock = asyncio.Lock()
transcript_lines: List[str] = []

async def process_audio():
    async with audio_lock:
        pcm_buf.extend(msg)
```

### WebSocket Communication
- Use JSON for all structured messages
- Include message type/command field: `{"cmd": "reset"}`
- Broadcast updates to all interested clients
- Implement client role detection (UI vs. audio streamer)
- Handle connection cleanup in finally blocks

### LLM Integration Patterns
- Separate question detection from answer generation
- Use rate limiting to prevent API abuse
- Implement deduplication using normalized question keys
- Provide fallback responses for errors
- Cache seen questions with TTL
- Example:
```python
def _qkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _norm(s).lower())

if k in self.seen_questions:
    continue
self.seen_questions[k] = time.time()
```

### Audio Processing Patterns
- Use windowing with overlap for continuous transcription
- Implement energy-based voice activity detection
- Buffer audio data with maximum size limits
- Convert audio to numpy arrays for processing
- Example:
```python
arr = np.frombuffer(window_bytes, dtype=np.int16).astype(np.float32) / 32768.0
if np.mean(arr*arr) < ENERGY_GATE:
    continue
```

### Multi-Platform Support
- Detect OS using `platform.system()`
- Create platform-specific configuration dictionaries
- Abstract platform differences in helper functions
- Provide clear error messages for missing dependencies
- Example:
```python
def get_platform_config():
    system = platform.system()
    if system == "Windows":
        return {"format": "dshow", "device_prefix": "audio="}
    elif system == "Darwin":
        return {"format": "avfoundation", "device_prefix": ":"}
    elif system == "Linux":
        return {"format": "alsa", "device_prefix": ""}
```

## Internal API Usage

### Ollama Integration
```python
import ollama

# Chat completion
response = ollama.chat(
    model=OLLAMA_MODEL_CLOUD,
    messages=[
        {'role': 'system', 'content': 'System prompt'},
        {'role': 'user', 'content': 'User message'}
    ]
)
content = response['message']['content']

# List available models
ollama.list()
```

### faster-whisper Usage
```python
from faster_whisper import WhisperModel

# Load model
model = WhisperModel(
    MODEL_NAME,
    compute_type=COMPUTE_TYPE,
    download_root=cache_root
)

# Transcribe audio
segments, info = model.transcribe(
    audio_array,
    language=FORCE_LANG,
    vad_filter=True,
    initial_prompt=INITIAL_PROMPT
)
```

### WebSocket Server
```python
import websockets

# Server setup
async with websockets.serve(
    handler,
    HOST,
    PORT,
    max_size=2**20,
    ping_interval=10,
    ping_timeout=30
):
    await asyncio.Future()

# Client connection
async with websockets.connect(
    ws_url,
    max_size=2**20,
    ping_interval=None,
    compression=None
) as ws:
    await ws.send(data)
    async for msg in ws:
        process(msg)
```

### FFmpeg Subprocess
```python
# Create subprocess
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    limit=2**20
)

# Read with timeout
chunk = await asyncio.wait_for(
    process.stdout.read(chunk_size),
    timeout=1.0
)

# Cleanup
process.terminate()
await asyncio.wait_for(process.wait(), timeout=3)
```

## Code Idioms

### Text Normalization
```python
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())
```

### Question Key Generation (Deduplication)
```python
def _qkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _norm(s).lower())
```

### Numbered Line Generation
```python
def get_last_n_lines(n: int) -> List[str]:
    if n <= 0 or not transcript_lines:
        return []
    start_idx = max(0, len(transcript_lines) - n)
    return [f"{i+1}. {transcript_lines[i]}" for i in range(start_idx, len(transcript_lines))]
```

### Rate Limiting with Deque
```python
answers_timestamps = deque(maxlen=64)

# Check rate limit
now = time.time()
while answers_timestamps and now - answers_timestamps[0] > 60:
    answers_timestamps.popleft()

if len(answers_timestamps) >= ANSWERS_PER_MIN:
    return False

# Record timestamp
answers_timestamps.append(now)
```

### Broadcast Pattern
```python
async def broadcast(data: dict):
    if not clients:
        return
    msg = json.dumps(data, ensure_ascii=False)
    for c in list(clients.values()):
        if c.wants_broadcast:
            try:
                if c.queue.full():
                    _ = c.queue.get_nowait()
                c.queue.put_nowait(msg)
            except Exception:
                clients.pop(c.ws, None)
```

### Executor Pattern for Blocking Operations
```python
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(None, blocking_function, *args)
```

## Best Practices

### Performance Optimization
- Use `int8` compute type for CPU-based Whisper inference
- Implement audio windowing to reduce latency
- Use semaphores to limit concurrent LLM requests
- Buffer audio with maximum size to prevent memory growth
- Use deque with maxlen for automatic size management

### Resource Management
- Always cleanup subprocesses in finally blocks
- Cancel background tasks on client disconnect
- Implement connection timeouts and heartbeats
- Use context managers for WebSocket connections
- Clear caches periodically (TTL-based expiration)

### Security Considerations
- Bind server to localhost by default (127.0.0.1)
- No authentication required for local-only access
- Sanitize LLM outputs to remove coaching language
- Validate JSON inputs before processing
- Handle malformed messages gracefully

### Testing & Debugging
- Use DEBUG flags to control verbosity
- Provide device listing functionality for troubleshooting
- Log connection attempts and errors
- Include platform information in startup messages
- Validate external dependencies on startup

### Code Maintainability
- Group related functionality in clearly marked sections
- Use descriptive variable names that explain purpose
- Keep functions focused on single responsibility
- Extract complex logic into helper functions
- Document non-obvious decisions with comments

### Cross-Platform Compatibility
- Use `pathlib.Path` for file operations
- Detect OS and adapt behavior accordingly
- Test on Windows, macOS, and Linux
- Provide platform-specific installation instructions
- Handle encoding differences (UTF-8 with error handling)

## Common Patterns Summary

### Configuration Pattern
```python
# ========================
# Section Name
# ========================
CONSTANT = value  # Description
```

### Async Handler Pattern
```python
async def handler(ws):
    client = setup_client(ws)
    try:
        async for msg in ws:
            await process(msg)
    except ConnectionClosed:
        pass
    finally:
        cleanup(client)
```

### LLM Request Pattern
```python
async with self.sem:
    try:
        response = ollama.chat(model=MODEL, messages=messages)
        return response['message']['content']
    except Exception as e:
        if DEBUG:
            print(f"[llm] Error: {e}")
        return fallback_response
```

### Platform Detection Pattern
```python
system = platform.system()
if system == "Windows":
    # Windows-specific code
elif system == "Darwin":
    # macOS-specific code
elif system == "Linux":
    # Linux-specific code
```

### Deduplication Pattern
```python
seen = {}
key = normalize(item)
if key in seen:
    continue
seen[key] = timestamp
```
