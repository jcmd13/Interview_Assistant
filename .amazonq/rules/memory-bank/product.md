# Product Overview

## Purpose
Interview_Assistant is a real-time AI-powered interview assistant that provides live audio transcription and intelligent question-answering capabilities. It helps users during interviews by transcribing conversations in real-time and generating contextual answers to detected questions using local LLM models.

## Value Proposition
- **Privacy-First**: All processing can be done locally using Ollama - conversations never leave your machine
- **Cost-Effective**: No API costs or usage limits with local models
- **Real-Time Performance**: Low-latency transcription using faster-whisper with intelligent question detection
- **Offline Capable**: Works without internet connection (except for cloud models)
- **Multi-Platform**: Runs on Windows, macOS, and Linux

## Key Features

### Real-Time Transcription
- Low-latency audio transcription using faster-whisper
- Configurable Whisper model sizes (tiny to large) for speed/accuracy tradeoff
- GPU acceleration support via CUDA for enhanced performance
- Automatic audio windowing and overlap for continuous transcription

### Intelligent Question Detection
- LLM-powered analyzer detects questions from live transcript
- Context-aware question identification optimized for technical interviews
- Configurable detection sensitivity and rate limiting

### AI-Powered Answer Generation
- Generates context-aware, in-character answers for detected questions
- Maintains conversation context for more relevant responses
- Configurable response persona (candidate, assistant, neutral)
- Multiple context modes (full, window, headtail) for different use cases

### Ollama Integration
- Uses local Ollama with support for cloud models
- No API keys required
- Easy model switching (gpt-oss:120b-cloud, phi3.5, llama3.2, etc.)
- Customizable model parameters and prompts

### Web-Based UI
- Standalone, zero-dependency HTML interface
- Three-panel layout: live transcript, answer detail, Q&A list
- Real-time WebSocket connection with status indicators
- Interactive controls: auto-scroll, follow mode, manual questions
- Session management: reset, save to Markdown
- Keyboard shortcuts for efficient navigation

### Robust Audio Client
- Multi-platform audio streaming using FFmpeg
- Automatic device detection and listing
- Stable connection with automatic reconnection
- Backpressure handling for reliable streaming

## Target Users

### Job Seekers
- Candidates preparing for technical interviews
- Professionals seeking real-time assistance during remote interviews
- Users wanting to review interview transcripts post-session

### Interviewers
- Technical interviewers wanting to capture and review conversations
- Recruiters needing accurate interview transcripts
- Teams conducting structured interviews with documentation needs

### Researchers & Developers
- AI/ML practitioners exploring real-time transcription systems
- Developers building conversational AI applications
- Privacy-conscious users requiring local processing

## Use Cases

### Technical Interview Assistance
- Real-time transcription of technical interview questions
- Context-aware answer suggestions for coding problems
- Post-interview review of questions and responses

### Interview Documentation
- Automatic transcription of interview sessions
- Exportable Markdown logs with timestamps
- Question/answer pairing for analysis

### Practice & Training
- Self-practice with AI-generated responses
- Review and improvement of interview performance
- Building confidence with realistic scenarios

### Accessibility
- Live captions for hearing-impaired participants
- Transcript generation for record-keeping
- Multi-language support via Whisper models
