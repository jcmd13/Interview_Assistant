#!/usr/bin/env python3
"""
Interview Assistant Server - Modern Entry Point

This is the new modular entry point for the Interview Assistant server.
It uses the refactored src/ package structure with proper separation of concerns.

Usage:
    python server.py

Architecture:
- Phase 1: Delegates to optimized_stt_server_v3.py (current)
- Phase 2: Will import and orchestrate src/ modules directly
- Phase 3+: Full plugin-based architecture

Legacy entry point (still works):
    python optimized_stt_server_v3.py

Both entry points now use the same modular src/ infrastructure:
- src.core.logger: Structured JSON logging
- src.core.config: Type-safe configuration
- src.core.timing: Latency tracking
"""

import sys
import asyncio
from pathlib import Path

# Ensure src/ is in the Python path
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    """
    Main entry point for the Interview Assistant server.

    Currently delegates to the legacy implementation in optimized_stt_server_v3.py
    while we gradually refactor components into src/ modules.
    """
    # Import server implementation
    from optimized_stt_server_v3 import (
        main as server_main,
        reset_state,
        server_shutdown,
        log,
    )

    try:
        # Run the async server
        asyncio.run(server_main())
    except KeyboardInterrupt:
        server_shutdown.set()
        log("startup", "info", "server_stopped", reason="keyboard_interrupt")
    except Exception as e:
        log("error", "error", "fatal_error", error=str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
