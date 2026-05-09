"""Bridge strategy: Extends the existing SaveModelStrategy for use with the platform.

This file provides a reference for the InstrumentedSaveModelStrategy pattern.
In practice, the LogParser approach (log_parser.py) is used because:
- Flower strategies run synchronously in the subprocess
- Log parsing avoids dual DB connections and Redis dependency
- The existing server.py already has structured log output

If direct DB writes from within Flower are needed in the future,
extend SaveModelStrategy as shown below and wire it in flower_server/server.py.
"""

# This module is a placeholder for future direct strategy instrumentation.
# Current implementation uses FlowerLogParser (log_parser.py) for all event bridging.
