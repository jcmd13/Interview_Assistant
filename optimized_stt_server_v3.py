import asyncio, json, os, time, re, hashlib, shutil
from typing import Set, Optional, List, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path  # For multi-OS compatibility

import numpy as np
import websockets
from faster_whisper import WhisperModel

# ========================
# Configuration
# ========================
HOST = "127.0.0.1"  # Hardcoded, removed os.getenv
PORT = 8123  # Hardcoded, removed os.getenv

SAMPLE_RATE = 16000
WINDOW_SECONDS = 6.0  # Hardcoded, removed os.getenv
HOP_SECONDS = 0.8  # Hardcoded, removed os.getenv
ENERGY_GATE = 1e-4  # Hardcoded, removed os.getenv

MODEL_NAME = "tiny"  # Hardcoded, removed os.getenv
COMPUTE_TYPE = "int8"  # Hardcoded, removed os.getenv
FORCE_LANG = None  # Hardcoded, removed os.getenv
# Generic tech prompt for better transcription of jargon
INITIAL_PROMPT = "Software engineering, data structures, algorithms, system design, cloud computing, AWS, Azure, GCP, microservices, API, CI/CD, DevOps, machine learning, data science, Python, Java, JavaScript, SQL, NoSQL, product management, agile, scrum, cloud security, SOC operations, incident response, SIEM, EDR, IAM, RBAC, zero trust."

# ========================
# LLM Configuration - OLLAMA ONLY
# ========================
LLM_ENABLED = True  # Hardcoded to True
OLLAMA_MODEL = "gpt-oss:120b-cloud"  #phi3.5:3.8b  #llama3.2 #qwen2.5:1.5b #llama3.2:1b #gemma2:2b #mistral
OLLAMA_BASE_URL = "http://localhost:11434"  # Added for Ollama
OLLAMA_MODEL_CLOUD = "gpt-oss:120b-cloud"

# ========================
# Advanced LLM Context                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       ntext Control
# ========================
LLM_INCLUDE_FULL_TRANSCRIPT = True  # Hardcoded, removed os.getenv
TECH_INTERVIEW_MODE = True  # Hardcoded, removed os.getenv
LLM_CONTEXT_MODE = "full"  # Hardcoded, removed os.getenv
LLM_WINDOW_LINES = 200  # Hardcoded, removed os.getenv
LLM_HEAD_LINES = 80  # Hardcoded, removed os.getenv
LLM_TAIL_LINES = 400  # Hardcoded, removed os.getenv
LLM_MAX_CONTEXT_CHARS = 400000  # Hardcoded, removed os.getenv
MAX_OUTTOK = 400  # Hardcoded, removed os.getenv
PERSONA = "candidate"  # Hardcoded, removed os.getenv

# ========================
# LLM Rate Limiting
# ========================
LLM_MIN_GAP_SEC = 0.5  # Hardcoded, removed os.getenv
ANSWERS_PER_MIN = 15  # Hardcoded, removed os.getenv
SEEN_TTL_SEC = 120.0  # Hardcoded, removed os.getenv
MAX_CONCURRENT_LLM = 3  # Hardcoded, removed os.getenv

# ========================
# Debug
# ========================
DEBUG = True  # Hardcoded, removed os.getenv
VERBOSE_BUFFER = False  # Hardcoded, removed os.getenv


# ========================
# Small Helpers & Context Builders (restored from French version)
# ========================
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _qkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _norm(s).lower())

def get_last_n_lines(n: int) -> List[str]:
    """Returns the last N numbered lines with their actual line numbers."""
    if n <= 0 or not transcript_lines: return []
    start_idx = max(0, len(transcript_lines) - n)
    return [f"{i+1}. {transcript_lines[i]}" for i in range(start_idx, len(transcript_lines))]

def get_head_tail_lines(head: int, tail: int) -> List[str]:
    """Returns a numbered 'head + ... + tail' to preserve global context without sending everything."""
    total = len(transcript_lines)
    if total == 0: return []
    head = max(0, min(head, total))
    tail = max(0, min(tail, total - head))
    parts = []
    for i in range(head):
        parts.append(f"{i+1}. {transcript_lines[i]}")
    if head + tail < total:
        parts.append("...")
    start_tail = max(head, total - tail)
    for i in range(start_tail, total):
        parts.append(f"{i+1}. {transcript_lines[i]}")
    return parts

def build_llm_context_text() -> str:
    """Constructs the context to send to the LLM based on LLM_CONTEXT_MODE."""
    mode = (LLM_CONTEXT_MODE or "window").lower()
    if mode == "full":
        lines = [f"{i+1}. {line}" for i, line in enumerate(transcript_lines)]
    elif mode == "headtail":
        lines = get_head_tail_lines(LLM_HEAD_LINES, LLM_TAIL_LINES)
    else:  # "window"
        lines = get_last_n_lines(LLM_WINDOW_LINES)
    
    txt = "\n".join(lines)
    if LLM_MAX_CONTEXT_CHARS and len(txt) > LLM_MAX_CONTEXT_CHARS:
        txt = txt[-LLM_MAX_CONTEXT_CHARS:]
    return txt

# ========================
# Whisper Loading with Resilient, Multi-OS Cache
# ========================
def hf_cache_dir() -> str:
    """Returns a platform-agnostic cache directory inside the user's home."""
    cache_path = Path.home() / ".cache" / "hf_models"
    cache_path.mkdir(parents=True, exist_ok=True)
    return str(cache_path)

def load_whisper_model() -> WhisperModel:
    cache_root = hf_cache_dir()
    try:
        print(f"[model] Loading {MODEL_NAME} in {cache_root}")
        return WhisperModel(MODEL_NAME, compute_type=COMPUTE_TYPE, download_root=cache_root)
    except Exception:
        model_folder_name = f"models--Systran--faster-whisper-{MODEL_NAME}"
        corrupted_path = os.path.join(cache_root, model_folder_name)
        if os.path.isdir(corrupted_path):
            print(f"[model] Corrupted cache detected, purging: {corrupted_path}")
            shutil.rmtree(corrupted_path, ignore_errors=True)
        return WhisperModel(MODEL_NAME, compute_type=COMPUTE_TYPE, download_root=cache_root)

# ========================
# LLM Response Sanitization (restored from French version)
# ========================
COACHING_PATTERNS = [
    r"\bHappy to elaborate if useful\b.*", r"\bLet me know if you'd like more details\b.*",
    r"\bYou (?:should|could|can)\b.*", r"\bYou demonstrate\b.*",
    r"\bOne (?:improvement|area to improve)\b.*", r"\bYour answer\b.*",
]

def sanitize_candidate_voice(text: str) -> str:
    for pat in COACHING_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\byou\b", "the interviewer", text, flags=re.IGNORECASE)
    text = re.sub(r"\byour\b", "the", text, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", text).strip(" .")

# ========================
# LLM Analyzer (more robust)
# ========================
@dataclass
class ConversationSegment:
    text: str; timestamp: float

@dataclass
class QuestionCandidate:
    question: str
    context: str
    timestamp: float
    confidence: float = 0.7      # ← Add default value
    urgency: str = "medium"      # ← Add default value
    topic_area: str = "general"  # ← Add default value

class ImprovedLLMAnalyzer:
    def __init__(self):
        """Initialize with Ollama only - no API keys needed"""
        self.enabled = LLM_ENABLED
        self.ollama_model = OLLAMA_MODEL_CLOUD
        self.ollama_url = OLLAMA_BASE_URL
        self.client = None
        self.previous_response_id = None
        self.last_llm_emit = 0.0
        self.seen_questions: Dict[str, float] = {}
        self.answers_timestamps = deque(maxlen=64)
        self.sem = asyncio.Semaphore(MAX_CONCURRENT_LLM)
    
        if self.enabled:
            try:
                import ollama
                # Test if Ollama is accessible
                ollama.list()
                print(f"[llm] ✅ Ready (model={OLLAMA_MODEL_CLOUD})")
            except Exception as e:
                print(f"[llm] ❌ Ollama error: {e}")
                print(f"[llm] Make sure Ollama is running: 'ollama serve'")
                print(f"[llm] And model is pulled: 'ollama pull {self.ollama_model}'")
                self.enabled = False  # Disable if Ollama is not accessible
        else:
            print("[llm] Disabled by configuration")

    def _trim_seen(self):
        now = time.time()
        expired = [k for k, t in self.seen_questions.items() if now - t > SEEN_TTL_SEC]
        for k in expired: self.seen_questions.pop(k, None)

    async def analyze_segment(self, segment: ConversationSegment) -> List[QuestionCandidate]:
        """Detect questions with context awareness"""
        if not self.enabled:
            return []

        text = segment.text.strip()

        # Broader detection for meeting support
        text_lower = text.lower()
        question_indicators = [
            "what", "how", "why", "when", "where", "which", "who", "whose",
            "can", "could", "would", "should", "will", "shall", "may", "might",
            "do", "does", "did", "is", "are", "was", "were", "has", "have",
            "tell me", "show me", "explain", "describe", "define", "clarify",
            "help me", "let me know", "any idea", "thoughts on", "opinion on"
        ]

        # More lenient pre-filter for meeting context
        has_indicator = any(indicator in text_lower for indicator in question_indicators)

        if not has_indicator and len(text.split()) < 4:
            return []

        async with self.sem:
            try:
                import ollama
                
                # Enhanced extraction prompt
                prompt = f"""Extract questions or topics that need assistance from this meeting dialogue.

                Include:
                - Direct questions
                - Implied questions or concerns
                - Topics where the speaker seems uncertain
                - Requests for information or clarification

                Return ONLY a JSON array of question strings.

                Examples:
                Input: "What's the best way to handle VPC peering?" 
                Output: ["What's the best way to handle VPC peering?"]

                Input: "I'm not sure about the security implications here."
                Output: ["What are the security implications?"]

                Input: "Hmm, how would that work with our current setup?"
                Output: ["How would that work with our current setup?"]

                Dialogue: {text}

                JSON array:"""

                response = ollama.chat(
                    model=OLLAMA_MODEL_CLOUD,  # Fast local for detection
                    messages=[
                        {'role': 'system', 'content': 'Extract questions from dialogue. Return only JSON arrays.'},
                        {'role': 'user', 'content': prompt}
                    ]
                )
                
                content = response['message']['content'].strip()
                
                # Parse JSON (same as before)
                backticks = '`' * 3  # Creates '```'
                if backticks in content:
                    parts = content.split(backticks)
                    for part in parts:
                        if part.strip().startswith('json'):
                            content = part.replace('json', '', 1).strip()
                        elif part.strip().startswith('['):
                            content = part.strip()
                
                if '[' in content:
                    start = content.index('[')
                    end = content.rindex(']') + 1
                    content = content[start:end]
                
                try:
                    questions = json.loads(content)
                    
                    if not isinstance(questions, list):
                        return []
                    
                    candidates = []
                    for q in questions[:5]:  # More questions for meeting context
                        if isinstance(q, str) and len(q.strip()) > 3:
                            q_clean = q.strip()
                            if not q_clean.endswith('?'):
                                q_clean += '?'
                            
                            candidates.append(QuestionCandidate(
                                question=q_clean,
                                context=text,
                                timestamp=time.time(),
                                confidence=0.8,
                                urgency="medium",
                                topic_area="technical"
                            ))
                    
                    if DEBUG and candidates:
                        print(f"[llm] ✅ Detected {len(candidates)} topics: {[c.question for c in candidates]}")
                    
                    return candidates
                    
                except json.JSONDecodeError:
                    return []
                
            except Exception as e:
                if DEBUG:
                    print(f"[llm] Detection error: {e}")
                return []

    async def _detect_questions(self, segment: ConversationSegment) -> List[QuestionCandidate]:
        if time.time() - self.last_llm_emit < LLM_MIN_GAP_SEC: return []
        qs = self._extract_questions_aggressive(segment.text)
        if not qs: return []
        if DEBUG: print(f"[llm] Found {len(qs)} potential questions: {[q[:40] + '...' for q in qs]}")

        candidates: List[QuestionCandidate] = []
        for q in qs:
            k = _qkey(q)
            if not k or k in self.seen_questions: continue
            
            decide = await asyncio.get_running_loop().run_in_executor(None, self._should_answer, q)
            if decide.get("should_answer"):
                self.seen_questions[k] = time.time()
                cand = QuestionCandidate(
                    question=q, context=segment.text, confidence=decide.get("confidence", 0.7),
                    urgency="relevant", topic_area="interview", timestamp=segment.timestamp, should_answer=True,
                )
                candidates.append(cand)
                if DEBUG: print(f"[llm] Will answer: {q}")
        return candidates[:3]

    def _extract_questions_aggressive(self, text: str) -> List[str]:
        """Advanced 6-stage question extraction (restored from French version)."""
        text = _norm(text)
        if not text: return []
        sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', text) if s.strip()]
        questions: List[str] = []
        for s in sentences:
            if s.endswith("?") and len(s.split()) >= 5: questions.append(s)
        
        head_terms = ["what","how","why","when","where","which","who","can you","could you","tell me","explain"]
        for s in sentences:
            sl = s.lower()
            if any(sl.startswith(term + " ") for term in head_terms) and len(s.split()) >= 6:
                questions.append(s if s.endswith("?") else s + "?")

        seen = set(); clean: List[str] = []
        for q in questions:
            k = _qkey(q)
            if k and k not in seen:
                seen.add(k)
                clean.append(q.strip(" ,;:-–—"))
        return clean[:3]

    def _should_answer(self, question: str) -> Dict[str, Any]:
        """Determine if we should answer this question"""
        if not self.enabled:
            return {"should_answer": False}
        
        # Rate limiting check
        now = time.time()
        while self.answers_timestamps and now - self.answers_timestamps[0] > 60:
            self.answers_timestamps.popleft()
        
        if len(self.answers_timestamps) >= ANSWERS_PER_MIN:
            if DEBUG:
                print(f"[llm] Rate limit reached ({ANSWERS_PER_MIN}/min)")
            return {"should_answer": False}
        
        # Improved heuristic check
        ql = question.lower().strip()
        
        # Strong question indicators
        question_words = ["what", "how", "why", "when", "where", "which", "who"]
        auxiliary_verbs = ["can", "could", "would", "should", "do", "does", "did", "is", "are", "was", "were", "will"]
        
        looks_like_q = (
            ql.endswith("?") or
            any(ql.startswith(w + " ") for w in question_words) or
            any(ql.startswith(w + " you") for w in auxiliary_verbs) or
            any(phrase in ql for phrase in ["tell me", "explain", "describe", "define"])
        )
        
        # Reject very short non-questions
        if not looks_like_q and len(question.split()) < 4:
            return {"should_answer": False}
        
        # For clear questions, answer immediately
        if ql.endswith("?") or any(ql.startswith(w + " ") for w in question_words):
            ts = time.time()
            self.last_llm_emit = ts
            self.answers_timestamps.append(ts)
            return {"should_answer": True, "confidence": 0.9}
        
        # For ambiguous cases, use Ollama (simplified)
        if looks_like_q:
            try:
                import ollama
                response = ollama.chat(
                    model=OLLAMA_MODEL_CLOUD,
                    messages=[
                        {'role': 'system', 'content': "Is this an interview question? Answer only YES or NO."},
                        {'role': 'user', 'content': question}
                    ]
                )
                out = response['message']['content'].strip().lower()
                decided_yes = "yes" in out
                
            except Exception:
                decided_yes = looks_like_q
            
            if decided_yes:
                ts = time.time()
                self.last_llm_emit = ts
                self.answers_timestamps.append(ts)
            
            return {"should_answer": decided_yes, "confidence": 0.7}
        
        return {"should_answer": False}

    async def _gen(self, candidate: QuestionCandidate) -> str:
        """Generate contextually-aware answer using Ollama Cloud"""
        try:
            import ollama
        
            q = (candidate.question or "").strip()
            
            if DEBUG:    
                print(f"[llm] 🌩️  Using MODEL: {OLLAMA_MODEL_CLOUD}")
        
            # Build system prompt based on persona
            if PERSONA == "candidate":
                system_prompt = """You are an expert AI assistant helping during a professional meeting or call.

                ROLE: Provide intelligent, contextually-aware support in real-time.

                OUTPUT STYLE:
                - Use first-person ("I would...") when asked about your opinion
                - Use second-person ("You could...") when giving advice
                - Provide 2-4 concise, actionable points
                - Include specific examples or references when relevant
                - Be professional but conversational
                - Format: Brief intro + 2-3 key points + optional suggestion

                CONTEXT AWARENESS:
                - Track conversation flow from the transcript
                - Reference previous discussion points when relevant
                - Adapt tone to match meeting context (formal vs. casual)
                - Prioritize actionable information over theory

                AVOID:
                - Long paragraphs or lectures
                - Bullet point lists (use flowing sentences)
                - Coaching language ("Let me explain...")
                - Overly technical jargon unless context demands it"""
            else:
                system_prompt = """You are a helpful meeting assistant. 
                Provide brief, contextual answers in 2-3 sentences.
                Be concise and actionable.""" 
        
            # Build enhanced context
            context_parts = []
            
            # Include conversation history for context awareness
            if LLM_INCLUDE_FULL_TRANSCRIPT:
                full_tx = build_llm_context_text()
                if full_tx:
                    recent_context = full_tx[-3000:]  # Last ~3000 chars
                    context_parts.append(f"Recent conversation:\n{recent_context}")
            
            # Add domain context
            if TECH_INTERVIEW_MODE:
                context_parts.append("Domain: Cloud computing, AWS, security, system design, software engineering, DevOps, infrastructure.")
            
            # Add current question with emphasis
            context_parts.append(f"Current question: {q}")
            context_parts.append("Provide a helpful, contextual response that fits naturally into the ongoing conversation.")
            
            user_content = "\n\n".join(context_parts)
            
            # Use cloud model for high-quality contextual answers
            response = ollama.chat(
                model=OLLAMA_MODEL_CLOUD,  # Cloud for best quality
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_content}
                ]
            )
            
            raw_text = response['message']['content'].strip()
            
            # Light sanitization (preserve conversational flow)
            cleaned = sanitize_candidate_voice(raw_text)
            
            if not cleaned.strip():
                if DEBUG:
                    print("[llm] Response was empty, using fallback...")
                return "Let me think about that. Based on the context, I'd suggest starting with a proof-of-concept to validate the approach."
        
            if DEBUG:
                print(f"[llm] Generated contextual answer ({len(cleaned)} chars)")
            
            return cleaned
            
        except Exception as e:
            error_msg = f"[Answer error] {str(e)[:120]}"
            if DEBUG:
                print(f"[llm] Generation error: {e}")
            return error_msg


# ========================
# Global Server State
# ========================
@dataclass
class ClientState:
    ws: websockets.WebSocketServerProtocol; queue: asyncio.Queue
    sender_task: Optional[asyncio.Task] = None; wants_broadcast: bool = True; role: str = "ui"

clients: Dict[websockets.WebSocketServerProtocol, ClientState] = {}
latest_text, sentence_buf = "", ""
detected = deque(maxlen=500); qa_log = deque(maxlen=200)
transcript_lines: List[str] = []
MAX_TRANSCRIPT_LINES = int(os.getenv("STT_MAX_TRANSCRIPT_LINES", "5000"))
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.?!])\s+')
pcm_buf = bytearray(); bytes_since_last = 0
WIN_BYTES = int(SAMPLE_RATE * 2 * WINDOW_SECONDS); HOP_BYTES = int(SAMPLE_RATE * 2 * HOP_SECONDS)
MAX_BUFFER_BYTES = WIN_BYTES * 2
audio_lock = asyncio.Lock(); server_shutdown = asyncio.Event(); transcriber_task: Optional[asyncio.Task] = None

# ========================
# Broadcast & WebSocket Handling
# ========================
async def _client_sender(client: ClientState):
    try:
        while True: await client.ws.send(await client.queue.get())
    except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError): pass
    finally:
        try: await client.ws.close()
        except Exception: pass

async def broadcast(data: dict):
    if not clients: return
    msg = json.dumps(data, ensure_ascii=False)
    for c in list(clients.values()):
        if c.wants_broadcast:
            try:
                if c.queue.full(): _ = c.queue.get_nowait()
                c.queue.put_nowait(msg)
            except Exception: clients.pop(c.ws, None)

async def handler(ws: websockets.WebSocketServerProtocol):
    global transcriber_task, bytes_since_last
    print(f"[ws] Client connected from {ws.remote_address}")
    client = ClientState(ws=ws, queue=asyncio.Queue(maxsize=100))
    client.sender_task = asyncio.create_task(_client_sender(client))
    clients[ws] = client

    try:
        await ws.send(json.dumps({"snapshot": {"transcript": latest_text, "detected": list(detected), "lines": transcript_lines[-200:]}}))
    except Exception: pass

    if transcriber_task is None or transcriber_task.done():
        transcriber_task = asyncio.create_task(read_and_transcribe_loop())

    try:
        async for msg in ws:
            if isinstance(msg, (bytes, bytearray)):
                async with audio_lock:
                    pcm_buf.extend(msg); bytes_since_last += len(msg)
                    if len(pcm_buf) > MAX_BUFFER_BYTES: del pcm_buf[:len(pcm_buf) - MAX_BUFFER_BYTES // 2]
            else:
                try:
                    data = json.loads(msg)
                    cmd = (data.get("cmd") or "").lower()
                    if cmd == "hello" and (data.get("client") or "").lower() in ("audio_streamer", "ingest"):
                        client.wants_broadcast = False
                        if DEBUG: print(f"[ws] Marked {ws.remote_address} as streamer; broadcasts OFF")
                    elif cmd == "reset":
                        async with audio_lock: pcm_buf.clear(); bytes_since_last = 0
                        reset_state(); print("[ws] Reset completed")
                except Exception: pass
    except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError): pass
    finally:
        clients.pop(ws, None)
        if client.sender_task: client.sender_task.cancel()
        print("[ws] Client disconnected")

# ========================
# Global Transcriber Loop
# ========================
async def read_and_transcribe_loop():
    global bytes_since_last, latest_text, sentence_buf, transcript_lines
    loop, last_hashes, process_count = asyncio.get_running_loop(), deque(maxlen=8), 0
    print("[stt] Transcription loop started (global)")
    PROMPT_WORDS = {w.strip(".,").lower() for w in INITIAL_PROMPT.split()} if INITIAL_PROMPT else set()

    while not server_shutdown.is_set():
        await asyncio.sleep(0.05)
        async with audio_lock:
            if not (bytes_since_last >= HOP_BYTES and len(pcm_buf) >= WIN_BYTES): continue
            bytes_since_last = 0; window_bytes = bytes(pcm_buf[-WIN_BYTES:])
        
        arr = np.frombuffer(window_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if np.mean(arr*arr) < ENERGY_GATE: continue
        
        def _transcribe():
            try:
                segments, _ = whisper.transcribe(arr, language=FORCE_LANG, vad_filter=True, initial_prompt=INITIAL_PROMPT if not latest_text else None)
                return list(segments)
            except Exception as e:
                print(f"[stt] Transcription error: {e}"); return []

        segments = await loop.run_in_executor(None, _transcribe)
        if not segments: continue

        for segment in segments:
            text = _norm(segment.text)
            if not text or len(text) < 2: continue
            
            # Advanced filtering (restored from French version)
            toks = [w.strip(".,").lower() for w in text.split()]
            if toks and PROMPT_WORDS and sum(1 for w in toks if w in PROMPT_WORDS) / max(1, len(toks)) > 0.6:
                if DEBUG: print("[stt] Dropped segment: initial_prompt echo")
                continue
            if re.search(r"\b(\w+(?:,\s*\w+){1,})\b(?:\s+\1\b){2,}", text, flags=re.I):
                if DEBUG: print("[stt] Dropped segment: repetitive phrase")
                continue

            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            if h in last_hashes: continue
            last_hashes.append(h)

            sentence_buf = (sentence_buf + " " + text).strip()
            parts = SENTENCE_SPLIT_RE.split(sentence_buf)
            
            complete = parts[:-1] if len(parts) > 1 and sentence_buf[-1] not in ".?!" else (parts if sentence_buf and sentence_buf[-1] in ".?!" else [])
            sentence_buf = "" if complete == parts else parts[-1]
            latest_text = sentence_buf

            for s in complete:
                s = _norm(s)
                if not s: continue
                transcript_lines.append(s)
                if len(transcript_lines) > MAX_TRANSCRIPT_LINES: del transcript_lines[:MAX_TRANSCRIPT_LINES // 10]
                if DEBUG: print(f"[stt] Line: {s}")
                await broadcast({"line": {"n": len(transcript_lines), "text": s}})
            
            await broadcast({"partial": text})

            if llm_analyzer and llm_analyzer.enabled:
                try:
                    cands = await llm_analyzer.analyze_segment(ConversationSegment(text=text, timestamp=time.time()))
                    for cand in cands:
                        item = {"q": cand.question, "t": int(cand.timestamp * 1000), "a": None}
                        detected.append(item)
                        await broadcast({"question_detected": item})
                        ans = await llm_analyzer._gen(cand)
                        item["a"] = ans; qa_log.append(item)
                        await broadcast({"qa": item})
                        if DEBUG: print(f"[llm] Response: {ans[:60]}...")
                except Exception as e:
                    print(f"[llm] Analysis error: {e}")

# ========================
# Utilities & Main
# ========================
def reset_state():
    global latest_text, sentence_buf, transcript_lines
    latest_text, sentence_buf = "", ""; transcript_lines.clear(); detected.clear(); qa_log.clear()
    if llm_analyzer:
        llm_analyzer.seen_questions.clear(); llm_analyzer.answers_timestamps.clear()

async def main():
    global whisper, llm_analyzer
    print("🚀 OPTIMIZED STT SERVER V4 (Best of Both Worlds)")
    print("=" * 50)
    print("[startup] Loading Whisper model..."); whisper = load_whisper_model()
    print("[startup] Initializing LLM Analyzer..."); llm_analyzer = ImprovedLLMAnalyzer()
    print(f"\n📋 CONFIG: LLM {'Enabled' if llm_analyzer.enabled else 'Disabled'}, Debug {'ON' if DEBUG else 'OFF'}")

    try:
        async with websockets.serve(handler, HOST, PORT, max_size=2**20, ping_interval=10, ping_timeout=30):
            print(f"\n🎤 Server ready on ws://{HOST}:{PORT}/"); await asyncio.Future()
    except Exception as e:
        print(f"[error] Server failed to start: {e}")

if __name__ == "__main__":
    try:
        whisper: WhisperModel; llm_analyzer: Optional[ImprovedLLMAnalyzer]
        asyncio.run(main())
    except KeyboardInterrupt:
        server_shutdown.set(); print("\n[shutdown] Server stopped.")
    except Exception as e:
        print(f"\n[fatal_error] {e}"); import traceback; traceback.print_exc()
