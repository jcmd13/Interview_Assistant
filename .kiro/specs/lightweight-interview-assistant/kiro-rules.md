# Kiro Agent Behavior Rules - Interview Assistant Project

## Project Context

**System**: Real-time AI interview assistant with modular, plugin-based architecture
**Target Platform**: macOS (primary), cross-platform compatible
**Core Philosophy**: Privacy-first, accessibility-focused, zero-distraction UX
**User**: John - DevOps/IT Security professional, Mac user, values local processing

## Critical Agent Behaviors

### 1. Specification Adherence
- **ALWAYS** reference requirements.md for acceptance criteria validation
- **ALWAYS** reference design.md for architectural decisions
- **ALWAYS** reference tasks.md for implementation dependencies
- When requirements conflict, prioritize: Security > Performance > Features > Privacy

### 2. Performance-First Decision Making
- **DEFAULT** to local processing solutions (Ollama, faster-whisper, native macOS APIs)
- **REQUIRE** explicit user consent before suggesting cloud services
- **AVOID** persistent data storage unless explicitly specified
- When suggesting external services, always provide local alternative

### 3. Accessibility as Core Feature
- Accessibility features are **optional and user-controllable** (Requirement 7.2)
- **NEVER** force accessibility features on all users
- Design for "invisible assistance" - zero interaction required during use
- Prioritize cognitive load reduction over feature richness

### 4. Interface Modularity
- **ALL** components must implement defined interfaces (design.md sections 2-7)
- Services communicate through interfaces, **NEVER** direct dependencies
- Support runtime service switching without restart (Requirement 8.2, 8.3)
- Configuration-driven component selection (Requirement 8.4)

### 5. Error Recovery Philosophy
- **GRACEFUL DEGRADATION** always (design.md Error Handling section)
- System continues with reduced functionality rather than failing completely
- No technical error messages to users (Requirement 2.5)
- Automatic fallback to alternative services when primary fails

### 6. macOS Native Optimization
- **PREFER** native macOS APIs when available (AVFoundation, Speech Framework)
- Toolbar must be invisible to screen sharing/recording (Requirement 6.1)
- Follow Apple HIG for native app design patterns (Requirement 6.5)
- Optimize for M-series chip architecture

### 7. Testing Discipline
- **EVERY** service interface requires unit tests (marked with * in tasks.md)
- Integration tests for service switching and configuration changes
- Performance benchmarks: transcription < 500ms, memory stable, CPU optimized
- Accessibility testing mandatory when accessibility features added

### 8. Plugin Architecture Awareness
- Design for extensibility via Industry Packs and Function Modules (design.md sections 6-7)
- Plugin discovery and loading must be safe and sandboxed
- All plugins use common interfaces from design.md
- Support future extensions without modifying core architecture

## Decision-Making Framework

### When Choosing Between Options

**Question 1**: Does this require external/cloud services?
- **YES**: Provide local alternative first, require explicit consent
- **NO**: Proceed

**Question 2**: Does this add user interaction during meetings?
- **YES**: Reconsider - violates Requirement 1.3 (zero clicks/input during use)
- **NO**: Proceed

**Question 3**: Does this compromise service modularity?
- **YES**: Refactor to use proper interfaces from design.md
- **NO**: Proceed

**Question 4**: Does this create direct service dependencies?
- **YES**: Inject via ServiceRegistry, use interfaces only
- **NO**: Proceed

**Question 5**: Is this privacy-preserving by default?
- **NO**: Make it local-first or add explicit consent
- **YES**: Proceed

### When Implementing Services

1. **Identify** the interface from design.md (AudioProcessorInterface, TranscriptionEngineInterface, etc.)
2. **Implement** all methods defined in the interface specification
3. **Register** with ServiceRegistry/PluginRegistry for hot-swapping
4. **Configure** via ConfigurationService, never hardcode
5. **Test** with mocks, validate interface compliance
6. **Document** in error recovery strategy (design.md Error Handling)

### When User Requirements Are Ambiguous

1. **Prioritize** according to: Privacy > Accessibility > Performance > Features
2. **Reference** the user story in requirements.md for intent
3. **Check** design.md for architectural guidance
4. **Prefer** simpler solution that maintains modularity
5. **Suggest** options with trade-offs rather than deciding alone

## Anti-Patterns to Avoid

### ❌ DON'T:
1. **Couple services directly** - always use interfaces
2. **Hardcode configuration** - use ConfigurationService
3. **Add visible notifications** - violates zero-distraction UX (Req 2.4)
4. **Force cloud services** - local-first is core principle (Req 5.1)
5. **Create global singletons** - use dependency injection
6. **Skip error handling** - graceful degradation is mandatory
7. **Add mandatory accessibility features** - they must be optional (Req 7.2)
8. **Assume internet connectivity** - support offline mode (Req 5.3)
9. **Break screen-sharing invisibility** - critical for professional use (Req 6.1)
10. **Require restarts for config changes** - hot-reload is required (Req 8.2, 8.3)

## Quality Gates

### Before Marking Task Complete

✓ Implementation matches interface specification in design.md
✓ Unit tests written (for tasks marked with * in tasks.md)
✓ Configuration externalized (no hardcoded values)
✓ Error handling with graceful degradation implemented
✓ Acceptance criteria from requirements.md validated
✓ Privacy/security considerations addressed
✓ macOS-specific optimizations considered (if applicable)
✓ Service can be hot-swapped without restart

### Before Phase Completion

✓ All phase tasks marked complete in tasks.md
✓ Integration tests passing
✓ Performance benchmarks met
✓ Documentation updated
✓ No cross-service direct dependencies
✓ Plugin/service registry updated

## Context Awareness

### User Background (John)
- Strong DevOps/IT security experience
- Familiar with Python, PowerShell, Home Assistant
- Building for accessibility (neurodivergent, anxious professionals)
- Job hunting, building portfolio project
- Values privacy, local-first, open source
- Running on Mac (likely M-series)

### Project Goals
1. **Primary**: Lightweight, unobtrusive meeting assistant
2. **Secondary**: Accessibility tool for professionals with anxiety/neurodivergence
3. **Tertiary**: Portfolio project demonstrating modular architecture
4. **Long-term**: Extensible platform for AI-assisted professional development

### Success Metrics
- Toolbar < 400x150px, semi-transparent, always-on-top working correctly
- Transcription latency < 500ms
- Zero interaction required during meetings
- Invisible to screen sharing/recording
- Services hot-swappable at runtime
- Fully functional offline (local-only mode)
- Memory stable, CPU < 10% average

## Agent Self-Correction Triggers

### When to Pause and Reconsider

**Trigger 1**: Implementation requires user interaction during active meeting
→ **Response**: Review Requirement 1.3, redesign for zero-interaction

**Trigger 2**: Service creates direct dependency on another service
→ **Response**: Review design.md interfaces, inject via registry

**Trigger 3**: Feature requires cloud/external service without local alternative
→ **Response**: Review Requirement 5.1, add local implementation first

**Trigger 4**: Configuration is hardcoded in service
→ **Response**: Extract to ConfigurationService per design.md

**Trigger 5**: Error causes system failure instead of degradation
→ **Response**: Review design.md Error Handling, implement fallback

**Trigger 6**: Accessibility feature is mandatory rather than optional
→ **Response**: Review Requirement 7.2, make it user-controllable

**Trigger 7**: macOS-specific optimization ignored when available
→ **Response**: Review design.md platform optimizations, prefer native APIs

## Communication Guidelines

### When Reporting Progress
- State which requirement/task is being addressed
- Reference specific sections in requirements.md, design.md, or tasks.md
- Highlight any deviations from spec with reasoning
- Note dependencies on other tasks (tasks.md shows with _Requirements: X.Y_)

### When Asking for Clarification
- Quote specific requirement or acceptance criteria
- Present options with trade-offs
- Reference relevant design.md sections
- Default to privacy-first, accessibility-aware choice if no response

### When Proposing Changes
- Explain why current spec is insufficient
- Show how change maintains architectural integrity
- Demonstrate continued adherence to core principles
- Get explicit approval before deviating from requirements.md

## Phase-Specific Focus

### Phase 1 (Current): Core Architecture Refactoring
**Priority**: Service interfaces, modularity, plugin system foundation
**Key Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5
**Critical Success Factor**: All services implement interfaces, hot-swapping works

### Phase 2: Native Toolbar UI
**Priority**: macOS native design, zero-interaction UX, screen-sharing invisibility
**Key Requirements**: 1.1, 1.2, 1.4, 6.1, 6.5
**Critical Success Factor**: Toolbar is truly invisible during video calls

### Phase 3: Native Audio
**Priority**: Low-latency, native macOS APIs, device switching
**Key Requirements**: 3.1, 3.4, 6.2
**Critical Success Factor**: Lower latency than FFmpeg, seamless switching

### Phase 4: AI Enhancements
**Priority**: Context management, pluggable LLM providers, privacy controls
**Key Requirements**: 4.1, 4.2, 4.3, 5.2, 5.4
**Critical Success Factor**: Ollama, OpenAI, Anthropic all work via same interface

### Phase 5: Industry Packs
**Priority**: Custom vocabulary, domain-specific AI context, pack management
**Key Requirements**: 4.4, 4.5, 3.2
**Critical Success Factor**: Packs improve transcription accuracy and AI relevance

### Phase 6: Function Modules (Future)
**Priority**: Visual analysis, document processing, extensibility framework
**Key Requirements**: Design foundations for future expansion
**Critical Success Factor**: Third-party plugins can be created and loaded safely

## Final Directive

When in doubt:
1. **Check requirements.md** for "THE system SHALL..." statements
2. **Check design.md** for interface specifications and architecture
3. **Check tasks.md** for implementation order and dependencies
4. **Ask** rather than assume when specifications are unclear
5. **Default** to: Privacy-first, Accessibility-aware, Interface-driven, Error-tolerant

This project is building a tool to help professionals present their best selves during high-stakes conversations. Every decision should support that mission while maintaining architectural integrity for future extensibility.
