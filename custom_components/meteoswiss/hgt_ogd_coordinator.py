"""Compatibility import for the canonical measured-HGT coordinator.

The coordinator definition lives in ``coordinator.py``. Keep this existing
import path as a single alias for consumers of the earlier b7 module layout.
"""

from .coordinator import MeteoSwissHgtCoordinator

__all__ = ["MeteoSwissHgtCoordinator"]
