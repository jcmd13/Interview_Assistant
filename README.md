# Trotski - Real-Time AI Interview Assistant

This project provides a high-performance, real-time audio transcription and AI-powered answering server. It uses faster-whisper for low-latency STT (Speech-to-Text) and Ollama with cloud models to intelligently detect questions from the transcript and generate relevant, contextual answers on the fly.

The system is composed of three main parts:

- **The Server** (`optimized_stt_server_v3.py`): A WebSocket server that receives raw audio, transcribes it, analyzes the text for questions, and generates answers using Ollama.
- **The Client** (`stable_audio_client_multi_os.py`): A robust, multi-platform audio streaming client that captures microphone input using FFmpeg and streams it to the server.
- **The UI** (`index.html`): A standalone, zero-dependency web interface that connects to the server to display the live transcript and Q&A panel.

## 🔒 Why Ollama?

This project has been updated to use **Ollama** instead of OpenAI for several key advantages:

- **🔐 Privacy**: All processing can be done locally - your conversations never leave your machine
- **💰 Cost-Effective**: No API costs or usage limits
- **🚀 Performance**: Local models provide consistent, fast responses without network latency
- **🔧 Flexibility**: Easy to switch between different models based on your needs
- **📶 Offline Capable**: Works without internet connection (except for cloud models)
- **🎯 Customizable**: Fine-tune responses by adjusting model parameters and prompts

## ✨ Features

- **Real-Time Transcription**: Low-latency audio transcription using faster-whisper
- **Intelligent Question Detection**: An LLM-powered analyzer detects questions from the live transcript
- **AI-Powered Answer Generation**: Generates context-aware, in-character answers for detected questions
- **Ollama Integration**: Uses local Ollama with cloud models - no API keys required!
- **Privacy-Focused**: All processing can be done locally with Ollama models
- **Contextual Awareness**: Maintains conversation context for more relevant responses
- **Standalone Web UI**: A feature-rich, single-file `index.html` dashboard to monitor the interview
- **Multi-Platform Support**: The server and client run on Windows, macOS, and Linux
- **Robust & Stable**: Includes automatic reconnection, backpressure handling, and stable connection parameters
- **Highly Configurable**: Nearly every aspect can be configured directly in the code

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Python 3.9+

### FFmpeg
Required by the audio client to capture microphone audio.

- **Windows**: Download from the [official website](https://ffmpeg.org/download.html) and add to PATH, or use Chocolatey (`choco install ffmpeg`)
- **macOS**: Install via Homebrew: `brew install ffmpeg`
- **Linux**: Install via your package manager: `sudo apt-get install ffmpeg` (Debian/Ubuntu)

### NVIDIA GPU with CUDA (Recommended)
For significant performance gains with the Whisper model.

- Install the latest [NVIDIA Driver](https://www.nvidia.com/drivers/)
- Install the [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) (v11.x is compatible)
- Install [cuDNN](https://developer.nvidia.com/cudnn)

### Ollama
Required for question detection and answer generation using local or cloud models.

- Install Ollama from [ollama.ai](https://ollama.ai/)
- Start the Ollama service: `ollama serve`
- Pull the required model: `ollama pull gpt-oss:120b-cloud` (or your preferred model)

## ⚡ Quick Start

For the impatient - get running in 5 minutes:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama and pull model
ollama serve &
ollama pull gpt-oss:120b-cloud

# 3. Clone and setup
git clone https://github.com/jcmd13/Interview_Assistant.git
cd Interview_Assistant
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# 4. Run the server
python optimized_stt_server_v3.py

# 5. Open index.html in your browser

# 6. Find your microphone and start streaming
python stable_audio_client_multi_os.py --list-devices
python stable_audio_client_multi_os.py --device "YOUR_DEVICE_NAME"
```

## 🚀 Detailed Installation

### 1. Clone the Repository

```bash
git clone https://github.com/iluxu/Trotski.git
cd Trotski
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# On Windows
.\venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

Create a `requirements.txt` file with the content specified below and run:

```bash
pip install -r requirements.txt
```

**CPU-Only Note**: The requirements.txt is already configured for CPU-only PyTorch. If you have an NVIDIA GPU and want to use CUDA acceleration, replace the torch installation lines with:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Set Up Ollama

Make sure Ollama is running and has the required model:

```bash
# Start Ollama service (if not already running)
ollama serve

# Pull the cloud model (in another terminal)
ollama pull gpt-oss:120b-cloud

# Verify the model is available
ollama list
```

The server is pre-configured to use Ollama with the `gpt-oss:120b-cloud` model. You can modify the model in `optimized_stt_server_v3.py` if needed.

## ⚙️ Usage

The process involves three steps: starting the server, opening the UI, and starting the audio client.

### 1. Run the Server

Start the server in a terminal. It will download the Whisper model on its first run.

```bash
python optimized_stt_server_v3.py
```

You should see output indicating the server is ready:
```
🎤 Server ready on ws://127.0.0.1:8123/
```

### 2. Open the Web UI

Simply open the `index.html` file in your web browser (e.g., Chrome, Firefox, Safari). No web server is needed. The page will automatically try to connect to the WebSocket server running on your local machine.

### 3. Run the Audio Client

The client needs to know which microphone to use.

#### Step A: Find Your Audio Device

Open a new terminal and run the client with the `--list-devices` flag:

```bash
python stable_audio_client_multi_os.py --list-devices
```

This will show you a list of available microphones and the correct name to use for your operating system.

#### Step B: Start Streaming

Now, run the client with the device name you found.

```bash
# Example for Windows
python stable_audio_client_multi_os.py --device "Mixage stéréo (Realtek(R) Audio)"

# Example for macOS
python stable_audio_client_multi_os.py --device ":0"

# Example for Linux
python stable_audio_client_multi_os.py --device "hw:0,0"
```

The client will connect to the server. Start speaking, and you will see the live transcript and Q&A appear in the `index.html` UI in your browser.

## 🖥️ Web UI Features (index.html)

The web UI is a powerful dashboard for monitoring the interview in real-time.

<!-- It's a good idea to add a screenshot of your UI here -->
<!-- <img src="https://i.imgur.com/your-screenshot-url.png" width="800" alt="UI Screenshot"> -->

### Three-Panel Layout

- **Transcript Panel (Left)**: Displays the live, timestamped transcription of the audio stream
- **Answer Detail (Center)**: Shows the full text of the selected question and its generated answer
- **Q&A List (Right)**: A table of all questions detected during the session. Click any question to view it in the center panel

### Status Indicators
At the top, you can see the WebSocket connection status, auto-scroll state, and a count of detected questions.

### Interactive Controls

- **📜 Auto**: Toggles auto-scrolling on the transcript panel
- **👁️ Follow**: Toggles automatically selecting the latest detected question
- **❓ Ask**: (UI-only feature) Manually type and submit a question to simulate an answer
- **🔄 Reset**: Clears the entire session state on the server and UI
- **💾 Save**: Exports the full transcript and Q&A log as a Markdown (.md) file

### Keyboard Shortcuts
The UI is fully navigable with keyboard shortcuts (e.g., j/k to navigate questions, p to toggle auto-scroll, s to save).

## ❤️ Support the Project

If you find this tool useful, please consider supporting its development. Your support helps cover API costs, encourages further development, and allows me to dedicate more time to improving it. Thank you!

<p align="center">
<a href="https://github.com/sponsors/iluxu" target="_blank">
<img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86" alt="Sponsor on GitHub">
</a>
&nbsp;&nbsp;
<a href="https://www.buymeacoffee.com/iluxu" target="_blank">
<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="28">
</a>
</p>

## 🔧 OS-Specific Tweaks & Performance

### Windows
- **Audio Configuration**: 
  - Open Sound Settings (Right-click speaker icon → Sounds → Recording tab)
  - Right-click in empty space → "Show Disabled Devices" 
  - Enable "Stereo Mix" or "What U Hear" to capture system audio
  - Set your microphone as default recording device
- Ensure Windows Defender real-time protection doesn't block audio processing
- Consider using Windows Terminal for better Unicode character display
- Set audio client to High Priority in Task Manager for reduced latency

### macOS
- Grant microphone permissions when prompted
- Use Activity Monitor to check CPU/GPU usage during transcription

### Linux
- Ensure your user is in the `audio` group: `sudo usermod -a -G audio $USER`
- For better performance, consider using `pipewire` instead of `pulseaudio`

## 🔧 Ollama Setup & Troubleshooting

### Installation
```bash
# Install Ollama (visit ollama.ai for platform-specific instructions)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the cloud model
ollama pull gpt-oss:120b-cloud
```

### Common Issues

**"Ollama not accessible" error:**
- Make sure Ollama is running: `ollama serve`
- Check if the service is listening: `curl http://localhost:11434/api/version`
- Verify the model is available: `ollama list`

**Model not found:**
- Pull the required model: `ollama pull gpt-oss:120b-cloud`
- You can use alternative models by changing `OLLAMA_MODEL_CLOUD` in the server code

**Performance Issues:**
- For faster responses, try smaller models like `phi3.5:3.8b` or `llama3.2:1b`
- Adjust `MAX_CONCURRENT_LLM` in the server configuration
- Consider using GPU acceleration if available

### Model Recommendations
- **Fast & Lightweight**: `phi3.5:3.8b`, `llama3.2:1b`, `qwen2.5:1.5b`
- **Balanced**: `gemma2:2b`, `mistral`
- **High Quality**: `gpt-oss:120b-cloud` (cloud model, requires internet)

## ⚙️ Configuration

The server is pre-configured with optimal settings. You can either:

1. **Use defaults**: Everything works out of the box with Ollama
2. **Customize settings**: Modify the configuration directly in `optimized_stt_server_v3.py`
3. **Environment variables**: Copy `.env.example` to `.env` and uncomment settings you want to change

### Key Configuration Options

### LLM Configuration (Ollama)
```python
OLLAMA_MODEL = "gpt-oss:120b-cloud"  # Main cloud model
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama server URL
LLM_ENABLED = True  # Enable/disable LLM features
```

### Whisper Configuration
```python
MODEL_NAME = "tiny"  # Whisper model size (tiny, base, small, medium, large)
COMPUTE_TYPE = "int8"  # Computation precision
SAMPLE_RATE = 16000  # Audio sample rate
```

### Audio Processing
```python
WINDOW_SECONDS = 6.0  # Audio window size for processing
HOP_SECONDS = 0.8  # Overlap between windows
ENERGY_GATE = 1e-4  # Minimum energy threshold
```

### Advanced Settings
```python
TECH_INTERVIEW_MODE = True  # Optimize for technical interviews
LLM_CONTEXT_MODE = "full"  # Context mode: "full", "window", or "headtail"
MAX_OUTTOK = 400  # Maximum output tokens
PERSONA = "candidate"  # Response persona
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for providing an excellent local LLM platform
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for efficient speech recognition
- [FFmpeg](https://ffmpeg.org/) for robust audio processing
- The open-source AI community for making powerful models accessible
