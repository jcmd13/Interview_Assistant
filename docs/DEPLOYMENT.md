# Deployment Guide

**Last Updated**: November 8, 2025
**Status**: Production Ready

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Configuration](#production-configuration)
4. [Performance Tuning](#performance-tuning)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting Deployment](#troubleshooting-deployment)
7. [Advanced Configurations](#advanced-configurations)

---

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/jcmd13/Interview_Assistant.git
cd Interview_Assistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: .\venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama (in separate terminal)
ollama serve

# 5. Run server
python optimized_stt_server_v3.py

# 6. In another terminal, start audio client
python stable_audio_client_multi_os.py --list-devices
python stable_audio_client_multi_os.py --device "Your Microphone"

# 7. Open UI in browser
# Open http://127.0.0.1:8123 in your browser
# Or run the launcher
python launcher.py
```

### Development Environment Setup

#### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 ffmpeg ollama

# Create virtual environment with system Python
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install development tools
pip install black isort pytest pytest-cov
```

#### Windows

```bash
# Install Chocolatey (if not already installed)
# https://chocolatey.org/install

# Install dependencies
choco install python ffmpeg ollama

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install development tools
pip install black isort pytest pytest-cov
```

#### Linux (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-venv python3-pip ffmpeg

# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install development tools
pip install black isort pytest pytest-cov
```

---

## Docker Deployment

### Building Docker Image

#### Dockerfile Template

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose WebSocket port
EXPOSE 8123

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# Start server
CMD ["python", "optimized_stt_server_v3.py"]
```

#### Building the Image

```bash
# Build image
docker build -t interview-assistant:latest .

# Build with specific Python version
docker build -t interview-assistant:py39 --build-arg PYTHON_VERSION=3.9 .

# Build with GPU support (CUDA)
docker build -f Dockerfile.cuda -t interview-assistant:cuda .
```

#### Running the Container

```bash
# Basic run
docker run -p 8123:8123 interview-assistant

# With environment variables
docker run -p 8123:8123 \
  -e WHISPER_MODEL=base \
  -e OLLAMA_MODEL_CLOUD=gpt-oss:120b-cloud \
  interview-assistant

# With volume mounts (for persistence)
docker run -p 8123:8123 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  interview-assistant

# With GPU support
docker run --gpus all -p 8123:8123 interview-assistant:cuda

# With resource limits
docker run -p 8123:8123 \
  --memory=4g \
  --cpus=2 \
  interview-assistant
```

### Docker Compose

#### docker-compose.yml

```yaml
version: '3.8'

services:
  server:
    build: .
    container_name: interview-assistant-server
    ports:
      - "8123:8123"
    environment:
      WHISPER_MODEL: base
      OLLAMA_MODEL_CLOUD: gpt-oss:120b-cloud
      DEBUG: "false"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - interview-network
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    container_name: interview-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    networks:
      - interview-network
    environment:
      OLLAMA_HOST: 0.0.0.0:11434

volumes:
  ollama_data:

networks:
  interview-network:
    driver: bridge
```

#### Launch with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f server

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Kubernetes Deployment

#### interview-assistant-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: interview-assistant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: interview-assistant
  template:
    metadata:
      labels:
        app: interview-assistant
    spec:
      containers:
      - name: server
        image: interview-assistant:latest
        ports:
        - containerPort: 8123
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: WHISPER_MODEL
          value: "base"
        - name: OLLAMA_MODEL_CLOUD
          value: "gpt-oss:120b-cloud"
        - name: DEBUG
          value: "false"
        livenessProbe:
          httpGet:
            path: /health
            port: 8123
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8123
          initialDelaySeconds: 10
          periodSeconds: 5
```

#### Deploy to Kubernetes

```bash
# Apply deployment
kubectl apply -f interview-assistant-deployment.yaml

# Check status
kubectl get pods -l app=interview-assistant

# View logs
kubectl logs -f deployment/interview-assistant

# Port forward for testing
kubectl port-forward svc/interview-assistant 8123:8123
```

---

## Production Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Server Configuration
SERVER_HOST=0.0.0.0  # Listen on all interfaces
SERVER_PORT=8123
DEBUG=false

# Audio Configuration
WHISPER_MODEL=base  # Use base for production (good accuracy/speed balance)
SAMPLE_RATE=16000
WINDOW_SECONDS=6.0  # 6 seconds for context
HOP_SECONDS=0.8     # Process every 0.8 seconds
ENERGY_GATE=-40     # Gate threshold in dB

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_CLOUD=gpt-oss:120b-cloud
MAX_CONCURRENT_LLM=3  # Limit simultaneous requests
MAX_OUTTOK=500        # Max answer length

# Interview Configuration
TECH_INTERVIEW_MODE=true
PERSONA=candidate  # candidate, assistant, or neutral
LLM_CONTEXT_MODE=full  # full, window, or headtail

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/interview_assistant.log

# Performance
ENABLE_GPU=true
WORKERS=4
BUFFER_SIZE=131072  # 128KB buffer
```

### Systemd Service (Linux)

Create `/etc/systemd/system/interview-assistant.service`:

```ini
[Unit]
Description=Interview Assistant Service
After=network.target ollama.service

[Service]
Type=simple
User=interview-assistant
WorkingDirectory=/opt/interview-assistant
Environment="PATH=/opt/interview-assistant/venv/bin"
ExecStart=/opt/interview-assistant/venv/bin/python optimized_stt_server_v3.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable interview-assistant
sudo systemctl start interview-assistant

# Check status
sudo systemctl status interview-assistant

# View logs
sudo journalctl -u interview-assistant -f
```

### Nginx Reverse Proxy

For production with SSL:

```nginx
upstream interview_assistant {
    server localhost:8123;
}

server {
    listen 443 ssl http2;
    server_name interview.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/interview.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/interview.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://interview_assistant;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket specific
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json;
}
```

---

## Performance Tuning

### Server Configuration Tuning

#### For Low-Latency Scenarios

```python
# In optimized_stt_server_v3.py
WHISPER_MODEL = "tiny"           # Faster transcription
WINDOW_SECONDS = 3.0             # Less context, faster
HOP_SECONDS = 0.3                # More frequent updates
MAX_CONCURRENT_LLM = 1           # Serialize answers
PERSONA = "neutral"              # Shorter responses
```

**Result**: ~2.5s end-to-end, less accurate

#### For High-Accuracy Scenarios

```python
WHISPER_MODEL = "large"          # Better transcription
WINDOW_SECONDS = 10.0            # More context
HOP_SECONDS = 2.0                # Less frequent updates
MAX_CONCURRENT_LLM = 5           # Parallel answers
PERSONA = "candidate"            # Full responses
```

**Result**: ~5-6s end-to-end, highly accurate

#### Balanced (Default)

```python
WHISPER_MODEL = "base"           # Good balance
WINDOW_SECONDS = 6.0             # Reasonable context
HOP_SECONDS = 0.8                # Regular updates
MAX_CONCURRENT_LLM = 3           # Good parallelism
PERSONA = "candidate"            # Full responses
```

**Result**: ~3-4s end-to-end, good accuracy

### Hardware Optimization

#### GPU Acceleration

```bash
# Check available GPU
nvidia-smi

# Install CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# faster-whisper will auto-detect GPU
# Whisper latency: 200-400ms → 50-150ms
```

#### Memory Optimization

```python
# Reduce buffer size for lower memory
WINDOW_SECONDS = 3.0  # Instead of 6.0
BUFFER_SIZE = 65536   # Instead of 131072

# Cache size
QUESTION_CACHE_SIZE = 100  # Instead of 500
```

#### CPU Optimization

```python
# For systems with limited CPU cores
WORKERS = 2  # Match number of cores
MAX_CONCURRENT_LLM = 1  # Reduce parallelism
HOP_SECONDS = 2.0  # Less frequent processing
```

---

## Monitoring & Logging

### Structured Logging

All logs are JSON formatted to stdout/file:

```bash
# View real-time logs with pretty-printing
python optimized_stt_server_v3.py 2>&1 | jq .

# Filter by component
grep -i "transcription" logs/interview_assistant.log

# Filter by level
grep '"level":"ERROR"' logs/interview_assistant.log
```

### Health Endpoint

```bash
# Check server health
curl http://localhost:8123/health

# Response:
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "transcription": "available",
  "ollama": "available",
  "connections": 1,
  "questions_detected": 5,
  "answers_generated": 5
}
```

### Metrics Endpoint

```bash
# Get system metrics
curl http://localhost:8123/metrics

# Response:
{
  "stats": {
    "transcription_latency": {
      "p50": 250,
      "p95": 400,
      "p99": 600
    },
    "question_detection_latency": {
      "p50": 75,
      "p95": 150,
      "p99": 200
    },
    "answer_generation_latency": {
      "p50": 2000,
      "p95": 3000,
      "p99": 4000
    }
  }
}
```

### Logging Configuration

```python
# In src/core/logger.py configuration

LOG_FORMAT = {
    "timestamp": "ISO8601",
    "level": "string",
    "component": "string",
    "message": "string",
    "metadata": "dict"
}

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}
```

---

## Troubleshooting Deployment

### Server Won't Start

```bash
# Check if port 8123 is in use
lsof -i :8123

# Kill existing process
kill -9 <PID>

# Check Python version
python --version  # Must be 3.9+

# Check dependencies
pip list | grep websockets
```

### Ollama Connection Issues

```bash
# Test Ollama availability
curl http://localhost:11434/api/version

# Check if Ollama is running
ollama list

# Pull required model
ollama pull gpt-oss:120b-cloud

# Restart Ollama
pkill ollama
ollama serve
```

### High Latency in Production

1. **Check hardware**:
   ```bash
   # CPU usage
   top -b -n1 | head -20

   # Memory usage
   free -h

   # GPU usage (if available)
   nvidia-smi
   ```

2. **Reduce buffer size**:
   ```python
   WINDOW_SECONDS = 3.0  # Instead of 6.0
   ```

3. **Use smaller models**:
   ```python
   WHISPER_MODEL = "tiny"
   OLLAMA_MODEL_CLOUD = "neural-chat:7b"  # Smaller/faster
   ```

4. **Increase parallelism**:
   ```python
   MAX_CONCURRENT_LLM = 5  # Or higher
   ```

### Memory Leaks

```bash
# Monitor memory over time
watch -n 1 'ps aux | grep python | grep -v grep'

# Profile memory usage
pip install memory-profiler
python -m memory_profiler optimized_stt_server_v3.py
```

---

## Advanced Configurations

### "Black Hole" Configuration (Offline Mode)

```python
# In optimized_stt_server_v3.py

# Use only local models (no internet required)
WHISPER_MODEL = "tiny"  # Download once, use offline
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL_CLOUD = "neural-chat:7b"  # Local model (no :cloud)

# Minimal memory footprint
WINDOW_SECONDS = 2.0
BUFFER_SIZE = 65536
MAX_CONCURRENT_LLM = 1

# Logging to file only (no network)
LOG_FILE = "logs/interview.log"
```

**Result**: Fully functional system with zero internet connectivity

### High-Performance Configuration

```python
# For powerful machines with GPU

WHISPER_MODEL = "large"           # Best accuracy
WINDOW_SECONDS = 8.0              # More context
HOP_SECONDS = 1.0                 # Regular updates
MAX_CONCURRENT_LLM = 5            # Parallel processing
OLLAMA_MODEL_CLOUD = "mistral"    # Faster, high quality

# Enable GPU
DEVICE = "cuda"  # Or "cpu" for CPU-only
```

### Low-Resource Configuration

```python
# For Raspberry Pi, old laptops, limited RAM

WHISPER_MODEL = "tiny"            # Minimal memory
WINDOW_SECONDS = 2.0              # Small buffer
HOP_SECONDS = 2.0                 # Less frequent
MAX_CONCURRENT_LLM = 1            # No parallelism
OLLAMA_MODEL_CLOUD = "orca-mini"  # Tiny model (3B params)
BUFFER_SIZE = 32768               # Minimal buffer
```

### Multi-Instance Configuration (Load Balancing)

```yaml
# docker-compose.yml with multiple servers

services:
  server-1:
    build: .
    ports:
      - "8123:8123"
    environment:
      INSTANCE_ID: 1

  server-2:
    build: .
    ports:
      - "8124:8123"
    environment:
      INSTANCE_ID: 2

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

---

## Scaling Guidelines

| Scale | Configuration | Hardware | Cost |
|-------|---------------|----------|------|
| **Single User** | Base config | 4GB RAM, 2 cores | Free |
| **Small Team (2-5)** | Balanced, GPU | 8GB RAM, 4 cores, GPU | $500-1000 |
| **Medium Team (5-20)** | Load balanced | 16GB RAM, 8 cores, GPU | $1000-3000 |
| **Large Deployment** | Kubernetes | 32GB+ RAM, high-end GPU | $5000+ |

---

## Monitoring Checklist

Daily:
- [ ] Server is running (`systemctl status`)
- [ ] Ollama is available (curl health endpoint)
- [ ] No error logs in past 24h
- [ ] Average latency < 4s

Weekly:
- [ ] Check disk space usage
- [ ] Review metrics trends
- [ ] Test failover procedure
- [ ] Backup session logs

Monthly:
- [ ] Update dependencies
- [ ] Review performance metrics
- [ ] Optimize configuration
- [ ] Test disaster recovery

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design details
- [TESTING.md](TESTING.md) - Testing procedures
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [Configuration Guide](CONFIGURATION.md) - Detailed config options

---

*For additional support, see [Support](../README.md#-support)*
