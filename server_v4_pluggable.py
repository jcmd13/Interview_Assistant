#!/usr/bin/env python3
"""
Interview Assistant Server v4 - Plugin-Aware Edition

This is a lightweight, modular server that uses the plugin system for all
major components:
- Transcription (pluggable Whisper models)
- LLM Analysis (pluggable Ollama models)
- Question Detection (plugin-based)
- Settings Management (runtime configuration)

Architecture:
- All components loaded via plugin system
- Hot-swappable without restart for model changes
- Settings API for configuration management
- Clean separation of concerns

Usage:
    python server_v4_pluggable.py
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, List
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path

import websockets
import numpy as np

from src.core.logger import get_logger, configure_logging
from src.core.config import get_config
from src.server.plugin_integration import (
    PluginTranscriber,
    PluginLLMAnalyzer,
    PluginManager,
    initialize_plugin_system,
)
from src.server.settings_api import SettingsManager

# Configure structured logging
configure_logging(log_level="INFO", json_output=True, pretty_print=False)
logger = get_logger("server.v4")

# =====================
# Configuration
# =====================
cfg = get_config()
HOST = cfg.server.host
PORT = cfg.server.port
SAMPLE_RATE = cfg.audio.sample_rate
WINDOW_SECONDS = cfg.audio.window_seconds
HOP_SECONDS = cfg.audio.hop_seconds
ENERGY_GATE = cfg.audio.energy_gate
DEBUG = cfg.debug.debug

# =====================
# Global State
# =====================
transcript_lines: List[str] = []
pcm_buf = np.zeros(int(SAMPLE_RATE * WINDOW_SECONDS), dtype=np.float32)
bytes_since_last = 0
ui_clients: Set = set()
transcriber: Optional[PluginTranscriber] = None
llm_analyzer: Optional[PluginLLMAnalyzer] = None
plugin_manager: Optional[PluginManager] = None
settings_manager: Optional[SettingsManager] = None
detected_questions: deque = deque(maxlen=50)
qa_log: Dict[str, str] = {}


@dataclass
class TranscriptionResult:
    """Result from transcription"""
    text: str
    start_time: float
    duration: float
    word_count: int


@dataclass
class QuestionDetected:
    """Question detected in transcript"""
    question: str
    timestamp: float
    context: str


async def broadcast_to_ui(event_type: str, data: Any):
    """Broadcast event to all connected UI clients"""
    if not ui_clients:
        return

    message = {
        "type": event_type,
        "timestamp": asyncio.get_event_loop().time(),
        "data": data
    }

    disconnected = set()
    for client in ui_clients:
        try:
            await client.send(json.dumps(message))
        except Exception:
            disconnected.add(client)

    # Clean up disconnected clients
    for client in disconnected:
        ui_clients.discard(client)


async def handle_transcription_result(result: TranscriptionResult):
    """Handle new transcription result"""
    global transcript_lines

    logger.info("transcription_result", text=result.text, duration=result.duration)

    # Add to transcript
    transcript_lines.append(result.text)

    # Broadcast to UI
    await broadcast_to_ui("transcript_update", {
        "text": result.text,
        "line_number": len(transcript_lines),
        "word_count": result.word_count,
    })

    # Check for questions
    await analyze_for_questions(result.text)


async def analyze_for_questions(text: str):
    """Analyze transcribed text for questions"""
    global detected_questions, qa_log

    if not llm_analyzer:
        return

    try:
        # Build context from recent transcript
        context_lines = transcript_lines[-20:] if len(transcript_lines) > 20 else transcript_lines
        context = "\n".join(context_lines)

        # Analyze
        analysis = await llm_analyzer.analyze_segment(text, context)

        if analysis and "questions" in analysis:
            for question in analysis["questions"]:
                # Avoid duplicates
                q_key = question.lower().strip()
                if q_key not in qa_log:
                    detected_q = QuestionDetected(
                        question=question,
                        timestamp=asyncio.get_event_loop().time(),
                        context=context,
                    )
                    detected_questions.append(detected_q)
                    qa_log[q_key] = ""  # Placeholder for answer

                    logger.info("question_detected", question=question)

                    # Broadcast to UI
                    await broadcast_to_ui("question_detected", asdict(detected_q))

                    # Generate answer
                    await generate_answer_for_question(question, context)

    except Exception as e:
        logger.error("question_analysis_failed", error=str(e))


async def generate_answer_for_question(question: str, context: str):
    """Generate LLM answer for detected question"""
    if not llm_analyzer:
        return

    try:
        logger.info("generating_answer", question=question)
        answer = await llm_analyzer.generate_answer(question, context, max_tokens=400)

        if answer:
            q_key = question.lower().strip()
            qa_log[q_key] = answer

            logger.info("answer_generated", question=question, answer_length=len(answer))

            # Broadcast to UI
            await broadcast_to_ui("answer_generated", {
                "question": question,
                "answer": answer,
                "timestamp": asyncio.get_event_loop().time(),
            })

    except Exception as e:
        logger.error("answer_generation_failed", error=str(e), question=question)


async def handle_audio_data(data: bytes):
    """Process incoming audio data"""
    global pcm_buf, bytes_since_last

    if len(data) % 2 != 0:
        return

    # Convert to float32
    audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

    # Shift buffer and add new data
    chunk_len = len(audio_chunk)
    buf_len = len(pcm_buf)

    if chunk_len >= buf_len:
        pcm_buf = audio_chunk[-buf_len:].copy()
    else:
        pcm_buf = np.roll(pcm_buf, -chunk_len)
        pcm_buf[-chunk_len:] = audio_chunk

    bytes_since_last += len(data)

    # Check if we should transcribe (every HOP_SECONDS)
    hop_bytes = int(HOP_SECONDS * SAMPLE_RATE * 2)  # 2 bytes per sample
    if bytes_since_last >= hop_bytes:
        bytes_since_last = 0
        await transcribe_current_window()


async def transcribe_current_window():
    """Transcribe current audio window"""
    global pcm_buf, transcriber

    if transcriber is None:
        return

    try:
        # Check energy gate
        rms = np.sqrt(np.mean(pcm_buf ** 2))
        if rms < ENERGY_GATE:
            return  # Skip silence

        # Transcribe
        result = await transcriber.transcribe(pcm_buf)

        if result and "text" in result:
            text = result["text"].strip()
            if text:
                await handle_transcription_result(
                    TranscriptionResult(
                        text=text,
                        start_time=asyncio.get_event_loop().time(),
                        duration=WINDOW_SECONDS,
                        word_count=len(text.split()),
                    )
                )

    except Exception as e:
        logger.error("transcription_failed", error=str(e))


async def handle_websocket(ws: websockets.WebSocketServerProtocol, path: str):
    """Handle incoming WebSocket connection"""
    try:
        # Get first message to identify client type
        first_msg = await ws.recv()
        msg = json.loads(first_msg)

        if msg.get("client") == "audio_streamer":
            # Audio streaming client
            logger.info("audio_client_connected")
            try:
                async for message in ws:
                    if isinstance(message, bytes):
                        await handle_audio_data(message)
                    else:
                        # JSON command
                        try:
                            cmd = json.loads(message)
                            if cmd.get("cmd") == "reset":
                                global transcript_lines, pcm_buf, qa_log
                                transcript_lines.clear()
                                pcm_buf.fill(0)
                                qa_log.clear()
                                logger.info("state_reset")
                        except json.JSONDecodeError:
                            pass
            finally:
                logger.info("audio_client_disconnected")

        else:
            # UI or admin client
            logger.info("ui_client_connected")
            ui_clients.add(ws)

            try:
                # Send initial state
                await ws.send(json.dumps({
                    "type": "snapshot",
                    "transcript": transcript_lines,
                    "questions": [asdict(q) for q in detected_questions],
                    "qa_log": qa_log,
                }))

                # Handle commands from UI
                async for message in ws:
                    try:
                        cmd = json.loads(message)
                        await handle_ui_command(ws, cmd)
                    except json.JSONDecodeError:
                        pass

            finally:
                ui_clients.discard(ws)
                logger.info("ui_client_disconnected")

    except Exception as e:
        logger.error("websocket_handler_error", error=str(e))


async def handle_ui_command(ws: websockets.WebSocketServerProtocol, cmd: Dict[str, Any]):
    """Handle commands from UI/admin clients"""
    cmd_type = cmd.get("cmd")

    if cmd_type == "get_settings":
        # Return current settings
        if settings_manager:
            await ws.send(json.dumps({
                "type": "settings",
                "data": settings_manager.get_all_settings(),
            }))

    elif cmd_type == "set_setting":
        # Update a setting
        key = cmd.get("key")
        value = cmd.get("value")
        if settings_manager:
            try:
                settings_manager.set_setting(key, value)
                await ws.send(json.dumps({
                    "type": "setting_updated",
                    "key": key,
                    "value": value,
                }))
                logger.info("setting_changed", key=key, value=value)
            except Exception as e:
                await ws.send(json.dumps({
                    "type": "error",
                    "message": f"Failed to set {key}: {str(e)}",
                }))

    elif cmd_type == "swap_transcriber_model":
        # Hot-swap Whisper model
        model = cmd.get("model")
        if transcriber:
            try:
                await transcriber.reload_model(model)
                await broadcast_to_ui("model_changed", {
                    "component": "transcriber",
                    "model": model,
                })
                logger.info("transcriber_model_swapped", model=model)
            except Exception as e:
                logger.error("transcriber_swap_failed", error=str(e))

    elif cmd_type == "swap_llm_model":
        # Hot-swap LLM model
        model = cmd.get("model")
        if llm_analyzer:
            try:
                await llm_analyzer.reload_model(model)
                await broadcast_to_ui("model_changed", {
                    "component": "llm",
                    "model": model,
                })
                logger.info("llm_model_swapped", model=model)
            except Exception as e:
                logger.error("llm_swap_failed", error=str(e))

    elif cmd_type == "get_plugins":
        # List available plugins
        if plugin_manager:
            plugins = plugin_manager.list_plugins()
            await ws.send(json.dumps({
                "type": "plugin_list",
                "plugins": {name: asdict(status) for name, status in plugins.items()},
            }))

    elif cmd_type == "reset":
        # Reset state
        global transcript_lines, pcm_buf, qa_log
        transcript_lines.clear()
        pcm_buf.fill(0)
        qa_log.clear()
        detected_questions.clear()
        logger.info("server_state_reset")


async def main():
    """Main server startup"""
    global transcriber, llm_analyzer, plugin_manager, settings_manager

    logger.info("server_starting", host=HOST, port=PORT)

    # Initialize plugin system
    plugin_manager = PluginManager()
    await initialize_plugin_system()

    # Initialize components
    transcriber = PluginTranscriber()
    transcriber.initialize(cfg.whisper.model_name)
    logger.info("transcriber_initialized")

    llm_analyzer = PluginLLMAnalyzer()
    llm_analyzer.initialize(cfg.ollama.model_cloud)
    logger.info("llm_analyzer_initialized")

    # Initialize settings manager
    settings_manager = SettingsManager()
    logger.info("settings_manager_initialized")

    # Start WebSocket server
    async with websockets.serve(handle_websocket, HOST, PORT):
        logger.info("server_ready", host=HOST, port=PORT, endpoint=f"ws://{HOST}:{PORT}")
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("server_shutdown")


if __name__ == "__main__":
    asyncio.run(main())
