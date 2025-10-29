# Technology Stack

## Programming Languages

### Python 3.9+
- **Primary Language**: Server and client implementation
- **Version Requirement**: Python 3.9 or higher
- **Usage**: All backend processing, ML inference, WebSocket server

### JavaScript (ES6+)
- **Usage**: Web UI interactivity and WebSocket client
- **Environment**: Browser-based, no build tools required
- **Features**: Async/await, WebSocket API, DOM manipulation

### HTML5 & CSS3
- **Usage**: Web UI structure and styling
- **Features**: Semantic HTML, CSS Grid/Flexbox, CSS variables

## Core Dependencies

### Machine Learning & AI

#### PyTorch
- **Purpose**: ML framework for Whisper model
- **Installation**: CPU or CUDA versions available
- **Components**: torch, torchvision, torchaudio
- **Configuration**: CPU by default, CUDA for GPU acceleration

#### faster-whisper
- **Purpose**: Optimized Whisper implementation for speech-to-text
- **Performance**: Low-latency transcription
- **Models**: tiny, base, small, medium, large
- **Backend**: CTranslate2 for efficient inference

#### Ollama
- **Purpose**: Local LLM inference platform
- **Features**: Question detection and answer generation
- **Models**: Supports multiple models (gpt-oss:120b-cloud, phi3.5, llama3.2, etc.)
- **API**: HTTP REST API on localhost:11434

### Networking & Communication

#### websockets
- **Purpose**: WebSocket server and client implementation
- **Usage**: Real-time bidirectional communication
- **Features**: Async/await support, connection management

### Data Processing

#### numpy
- **Purpose**: Audio data manipulation and numerical operations
- **Usage**: Audio buffer processing, energy calculations
- **Performance**: Efficient array operations

### External Tools

#### FFmpeg
- **Purpose**: Audio capture and format conversion
- **Installation**: System-level dependency
- **Usage**: Microphone input capture, audio resampling
- **Platforms**: Windows, macOS, Linux

## Development Environment

### Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
.\venv\Scripts\activate   # Windows
```

### Dependency Installation
```bash
pip install -r requirements.txt
```

### GPU Support (Optional)
```bash
# Replace CPU PyTorch with CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Build & Deployment

### No Build Process Required
- Python scripts run directly
- HTML file opens in browser without server
- No compilation or bundling needed

### Development Commands

#### Start Server
```bash
python optimized_stt_server_v3.py
```

#### List Audio Devices
```bash
python stable_audio_client_multi_os.py --list-devices
```

#### Start Audio Client
```bash
python stable_audio_client_multi_os.py --device "DEVICE_NAME"
```

#### Start Ollama Service
```bash
ollama serve
```

#### Pull Ollama Model
```bash
ollama pull gpt-oss:120b-cloud
```

## System Requirements

### Minimum Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB (16GB recommended for larger models)
- **Storage**: 5GB for models and dependencies
- **OS**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **Network**: Localhost WebSocket support

### Recommended Requirements
- **GPU**: NVIDIA GPU with CUDA support (for faster transcription)
- **CUDA**: Version 11.x or 12.x
- **cuDNN**: Compatible version with CUDA
- **RAM**: 16GB+ for large Whisper models
- **Storage**: 10GB+ for multiple Ollama models

### Browser Requirements
- **Modern Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Features**: WebSocket API, ES6+ JavaScript support
- **No Extensions Required**: Standalone HTML file

## Configuration Management

### Environment Variables
- **File**: `.env.example` (copy to `.env`)
- **Format**: KEY=VALUE pairs
- **Categories**:
  - Ollama configuration
  - Server settings
  - Whisper parameters
  - Audio processing
  - LLM behavior
  - Debug options

### Default Configuration
- All settings have sensible defaults
- No `.env` file required for basic usage
- Configuration embedded in Python scripts

## Performance Optimization

### Whisper Model Selection
- **tiny**: Fastest, lowest accuracy (~1GB RAM)
- **base**: Balanced speed/accuracy (~1GB RAM)
- **small**: Good accuracy (~2GB RAM)
- **medium**: High accuracy (~5GB RAM)
- **large**: Best accuracy (~10GB RAM)

### Compute Type
- **int8**: Fastest, lowest memory (CPU-friendly)
- **float16**: Balanced (GPU-recommended)
- **float32**: Highest accuracy, slowest

### Ollama Model Selection
- **Fast**: phi3.5:3.8b, llama3.2:1b, qwen2.5:1.5b
- **Balanced**: gemma2:2b, mistral
- **High Quality**: gpt-oss:120b-cloud (requires internet)

### Audio Processing
- **Sample Rate**: 16000 Hz (optimal for Whisper)
- **Window Size**: 6.0 seconds (configurable)
- **Hop Size**: 0.8 seconds (overlap for continuity)

## Platform-Specific Notes

### Windows
- FFmpeg installation via Chocolatey or manual download
- Audio device names: "Stereo Mix", "Microphone Array"
- Windows Defender may require exceptions

### macOS
- FFmpeg via Homebrew: `brew install ffmpeg`
- Audio device format: `:0`, `:1` (device index)
- Microphone permissions required

### Linux
- FFmpeg via package manager: `apt-get install ffmpeg`
- Audio device format: `hw:0,0`, `hw:1,0`
- User must be in `audio` group
- PipeWire or PulseAudio for audio routing

## Security Considerations

### Local Processing
- All data processed locally by default
- No external API calls (except cloud Ollama models)
- No data persistence unless explicitly saved

### Network Security
- WebSocket server binds to localhost (127.0.0.1)
- No external network exposure by default
- No authentication required (local-only access)

### Privacy
- No telemetry or analytics
- No cloud dependencies (with local models)
- User controls all data export

## Testing & Debugging

### Debug Mode
- Enable via environment variable: `DEBUG=true`
- Verbose buffer logging: `VERBOSE_BUFFER=true`
- Console output for troubleshooting

### Connection Testing
```bash
# Test Ollama connection
curl http://localhost:11434/api/version

# List available models
ollama list

# Test WebSocket server
# Open index.html and check connection status
```

### Audio Device Testing
```bash
# List all audio devices
python stable_audio_client_multi_os.py --list-devices

# Test specific device
python stable_audio_client_multi_os.py --device "DEVICE_NAME"
```
