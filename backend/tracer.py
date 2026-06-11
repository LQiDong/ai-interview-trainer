"""
Tracing / logging utility.

Every agent call writes a trace entry to data/traces/{session_id}.json.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ── Paths ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent  # project root
TRACES_DIR = BASE_DIR / "data" / "traces"


def _ensure_dir() -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)


# ── Trace entry ──────────────────────────────────────────────────────

class TraceEntry:
    def __init__(
        self,
        session_id: str,
        agent_type: str,
        phase: str,
        llm_mode: str,
        input_data: dict,
        output_data: Any,
        duration_ms: float,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "agent_type": agent_type,
            "phase": phase,
            "llm_mode": llm_mode,
            "input_summary": _summarize(input_data),
            "output_summary": _summarize(output_data),
            "duration_ms": round(duration_ms, 2),
            "error": error,
            "metadata": metadata or {},
        }

    def to_dict(self) -> dict:
        return self.entry


def _summarize(data: Any, max_len: int = 500) -> Any:
    """Truncate long strings for readability in traces."""
    if isinstance(data, str) and len(data) > max_len:
        return data[:max_len] + f"...[truncated, total {len(data)} chars]"
    if isinstance(data, dict):
        return {k: _summarize(v, max_len) for k, v in data.items()}
    if isinstance(data, list):
        if len(data) > 10:
            return [_summarize(item, max_len) for item in data[:10]] + [
                f"...[{len(data) - 10} more items]"
            ]
        return [_summarize(item, max_len) for item in data]
    return data


# ── Trace writer ─────────────────────────────────────────────────────

async def write_trace(
    session_id: str,
    agent_type: str,
    phase: str,
    llm_mode: str,
    input_data: dict,
    output_data: Any,
    duration_ms: float,
    error: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Append a trace entry to the session's trace file.

    The trace file is a JSON array; each call appends one entry.
    """
    _ensure_dir()

    entry = TraceEntry(
        session_id=session_id,
        agent_type=agent_type,
        phase=phase,
        llm_mode=llm_mode,
        input_data=input_data,
        output_data=output_data,
        duration_ms=duration_ms,
        error=error,
        metadata=metadata,
    )

    trace_file = TRACES_DIR / f"{session_id}.json"

    # Read existing traces or create new list
    if trace_file.exists():
        try:
            existing = json.loads(trace_file.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, Exception):
            existing = []
    else:
        existing = []

    existing.append(entry.to_dict())

    trace_file.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_traces(session_id: str) -> list[dict]:
    """Read all traces for a session."""
    _ensure_dir()
    trace_file = TRACES_DIR / f"{session_id}.json"
    if not trace_file.exists():
        return []
    try:
        return json.loads(trace_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return []
