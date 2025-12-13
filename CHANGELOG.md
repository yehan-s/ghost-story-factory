# Changelog

All notable changes to Ghost Story Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] - 2025-10-25

### Added

**Core Game Engine (Phase 1-2)**
- Interactive game engine with real-time LLM generation
  - `GameEngine`: Main game loop with state management
  - `GameState`: Core game variables (PR/GR/WF/timestamp/inventory)
  - `ChoicePointsGenerator`: Dynamic choice generation (LLMClient mode)
  - `RuntimeResponseGenerator`: Narrative response generation
  - `IntentMappingEngine`: Choice validation and intent extraction
  - `EndingSystem`: Multi-ending system (补完/旁观/迷失)
- CLI UI with rich formatting
  - Interactive menus with `rich` library
  - Real-time progress indicators
  - Game state visualization
  - Save/load functionality

**Architecture Improvements**
- **ADR-004**: LLMClient architecture refactoring
  - Replaced CrewAI with direct HTTP calls for structured generation
  - Full request/response logging for debugging
  - Complete error diagnostics (captures original LLM output)
- **ADR-005**: LangGraph orchestration layer ✅
  - Node-level telemetry collection
  - JSON stability metrics tracking (100% success rate)
  - Guided mode structure validation
  - Environment variable: `USE_LANGGRAPH_PIPELINE=1` (experimental)
- **ADR-006**: Response generation LLMClient migration
  - Fixed guided mode structure collapse (depth/beat scoping)
  - Timeout optimization (`RESPONSE_MAX_TOKENS=800-1200`)
  - Environment variable: `USE_LLMCLIENT_RESPONSE=1` (default enabled)

**Content Generation System**
- Dynamic branch story generation (character analysis whitelist-based)
  - Auto-extracts supporting characters from `protagonist.md`
  - Supports variable number of branches (e.g., 7 branches for Hangzhou)
  - File naming includes character names: `{city}_branch_{idx}_{character}_story.md`
  - `--no-branches` flag to skip branch generation

**Engineering Optimizations**
- Parallel generation capability (smart dynamic queue)
  - `generate_smart_parallel.py`: Intelligent parallel generator
  - Automatic retry mechanism
  - Real-time progress display
- Centralized logging system
  - Timestamped log files in `logs/` directory
  - Full stack trace capture
  - Console prints log file paths

### Changed

- Migrated from CrewAI to LLMClient for all structured JSON generation
  - Skeleton generation: `SkeletonGenerator` → LLMClient
  - Choice generation: `ChoicePointsGenerator` → LLMClient
  - Response generation: `RuntimeResponseGenerator` → LLMClient
- Unified LLM timeout configuration
  - Progressive timeout schedule: `LLM_TIMEOUTS=60,120,180` (default)
  - Exponential backoff retry: `LLM_RETRY_DELAY=2.0`, `LLM_RETRY_MAX_DELAY=60.0`

### Fixed

- JSON stability improved to 100% success rate (10/10 LLM calls successful)
  - 9 first-time successes, 1 salvage success, 0 failures
- Guided mode structure collapse in response generation
  - Introduced depth/beat bucketing for approximate merging
- F-string format specifier bugs in JSON templates
  - Fixed invalid format specifier errors in choice generation prompts

### Testing

- Unit test coverage >80%
- End-to-end testing passed (complete Hangzhou story playthrough)
- Node-level telemetry validation passed

### Documentation

- Added 6 ADRs (Architecture Decision Records)
  - ADR-001: Plot Skeleton Pipeline
  - ADR-002: v4 Default Pipeline
  - ADR-003: v4 Workflow Staging and Agents
  - ADR-004: Core LLM Refactor
  - ADR-005: LangGraph Agent Orchestration ✅
  - ADR-006: Response LLMClient and Guided Approx Merge Scope
- Complete architecture documentation in `docs/architecture/`
- Updated `CLAUDE.md` with ADR-005 completion status

---

## [Unreleased]

### Planned for v0.2.0 (Target: 2025-03-15)

**Static Dialogue Pregeneration System (P2)**
- Dialogue tree BFS traversal generator
- Checkpoint/resume mechanism
- Game engine support for pregenerated mode (zero-latency gameplay)
- Response time optimization (<0.1s vs 15-25s in dynamic mode)
- Cost optimization ($10-20 per story)

**Documentation Enhancements**
- Complete user manual
- API documentation generation
- Developer guide for contributors

---

[v0.1.0]: https://github.com/yehan-s/ghost-story-factory/releases/tag/v0.1.0
