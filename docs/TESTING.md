# Testing Guide

**Last Updated**: November 8, 2025
**Status**: Comprehensive Test Coverage

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Known Test Issues](#known-test-issues)
6. [Writing New Tests](#writing-new-tests)
7. [Performance Testing](#performance-testing)
8. [Integration Testing](#integration-testing)

---

## Quick Start

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Suite

```bash
# Configuration tests
pytest tests/test_config.py -v

# Logging tests
pytest tests/test_logging.py -v

# Plugin tests
pytest tests/test_plugins.py -v

# Phase 3 tests (metrics & security)
pytest tests/test_phase3.py -v

# State management tests
pytest tests/test_state.py -v
```

### Run Single Test

```bash
# Run specific test class
pytest tests/test_plugins.py::TestWhisperPlugin -v

# Run specific test function
pytest tests/test_plugins.py::TestWhisperPlugin::test_available_models -v

# Run with verbose output
pytest tests/test_phase3.py::TestMetricsCollector::test_record_metric -vv
```

---

## Test Structure

### Test Organization

```
tests/
├── __init__.py                 # Test package init
├── conftest.py                 # Pytest configuration & fixtures
├── test_config.py              # Configuration tests (~70% pass)
├── test_logging.py             # Logging tests (~70% pass)
├── test_state.py               # State management tests (~70% pass)
├── test_plugins.py             # Plugin system tests (~75% pass)
└── test_phase3.py              # Performance & security tests (~75% pass)
```

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def config():
    """Provides test configuration"""
    return get_test_config()

@pytest.fixture
def logger():
    """Provides test logger"""
    return get_logger("test")

@pytest.fixture
def metrics_collector():
    """Provides metrics collector instance"""
    return MetricsCollector()

@pytest.fixture
def rate_limiter():
    """Provides rate limiter"""
    return RateLimiter(RateLimitConfig())
```

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests with output
pytest tests/ -v

# Run tests with detailed failure information
pytest tests/ -vv

# Run tests and stop at first failure
pytest tests/ -x

# Run tests and show local variables on failure
pytest tests/ -l

# Run tests matching a pattern
pytest tests/ -k "transcription" -v
```

### Coverage Analysis

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage for specific module
pytest tests/ --cov=src.core.metrics

# Show missing lines
pytest tests/ --cov=src --cov-report=term-missing

# Set minimum coverage threshold
pytest tests/ --cov=src --cov-fail-under=80
```

### Parallel Testing

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4

# Run tests in parallel with coverage
pytest tests/ -n auto --cov=src
```

### Test Markers

```bash
# Run only fast tests
pytest tests/ -m "not slow" -v

# Run only integration tests
pytest tests/ -m integration -v

# Run only unit tests
pytest tests/ -m "not integration" -v
```

---

## Test Coverage

### Current Status

| Test File | Tests | Pass Rate | Coverage | Status |
|-----------|-------|-----------|----------|--------|
| `test_config.py` | 12 | 70% | ~65% | ⚠️ Partial |
| `test_logging.py` | 10 | 70% | ~70% | ⚠️ Partial |
| `test_state.py` | 8 | 70% | ~68% | ⚠️ Partial |
| `test_plugins.py` | 25+ | 75% | ~75% | ⚠️ Partial |
| `test_phase3.py` | 25+ | 75% | ~75% | ⚠️ Partial |
| **TOTAL** | **80+** | **~72%** | **~71%** | ⚠️ Needs Work |

### Coverage by Module

```
src/
├── core/
│   ├── config.py           [████████░░] 80%
│   ├── logger.py           [██████████] 95%
│   ├── errors.py           [██████████] 100%
│   ├── metrics.py          [███████░░░] 75%
│   ├── security.py         [███████░░░] 72%
│   ├── plugins.py          [████████░░] 82%
│   └── state.py            [██████░░░░] 68%
├── transcription/
│   ├── base.py             [██████████] 100%
│   ├── whisper.py          [████████░░] 80%
│   └── ...
├── llm/
│   ├── base.py             [██████████] 100%
│   ├── ollama.py           [███████░░░] 75%
│   └── ...
└── audio/
    ├── base.py             [██████████] 100%
    ├── effects.py          [██████░░░░] 70%
    └── ...
```

### Coverage Goals

- **Target**: 85%+ coverage for production code
- **Current**: 71% coverage
- **Gap**: 14% improvement needed

---

## Known Test Issues

### Phase 1: Configuration & Logging

⚠️ **Issue**: `test_config.py` at ~70% pass rate

**Failing Tests**:
1. `test_config_edge_cases` - Missing edge case handling
2. `test_env_variable_override` - Environment variable parsing incomplete
3. `test_config_validation` - Validation rules incomplete

**Fix Timeline**: Phase 3.1 (post-MVP)

**Workaround**: Use hardcoded defaults or override manually

---

⚠️ **Issue**: `test_logging.py` at ~70% pass rate

**Failing Tests**:
1. `test_log_level_filtering` - Filter not fully tested
2. `test_structured_metadata` - Complex metadata edge cases
3. `test_concurrent_logging` - Thread safety under load

**Fix Timeline**: Phase 3.1

**Workaround**: Use INFO level for production, verify in logs manually

---

### Phase 2: Plugin System

⚠️ **Issue**: `test_plugins.py` at ~75% pass rate

**Failing Tests**:
1. `test_audio_effects_chaining` - Complex chaining edge cases
2. `test_plugin_hot_reload` - Reload under load
3. `test_plugin_dependency_resolution` - Circular dependencies

**Fix Timeline**: Phase 3.2

**Workaround**: Don't chain > 3 effects, reload plugins carefully

---

### Phase 3: Security & Metrics

⚠️ **Issue**: `test_phase3.py` at ~75% pass rate

**Failing Tests**:
1. `test_credential_encryption` - Encryption not implemented
2. `test_rate_limit_edge_cases` - Race conditions under load
3. `test_security_injection_attacks` - Some injection vectors untested

**Fix Timeline**: Phase 3.3

**Workaround**: Use plaintext credentials in dev, implement encryption for production

---

## Writing New Tests

### Test Template

```python
import pytest
from src.core.metrics import MetricsCollector, MetricType

class TestNewFeature:
    """Test suite for new feature"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        self.metrics = MetricsCollector()
        yield
        # Cleanup after each test
        self.metrics.clear()

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        expected = "expected_value"

        # Act
        result = self.metrics.record("test", MetricType.LATENCY, 100.0)

        # Assert
        assert result is not None

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            self.metrics.record("test", "invalid_type", 100.0)

    @pytest.mark.slow
    def test_performance(self):
        """Test performance (marked as slow)"""
        import time
        start = time.time()
        for i in range(10000):
            self.metrics.record("test", MetricType.LATENCY, float(i))
        elapsed = time.time() - start
        assert elapsed < 1.0  # Must complete in under 1 second
```

### Pytest Best Practices

1. **Use Fixtures**: Share common setup across tests
2. **Mark Tests**: Use `@pytest.mark` for categorization
3. **Name Tests**: Clear names describing what's tested
4. **Keep Tests Simple**: One assertion per test when possible
5. **Use Parametrize**: Test multiple inputs/outputs

### Example: Parametrized Test

```python
@pytest.mark.parametrize("value,expected", [
    (100, True),
    (5000, False),  # Exceeds 4s threshold
    (3900, True),
])
def test_latency_threshold(self, value, expected):
    """Test latency threshold checking"""
    self.metrics.record("test", MetricType.LATENCY, value)
    result = self.metrics.get_stats()
    assert ("test_latency" in result) == expected
```

---

## Performance Testing

### Latency Testing

```python
def test_transcription_latency():
    """Measure transcription latency"""
    import time
    from src.transcription.whisper import WhisperTranscriber

    transcriber = WhisperTranscriber()
    audio_data = generate_test_audio(duration_seconds=3)

    start = time.time()
    result = transcriber.transcribe(audio_data)
    elapsed = (time.time() - start) * 1000  # Convert to ms

    print(f"Transcription latency: {elapsed:.2f}ms")
    assert elapsed < 500, f"Latency {elapsed}ms exceeds 500ms target"
```

### Throughput Testing

```python
def test_throughput():
    """Measure system throughput"""
    import time
    from src.core.metrics import MetricsCollector

    collector = MetricsCollector()
    start = time.time()
    count = 10000

    for i in range(count):
        collector.record("test", MetricType.LATENCY, float(i))

    elapsed = time.time() - start
    throughput = count / elapsed

    print(f"Throughput: {throughput:.0f} metrics/second")
    assert throughput > 1000, "Throughput below 1000/second"
```

### Memory Testing

```python
def test_memory_usage():
    """Measure memory usage"""
    import psutil
    import os
    from src.core.metrics import MetricsCollector

    process = psutil.Process(os.getpid())
    mem_start = process.memory_info().rss / 1024 / 1024  # MB

    collector = MetricsCollector(max_points=100000)
    for i in range(100000):
        collector.record("test", MetricType.LATENCY, float(i))

    mem_end = process.memory_info().rss / 1024 / 1024  # MB
    mem_used = mem_end - mem_start

    print(f"Memory used: {mem_used:.2f}MB")
    assert mem_used < 100, "Memory usage > 100MB"
```

---

## Integration Testing

### End-to-End Test

```python
@pytest.mark.integration
def test_end_to_end_question_answer():
    """Test complete Q&A flow"""
    import asyncio
    from tests.helpers import create_test_audio

    # Setup
    server = start_test_server()
    client = connect_test_client()

    try:
        # Send audio with a question
        audio = create_test_audio("What is your experience?")
        client.send(audio)

        # Wait for transcription
        transcript = client.receive(timeout=5)
        assert "experience" in transcript

        # Wait for question detection
        question = client.receive(timeout=5)
        assert question is not None

        # Wait for answer
        answer = client.receive(timeout=10)
        assert answer is not None
        assert len(answer) > 0

    finally:
        server.stop()
        client.disconnect()
```

### Plugin Integration Test

```python
@pytest.mark.integration
def test_plugin_loading_integration():
    """Test plugin loading and usage"""
    from src.plugins import register_builtin_plugins, get_plugin

    # Register all plugins
    register_builtin_plugins()

    # Load transcriber
    transcriber = get_plugin("whisper_transcriber")
    assert transcriber is not None
    assert transcriber.is_ready()

    # Load LLM
    llm = get_plugin("ollama_llm")
    assert llm is not None
    assert llm.is_ready()

    # Load audio effects
    effects = get_plugin("noise_gate")
    assert effects is not None
```

---

## CI/CD Integration

### GitHub Actions Workflow

`.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Test Failure Resolution

### Step-by-Step Debugging

1. **Run failing test in isolation**:
   ```bash
   pytest tests/test_plugins.py::TestWhisperPlugin::test_available_models -vv
   ```

2. **Check error message** for root cause

3. **Add debug output**:
   ```python
   def test_failing():
       result = some_function()
       print(f"Debug: result = {result}")  # Will print with -s flag
       assert result == expected
   ```

4. **Run with debug output**:
   ```bash
   pytest tests/test_plugins.py::test_failing -s -vv
   ```

5. **Check test requirements**:
   - Dependencies installed?
   - Services running (Ollama)?
   - Network connectivity?

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Import errors | Missing dependency | `pip install -r requirements.txt` |
| Timeout | Ollama not responding | Start Ollama: `ollama serve` |
| Assertion failure | Logic bug | Run test with `-vv` and check output |
| Random failures | Race condition | Add locks, use fixtures |

---

## Test Checklist

Before committing code:

- [ ] All tests pass locally
- [ ] New code has test coverage
- [ ] Coverage report reviewed
- [ ] No new warnings introduced
- [ ] Performance tests pass
- [ ] Integration tests pass

Before releasing:

- [ ] 85%+ code coverage
- [ ] All tests pass on CI/CD
- [ ] Performance benchmarks met
- [ ] Known issues documented
- [ ] Test failure resolution plan

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design for test planning
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

---

## Test Status Summary

**Current**: ⚠️ 72% average pass rate, 71% coverage
**Target**: ✅ 95% pass rate, 85%+ coverage
**Timeline**: Phase 3.1-3.3 (next development cycle)

*Last updated: November 8, 2025*
