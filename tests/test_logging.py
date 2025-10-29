"""
Tests for Structured Logging System

This test module verifies that the structured logging system works correctly
and outputs valid JSON with the expected fields.
"""

import json
import sys
from io import StringIO
import pytest

from src.core.logger import (
    configure_logging,
    get_logger,
    get_logger_with_request_id,
    set_log_level,
)


class TestLoggingConfiguration:
    """Test logging configuration and setup"""

    def test_configure_logging_json_output(self):
        """Test that configure_logging sets up JSON output"""
        configure_logging(log_level="INFO", json_output=True)
        logger = get_logger("test.component")

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        logger.info("test_event", test_key="test_value", count=42)

        # Restore stdout
        sys.stdout = sys.__stdout__

        # Parse JSON output
        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        # Verify required fields
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert log_entry["level"] == "info"
        assert "event" in log_entry
        assert log_entry["event"] == "test_event"
        assert "component" in log_entry
        assert log_entry["component"] == "test.component"
        assert "test_key" in log_entry
        assert log_entry["test_key"] == "test_value"
        assert "count" in log_entry
        assert log_entry["count"] == 42

    def test_logger_factory(self):
        """Test that get_logger creates component-specific loggers"""
        logger1 = get_logger("component.a")
        logger2 = get_logger("component.b", extra_data="value")

        # Capture output for logger1
        captured_output = StringIO()
        sys.stdout = captured_output
        logger1.info("event_a")
        sys.stdout = sys.__stdout__

        output1 = captured_output.getvalue().strip()
        log_entry1 = json.loads(output1)

        assert log_entry1["component"] == "component.a"
        assert log_entry1["event"] == "event_a"

        # Capture output for logger2
        captured_output = StringIO()
        sys.stdout = captured_output
        logger2.info("event_b")
        sys.stdout = sys.__stdout__

        output2 = captured_output.getvalue().strip()
        log_entry2 = json.loads(output2)

        assert log_entry2["component"] == "component.b"
        assert log_entry2["event"] == "event_b"
        assert log_entry2["extra_data"] == "value"

    def test_logger_with_request_id(self):
        """Test that request_id is properly bound to logger"""
        logger = get_logger_with_request_id("test.request", request_id="req_123")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.info("request_processed")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["request_id"] == "req_123"
        assert log_entry["event"] == "request_processed"

    def test_logger_with_auto_generated_request_id(self):
        """Test that request_id is auto-generated if not provided"""
        logger = get_logger_with_request_id("test.auto")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.info("auto_request")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        # Should have a request_id (auto-generated)
        assert "request_id" in log_entry
        assert log_entry["request_id"] is not None
        assert len(log_entry["request_id"]) > 0


class TestLogLevels:
    """Test different log levels"""

    def test_debug_level_logging(self):
        """Test DEBUG level logging"""
        configure_logging(log_level="DEBUG", json_output=True)
        logger = get_logger("test.debug")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.debug("debug_message", detail="debug_data")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["level"] == "debug"
        assert log_entry["event"] == "debug_message"
        assert log_entry["detail"] == "debug_data"

    def test_info_level_logging(self):
        """Test INFO level logging"""
        configure_logging(log_level="INFO", json_output=True)
        logger = get_logger("test.info")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.info("info_message", status="success")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["level"] == "info"
        assert log_entry["event"] == "info_message"
        assert log_entry["status"] == "success"

    def test_warning_level_logging(self):
        """Test WARNING level logging"""
        configure_logging(log_level="WARNING", json_output=True)
        logger = get_logger("test.warning")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.warning("warning_message", reason="threshold_exceeded")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["level"] == "warning"
        assert log_entry["event"] == "warning_message"
        assert log_entry["reason"] == "threshold_exceeded"

    def test_error_level_logging(self):
        """Test ERROR level logging"""
        configure_logging(log_level="ERROR", json_output=True)
        logger = get_logger("test.error")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.error("error_message", error="connection_failed")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["level"] == "error"
        assert log_entry["event"] == "error_message"
        assert log_entry["error"] == "connection_failed"


class TestStructuredData:
    """Test structured data in logs"""

    def test_multiple_key_value_pairs(self):
        """Test logging with multiple structured fields"""
        configure_logging(log_level="INFO", json_output=True)
        logger = get_logger("test.structured")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.info(
            "complex_event",
            user_id=12345,
            action="login",
            ip_address="192.168.1.1",
            duration_ms=150,
            success=True
        )
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["event"] == "complex_event"
        assert log_entry["user_id"] == 12345
        assert log_entry["action"] == "login"
        assert log_entry["ip_address"] == "192.168.1.1"
        assert log_entry["duration_ms"] == 150
        assert log_entry["success"] is True

    def test_nested_data_structures(self):
        """Test logging with nested data (lists, dicts)"""
        configure_logging(log_level="INFO", json_output=True)
        logger = get_logger("test.nested")

        captured_output = StringIO()
        sys.stdout = captured_output
        logger.info(
            "nested_event",
            metadata={"version": "1.0", "env": "test"},
            tags=["audio", "transcription"],
            counts=[1, 2, 3]
        )
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["event"] == "nested_event"
        assert log_entry["metadata"]["version"] == "1.0"
        assert log_entry["metadata"]["env"] == "test"
        assert log_entry["tags"] == ["audio", "transcription"]
        assert log_entry["counts"] == [1, 2, 3]


class TestLogLevelControl:
    """Test runtime log level changes"""

    def test_set_log_level_runtime(self):
        """Test changing log level at runtime"""
        # Start with INFO
        configure_logging(log_level="INFO", json_output=True)

        # Change to DEBUG
        set_log_level("DEBUG")
        logger = get_logger("test.runtime")

        # DEBUG messages should now appear
        captured_output = StringIO()
        sys.stdout = captured_output
        logger.debug("debug_after_change")
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        log_entry = json.loads(output)

        assert log_entry["level"] == "debug"
        assert log_entry["event"] == "debug_after_change"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
