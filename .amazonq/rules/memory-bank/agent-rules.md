# Kiro Agent Behavior Rules - Interview Assistant Project

## Project Context

**System**: Real-time AI interview assistant with career development platform foundation
**Target Platform**: macOS (primary), cross-platform compatible
**Core Philosophy**: Performance-first, zero-friction setup, complete modularity, glanceable UI, career-focused AI
**User**: Job seekers, interview candidates, business professionals, customer success teams
**Business Model**: Freemium SaaS (free core tool, premium career services future)

## Critical Performance Metric

**THE PRIMARY PERFORMANCE INDICATOR**: End-to-end latency from question asked → usable LLM answer displayed

**Target Latency Budget**:
- Audio capture to transcription: < 500ms
- Question detection: < 100ms
- LLM response generation: < 3s (target: 1.5s)
- Term explanation (optional): < 200ms additional
- **TOTAL END-TO-END**: < 4s from question spoken to answer displayed

All architectural decisions must optimize for this latency chain.

## Priority Hierarchy

When requirements conflict, prioritize in this order:
1. **Performance** (end-to-end latency)
2. **Modularity** (plugin architecture, swappable components)
3. **Zero-Friction UX** (works out-of-box, minimal interaction)
4. **Security** (credential storage, input validation, plugin sandboxing)
5. **User Experience** (glanceable UI, adaptive density)
6. **Features** (additional capabilities)

---

## Critical Agent Behaviors

### 1. Performance-First Decision Making

**DO:**
- ✅ Measure end-to-end latency for every change
- ✅ Use fastest available solution within cost constraints (free tier only)
- ✅ Prefer Ollama with cloud-routed models when API key provided (faster than local)
- ✅ Batch LLM prompts when possible (e.g., question + term explanations in one call)
- ✅ Implement caching for term definitions, customer context
- ✅ Use async/await throughout for non-blocking I/O
- ✅ Pre-warm LLM models at startup
- ✅ Stream LLM responses for progressive display

**DON'T:**
- ❌ Add features that increase latency >200ms without explicit justification
- ❌ Make synchronous API calls in the critical path
- ❌ Fetch data that could be cached
- ❌ Use threads when asyncio is available
- ❌ Implement features requiring paid services without free fallback

### 2. Zero-Configuration Installation

**DO:**
- ✅ Bundle Ollama installer in main application installer
- ✅ Auto-install Ollama if not present (no user prompt needed)
- ✅ Download default local model automatically (qwen2.5:1.5b)
- ✅ Test that system works immediately after install (no configuration)
- ✅ Detect environment (audio devices, Ollama status, network) on first launch
- ✅ Select optimal defaults automatically
- ✅ Work completely offline with local-only processing

**DON'T:**
- ❌ Require user to pre-install Ollama
- ❌ Require user to create accounts for core functionality
- ❌ Block core features on configuration or API keys
- ❌ Assume internet connectivity for basic operation

### 3. Smart Onboarding (Optional Enhancement)

**DO:**
- ✅ Make ALL onboarding steps optional and skippable
- ✅ Explain value clearly ("Why this helps") before asking for data
- ✅ Validate API keys immediately with visual feedback
- ✅ Store credentials in OS keychain (macOS Keychain, Windows Credential Manager)
- ✅ Remember user preferences for future sessions
- ✅ Pre-fill session context from clipboard when possible

**DON'T:**
- ❌ Block usage if onboarding is skipped
- ❌ Store API keys in plaintext config files
- ❌ Require configuration before system can be used
- ❌ Show onboarding every time (once per install)

### 4. Complete Plugin Modularity

**DO:**
- ✅ Implement ALL components as plugins (audio, transcription, LLM, UI, CRM)
- ✅ Use abstract interfaces defined in design.md
- ✅ Support hot-swapping plugins at runtime without restart
- ✅ Get all configuration from ConfigurationService (never hardcode)
- ✅ Register plugins with PluginRegistry for discovery
- ✅ Validate plugin compatibility and dependencies at load time
- ✅ Sandbox plugins to prevent system access abuse

**DON'T:**
- ❌ Create direct dependencies between plugins
- ❌ Hardcode plugin selection (always config-driven)
- ❌ Skip interface implementation (implement ALL required methods)
- ❌ Allow plugins to access system resources without permission

### 5. Glanceable, Zero-Interaction UI

**DO:**
- ✅ Use visual hierarchy to convey importance (size, color, position)
- ✅ Show critical info automatically (questions, answers, key terms)
- ✅ Auto-hide/fade less important content (transcript, settings)
- ✅ Implement progressive disclosure (info appears when relevant)
- ✅ Adapt UI density to context (camera on = stealth, phone call = expansive)
- ✅ Use consistent color coding (blue=question, green=answer, yellow=term, red=alert)
- ✅ Bold first sentence of answers for quick scanning
- ✅ Highlight key phrases automatically

**DON'T:**
- ❌ Require clicking/scrolling to see critical information
- ❌ Show all information at once (causes cognitive overload)
- ❌ Use color alone to distinguish critical info (accessibility)
- ❌ Add UI elements that distract during live conversation
- ❌ Force user to manage UI during active interview/call

### 6. Card-Based Modular Layout

**DO:**
- ✅ Implement grid-based card system (20rem columns x 1rem rows)
- ✅ Support drag-and-drop card repositioning
- ✅ Enable card resizing with snap-to-grid behavior
- ✅ Provide layout presets (Interview Stealth, Phone Call, Business Meeting, Customer Call)
- ✅ Allow saving custom layouts with names
- ✅ Support hotkeys for quick layout switching (Ctrl+1, Ctrl+2, etc.)
- ✅ Maintain aspect ratios during window resize

**DON'T:**
- ❌ Force fixed layout (must be customizable)
- ❌ Lose layout settings between sessions
- ❌ Allow cards to overlap without user intent
- ❌ Require manual layout configuration (good defaults)

### 7. Intelligent Term/Acronym Handling

**DO:**
- ✅ Detect acronyms and industry jargon automatically
- ✅ Explain terms inline or via tooltip on first mention
- ✅ Make term explanations toggleable (session settings)
- ✅ Batch explanations with existing LLM prompts (no extra latency)
- ✅ Skip explanations if latency budget exceeded (>3000ms)
- ✅ Cache definitions for session (no duplicate API calls)
- ✅ Show terms in dedicated collapsible card

**DON'T:**
- ❌ Explain same term multiple times per session
- ❌ Make separate LLM call for each term (batch them)
- ❌ Add term explanations if it breaks latency budget
- ❌ Force term explanations when user disabled feature

### 8. CRM Integration for Business Use

**DO:**
- ✅ Detect CRM-linked calls automatically (phone number, email match)
- ✅ Fetch customer context asynchronously (non-blocking)
- ✅ Support Salesforce and Microsoft Dynamics 365
- ✅ Inject customer context into LLM prompts automatically
- ✅ Display customer profile, account value, last interaction, open cases
- ✅ Use AI to detect upsell opportunities and churn risk
- ✅ Suggest personalized talking points based on customer history
- ✅ Make CRM integration optional plugin

**DON'T:**
- ❌ Block call start waiting for CRM data (load async)
- ❌ Hard-code CRM provider (use plugin interface)
- ❌ Store CRM credentials insecurely
- ❌ Require CRM for interview use cases

### 9. Structured Logging from Day One

**DO:**
- ✅ Use structured JSON logging with timing metadata
- ✅ Log every pipeline stage with duration (audio, transcription, detection, LLM, UI)
- ✅ Include component name, log level, timestamp, message, metadata in every entry
- ✅ Provide verbose mode for detailed debugging
- ✅ Use clear, actionable error messages for users (not stack traces)
- ✅ Log security events (auth, config changes, plugin loads)
- ✅ Track performance metrics (p50, p95, p99 latencies)

**DON'T:**
- ❌ Add logging as afterthought (design in from start)
- ❌ Show technical errors to users (log internally, show friendly message)
- ❌ Skip timing data in logs
- ❌ Use print() statements (use proper logging library)

### 10. Security from Day One

**DO:**
- ✅ Validate all user inputs and external data
- ✅ Store credentials in OS keychain (encrypted)
- ✅ Sandbox plugins from system and each other
- ✅ Use TLS for all network calls
- ✅ Implement rate limiting for API calls
- ✅ Audit log security-relevant events
- ✅ Encrypt sensitive local data (resume, PII)

**DON'T:**
- ❌ Store credentials in plaintext
- ❌ Allow arbitrary code execution from plugins
- ❌ Skip input validation
- ❌ Add security as afterthought

### 11. Privacy-First Data Strategy

**DO:**
- ✅ Process everything locally by default (data stays on device)
- ✅ Require explicit opt-in for ANY data collection
- ✅ Show transparently what data is collected and why
- ✅ Provide easy export/deletion of all user data
- ✅ Anonymize data before sharing (if user opts in)
- ✅ Auto-delete transcripts after 7 days (configurable)
- ✅ Support fully offline mode

**DON'T:**
- ❌ Collect data without explicit user consent
- ❌ Require cloud services for core functionality
- ❌ Share data with third parties without permission
- ❌ Make privacy settings hard to find

---

## Quality Gates

### Before Marking Task Complete

✅ Works without any user configuration (local-only mode tested)
✅ Onboarding flow is optional and skippable
✅ API keys stored securely (OS keychain)
✅ Plugin interface implemented completely (all required methods)
✅ Plugin registered with discovery system
✅ Configuration externalized (no hardcoded values)
✅ Structured logging with timing data
✅ End-to-end latency measured and within budget
✅ Privacy controls clearly explained
✅ Fallback behavior works when dependencies unavailable
✅ Error handling with clear user messages
✅ Input validation for external data
✅ Unit tests written (for tasks marked with * in tasks.md)
✅ Accessibility considered (color not sole indicator)
✅ Database schema includes future service hooks (if applicable)

---

## Success Metrics

- **Critical**: End-to-end latency < 4s (p95)
- Toolbar < 400x150px in stealth mode
- Zero interaction during meetings
- Invisible to screen sharing/recording
- Plugins hot-swappable
- Works on fresh macOS install
- Structured logging throughout
- Memory stable, CPU < 10%

---

## Final Directive

When in doubt:
1. **Measure latency** - End-to-end is the only metric that matters
2. **Check requirements.md** for SHALL statements
3. **Check design.md** for plugin interfaces
4. **Check tasks.md** for dependencies
5. **Default to**: Fastest (free tier), Modular, Zero-config, Glanceable, Logged, Secure, Private

**Core Principle**: This tool must respond fast enough to be useful during live interviews while being invisible/non-distracting. Every decision must consider: "Does this increase latency or require user attention?" If yes, justify explicitly.
