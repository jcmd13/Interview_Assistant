# Specification Changes for Kiro Implementation
## Based on Full Conversation History

This document outlines ALL requested changes to requirements.md, design.md, and tasks.md based on the complete conversation.

---

## Section 1: Installation & Zero-Configuration

### Changes to Requirements.md

**NEW REQUIREMENT: REQ-INSTALL-001 - Bundled Ollama Installation**
The system SHALL bundle Ollama installation within the main application installer and automatically install Ollama if not present on the target system, requiring no user interaction.

**Acceptance Criteria**:
- Installer detects if Ollama is present
- If absent, automatically downloads and installs Ollama (macOS .dmg, Windows .exe, Linux curl script)
- Downloads default local model (qwen2.5:1.5b) automatically
- System is functional immediately after installation with no configuration
- Works completely offline with local-only processing

**NEW REQUIREMENT: REQ-INSTALL-002 - Zero Prerequisites**
The system SHALL NOT require users to:
- Pre-install Ollama manually
- Create accounts (ollama.com, OpenAI, etc.) for core functionality
- Configure any settings before first use
- Have internet connectivity for basic operation

**Acceptance Criteria**:
- Fresh install on clean macOS/Windows/Linux works immediately
- No account creation prompts block usage
- Local-only mode (Tier 1) is default
- All core features (audio, transcription, question detection, answer generation) work without configuration

---

## Section 2: Smart Onboarding Flow

### Changes to Requirements.md

**NEW REQUIREMENT: REQ-ONBOARD-001 - Three-Phase Progressive Onboarding**
The system SHALL implement a three-phase onboarding flow where ALL phases are optional and skippable:

**Phase 1 - LLM/API Setup (2 minutes, optional)**:
- Option to add Ollama Cloud API key (free tier) for faster responses
- Option to add OpenAI/Anthropic keys for premium quality
- Option to keep local-only processing
- Immediate key validation with visual feedback

**Phase 2 - Career Profile Setup (3 minutes, optional)**:
- Optional fields: name, career field, job title, years experience
- Optional resume upload (PDF/DOCX) or paste
- Explain value: "AI can reference your experience in answers"
- Can be completed later or skipped entirely

**Phase 3 - Session Context (30 seconds, per-interview)**:
- Optional fields: company name, position, job posting URL
- Auto-populate from clipboard if possible
- Can be skipped for generic session

**Acceptance Criteria**:
- Every onboarding step has prominent "Skip" button
- System works perfectly if all onboarding is skipped
- Onboarding shown only once per installation
- User can revisit onboarding via settings menu
- No blocking modals or forced data entry

**NEW REQUIREMENT: REQ-ONBOARD-002 - API Key Management**
The system SHALL implement three-tier LLM access:

**Tier 1 (Default, Zero Config)**:
- Local Ollama on localhost:11434
- No API key required
- Works offline
- Performance: Good (~1-2s responses)

**Tier 2 (Recommended, Optional)**:
- Ollama Cloud API (cloud-routed models)
- Free tier available at ollama.com/api
- Requires free account and API key
- Performance: Excellent (~500ms responses)

**Tier 3 (Premium, Optional)**:
- OpenAI, Anthropic, etc.
- Paid API keys
- Best quality
- Performance: Excellent

**Acceptance Criteria**:
- System defaults to Tier 1 if no keys provided
- Graceful fallback chain: Tier 3 → Tier 2 → Tier 1
- API keys stored in OS keychain (never plaintext)
- User can switch tiers in settings without restart

---

## Section 3: User Profile & Context Architecture

### Changes to Requirements.md & Design.md

**NEW REQUIREMENT: REQ-PROFILE-001 - Local User Profile Storage**
The system SHALL implement a local SQLite database to store user profile data:

**User Profile Schema**:
```sql
CREATE TABLE user_profiles (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    full_name TEXT,
    email TEXT,
    career_field TEXT,
    job_title TEXT,
    years_experience INTEGER,
    resume_text TEXT,
    resume_file_path TEXT,
    parsed_skills JSON,
    preferences JSON
);
```

**Acceptance Criteria**:
- Profile data stored locally in ~/.interview_assistant/data.db
- Resume text and file path stored (encrypted at rest)
- Skills automatically parsed from resume (JSON array)
- Preferences include: verbose_responses, technical_depth, answer_style

**NEW REQUIREMENT: REQ-PROFILE-002 - Session Context Management**
The system SHALL track individual interview sessions with context:

**Session Schema**:
```sql
CREATE TABLE interview_sessions (
    id TEXT PRIMARY KEY,
    user_profile_id TEXT,
    created_at TIMESTAMP,
    company TEXT,
    position TEXT,
    job_posting_url TEXT,
    job_description TEXT,
    parsed_requirements JSON,
    key_topics JSON,
    duration_seconds INTEGER,
    outcome TEXT  -- offered, rejected, pending
);
```

**Acceptance Criteria**:
- Each interview is a separate session
- Job posting URL auto-fetched and parsed
- Requirements extracted from job description (AI-powered)
- Key topics identified for focus
- Session outcome tracked (for future analytics)

**NEW REQUIREMENT: REQ-PROFILE-003 - Profile-Aware LLM Context**
The system SHALL inject user profile and session context into LLM prompts:

**Context Injection Template**:
```
You are helping {user_name}, a {job_title} with {years_experience} years
of experience in {career_field}.

They are interviewing for: {position} at {company}

Job requirements: {parsed_requirements}
Candidate's skills: {parsed_skills}

Question: {detected_question}

Provide a concise, relevant answer that:
1. Draws on their actual experience
2. Addresses job requirements
3. Is appropriate for their seniority level
```

**Acceptance Criteria**:
- Profile data injected only if user provided it
- Session context injected if available
- Works fine with no profile (generic responses)
- Responses are measurably more personalized with profile

---

## Section 4: Intelligent Term/Acronym Explanation

### Changes to Requirements.md & Design.md

**NEW REQUIREMENT: REQ-TERM-001 - Automatic Acronym Detection**
The system SHALL automatically detect acronyms and industry-specific jargon in real-time transcription and questions.

**Detection Criteria**:
- All-caps words 2-6 characters (SRE, CI/CD, K8s)
- Known industry terms from configurable dictionary
- Context-aware (field-specific: DevOps, Sales, Medical, etc.)

**Acceptance Criteria**:
- Detection accuracy > 90% for common acronyms
- False positive rate < 10%
- Runs in < 50ms (non-blocking)

**NEW REQUIREMENT: REQ-TERM-002 - Toggleable Term Explanations**
The system SHALL provide user-controllable term explanation feature:

**User Controls**:
- Toggle: "Auto-explain acronyms/terms" (default: ON)
- Scope: Per-session or global setting
- UI: Checkbox in quick settings menu

**Acceptance Criteria**:
- When ON: Terms explained inline or tooltip on first mention
- When OFF: No explanations, no extra LLM calls
- Toggle takes effect immediately (no restart)
- Setting persisted between sessions

**NEW REQUIREMENT: REQ-TERM-003 - Latency-Aware Batching**
The system SHALL batch term explanations with existing LLM prompts to minimize latency:

**Batching Strategy**:
- If question prompt pending: Append "Also briefly define: {term}"
- If latency > 3000ms: Skip explanation to maintain performance
- If term already explained this session: Don't repeat

**Acceptance Criteria**:
- Term explanations add < 200ms latency (when batched)
- No separate LLM call per term
- Latency threshold configurable
- Session-scoped deduplication (term explained once only)

**NEW REQUIREMENT: REQ-TERM-004 - Term Explainer Card**
The system SHALL display term explanations in dedicated UI card:

**Card Behavior**:
- Shows recently explained terms (last 5)
- Auto-collapses after 10 seconds of no new terms
- Fades to 30% opacity when minimized
- Tooltip on hover for full definition
- "Clear All" button to reset session terms

**Acceptance Criteria**:
- Card only visible when terms detected
- Terms shown in chronological order
- Each term: acronym + brief definition (1 sentence)
- Color-coded (yellow/orange) for quick identification

---

## Section 5: Card-Based Modular UI

### Changes to Requirements.md & Design.md

**NEW REQUIREMENT: REQ-UI-001 - Grid-Based Card System**
The system SHALL implement a modular card-based UI where each element is independently resizable and repositionable:

**Core Cards**:
1. Live Transcript Card
2. Current Question Card
3. Answer Card
4. Context/Memory Card
5. Term Explainer Card
6. Status/Settings Card

**Grid System**:
- Grid units: 20rem columns x 1rem rows
- Minimum card size: 20rem width x 1rem height
- Snap-to-grid alignment (invisible grid)
- Collision detection (cards push others aside)

**Acceptance Criteria**:
- All cards draggable via header bar
- All cards resizable via edge handles
- Cards snap to grid for clean alignment
- Layout state persisted between sessions
- No cards overlap unless user forces it

**NEW REQUIREMENT: REQ-UI-002 - Layout Presets**
The system SHALL provide pre-configured layout presets for common use cases:

**Required Presets**:

1. **Interview Stealth** (400x150px):
   - Minimal, semi-transparent
   - Only Question + Answer cards visible
   - Auto-collapse after 10s idle
   - Designed for video interviews with camera on

2. **Phone Call Expansive** (800x600px):
   - Full-featured, 100% opacity
   - All cards visible
   - Full transcript scrollable
   - Designed for audio-only calls

3. **Business Meeting Capture** (1200x800px):
   - All cards + meeting notes
   - Transcript recording enabled
   - Action items tracking
   - Designed for internal team meetings

4. **Customer Success Call** (1000x700px):
   - CRM integration active
   - Customer profile + history cards
   - Upsell opportunities + churn risk
   - Designed for sales/support calls

**Acceptance Criteria**:
- User can switch presets via dropdown menu
- Hotkeys assigned: Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4
- User can create custom presets
- Presets include: window size, visible cards, opacity, card positions
- Emergency hide-all hotkey: Ctrl+H

**NEW REQUIREMENT: REQ-UI-003 - Glanceable Information Display**
The system SHALL use visual hierarchy and progressive disclosure to present information with zero required user interaction:

**Visual Hierarchy** (size, weight, color):
- Questions: 24px bold blue (highest priority)
- Answers: 20px bold green (second priority)
- Terms: 16px italic orange (third priority)
- Transcript: 14px gray 70% opacity (lowest priority)

**Progressive Disclosure**:
- Information appears automatically when relevant
- Less important content fades or collapses
- No scrolling required for critical info
- Hover/click to reveal more detail

**Acceptance Criteria**:
- User can glance at screen and immediately identify current question/answer
- Key phrases automatically highlighted in answers (yellow background)
- First sentence of answer bolded for quick scanning
- Transcript auto-scrolls but doesn't distract

**NEW REQUIREMENT: REQ-UI-004 - Adaptive Density Modes**
The system SHALL automatically detect context and adjust UI density:

**Detection Logic**:
- If camera detected AND screen share active → Stealth mode
- If audio-only call detected → Expansive mode
- If CRM integration active → Business mode
- Default → Normal mode

**Density Modes**:
- **Stealth**: Minimal cards, auto-hide after 10s, 80% opacity, <400x150px
- **Normal**: Standard density, all cards available
- **Expansive**: Full detail, all cards visible, scrollable transcript
- **Business**: CRM data + meeting tools + recording

**Acceptance Criteria**:
- Mode switches automatically based on context
- User can override auto-detection
- Manual override persists until changed
- Smooth transitions between modes (300ms fade)

**NEW REQUIREMENT: REQ-UI-005 - Layout Persistence & Management**
The system SHALL support saving, loading, and managing custom layouts:

**Features**:
- Save current layout with custom name
- Restore saved layouts from dropdown
- Export layouts to JSON file
- Import layouts from JSON file
- Restore factory defaults
- Assign hotkeys to saved layouts

**Acceptance Criteria**:
- Layouts stored in ~/.interview_assistant/layouts/
- Each layout: JSON file with card positions, sizes, visibility
- Quick settings menu shows layout dropdown
- "Save as..." button creates new layout
- "Restore original" button resets to factory

---

## Section 6: CRM Integration for Business Users

### Changes to Requirements.md & Design.md

**NEW REQUIREMENT: REQ-CRM-001 - Salesforce Integration**
The system SHALL integrate with Salesforce API to enrich customer calls with context:

**Data Fetched**:
- Contact/Lead profile (name, title, company)
- Account information (annual revenue, industry, size)
- Last interaction date and topic
- Open cases/tickets
- Purchase history and active contracts
- Notes and relationship milestones

**Integration Flow**:
1. Call starts → System detects phone number or email
2. Async query to Salesforce API
3. Fetch customer context (non-blocking)
4. Display in Customer Context Card
5. Inject context into LLM prompts

**Acceptance Criteria**:
- Salesforce plugin implements ICRMConnector interface
- API key stored in OS keychain
- Data fetched asynchronously (< 2s)
- Call can proceed if CRM fetch fails (graceful degradation)
- Context updates live during call if new data arrives

**NEW REQUIREMENT: REQ-CRM-002 - AI-Enhanced CRM Insights**
The system SHALL use AI to analyze CRM data and provide actionable insights:

**AI-Generated Insights**:
1. **Upsell Opportunities**: Detect when customer mentions needs matching higher tier products
2. **Churn Risk Assessment**: Analyze interaction frequency, sentiment, open issues
3. **Suggested Talking Points**: Generate personalized conversation starters based on history
4. **Relationship Milestones**: Surface important dates (renewals, anniversaries, past successes)

**Acceptance Criteria**:
- Insights displayed in dedicated card
- Confidence scores shown for predictions (Low/Medium/High)
- User can dismiss or act on insights
- Insights logged for accuracy tracking (future analytics)

**NEW REQUIREMENT: REQ-CRM-003 - Microsoft Dynamics 365 Support**
The system SHALL support Microsoft Dynamics 365 CRM with equivalent functionality:

**Implementation**:
- Dynamics plugin implements ICRMConnector interface
- Same data fetch pattern as Salesforce
- Uses Dynamics Web API
- Authentication via OAuth2

**Acceptance Criteria**:
- User can select CRM provider in settings (Salesforce | Dynamics | None)
- Only one CRM plugin active at a time
- Switching CRM providers doesn't require restart

**NEW REQUIREMENT: REQ-CRM-004 - Context-Aware LLM Prompts**
The system SHALL automatically inject CRM context into LLM prompts for personalized suggestions:

**Context Injection**:
```
You are assisting in a call with {customer_name} from {company}.

Account: ${account_value}/year, {industry}, {company_size} employees
Last interaction: {date} - discussed {topic}
Open issues: {open_cases_summary}
Recent purchases: {products}

Opportunities:
- Upsell: {upsell_suggestion} (confidence: {confidence})
- Renewal: {renewal_date} (in {days_until} days)

Churn risk: {risk_level}
Indicators: {risk_indicators}

Provide responses that:
1. Reference their specific context naturally
2. Address any pain points from open cases
3. Suggest relevant upsells if appropriate
4. Be warm and personalized
```

**Acceptance Criteria**:
- CRM context injected only when available
- Works fine without CRM (generic responses)
- Context includes relevant data only (not entire CRM record)
- Respects data privacy (no PII in logs)

---

## Priority Summary for Kiro

### Implement in This Order:

**Phase 1 - Foundation (Current)**:
1. ✅ Bundled Ollama installation
2. ✅ Zero-config defaults
3. ✅ Three-tier LLM access (local/cloud/premium)
4. ✅ Structured logging infrastructure
5. ✅ Plugin architecture foundation
6. ✅ Database schema (all tables including future hooks)

**Phase 2 - Smart Features**:
1. Optional onboarding flow (3 phases)
2. User profile & context management
3. Profile-aware LLM prompts
4. Term detection & explanation
5. Session-scoped deduplication

**Phase 3 - Advanced UI**:
1. Card-based layout system
2. Layout presets (4 required)
3. Glanceable information display
4. Adaptive density modes
5. Layout persistence & management

**Phase 4 - Business Features**:
1. CRM integration interface
2. Salesforce plugin
3. Dynamics 365 plugin
4. AI-enhanced insights
5. Context-aware prompts

**Phase 5 - Polish**:
1. Performance monitoring
2. Latency budget enforcement
3. Verbose logging mode
4. Clear error messages
5. Feature flags configuration
