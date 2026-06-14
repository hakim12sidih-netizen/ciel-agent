"""
CIEL — Performance profiling.

Modules :
  - Timer / @timed decorator
  - Profiler (benchmark N itérations)
  - CLI : ciel perf profile, doctor, timings
"""
from __future__ import annotations

from .timing import Timer, timed, get_timings, reset_timings, Profiler

__all__ = ["Timer", "timed", "get_timings", "reset_timings", "Profiler"]
