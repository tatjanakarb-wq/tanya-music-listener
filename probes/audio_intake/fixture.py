"""Deterministic, copyright-free stereo WAV fixture for testing tool-to-model audio delivery.

Two variants share notes, length, level contour and instrumentation; only the
temporal ordering of pitches differs. Only inspect this module after blind tests.
"""
from __future__ import annotations

import base64
import hashlib
import io
import math
import struct
import wave
from typing import Literal

SAMPLE_RATE = 24000
CHANNELS = 2
SAMPLE_WIDTH = 2
SECONDS_PER_NOTE = 0.42
PITCHES = (220.00, 293.66, 349.23, 440.00)

def make_wav(clip: Literal["A", "B"]) -> bytes:
    """Return a short valid WAV. Invalid IDs never trigger arbitrary file access."""
    if clip not in ("A", "B"):
        raise ValueError("clip must be A or B")
    notes = PITCHES if clip == "A" else tuple(reversed(PITCHES))
    note_frames = int(SECONDS_PER_NOTE * SAMPLE_RATE)
    frames = bytearray()
    for pitch in notes:
        for i in range(note_frames):
            t = i / SAMPLE_RATE
            # Identical amplitude envelope for both clips, phase reset per note.
            edge = min(1.0, i / (SAMPLE_RATE * 0.018), (note_frames - 1 - i) / (SAMPLE_RATE * 0.018))
            edge = max(0.0, edge)
            tone = (0.60 * math.sin(2 * math.pi * pitch * t)
                    + 0.20 * math.sin(4 * math.pi * pitch * t)
                    + 0.06 * math.sin(6 * math.pi * pitch * t))
            value = int(max(-32000, min(32000, 20000 * edge * tone)))
            frames.extend(struct.pack("<hh", value, int(value * 0.92)))
    with io.BytesIO() as out:
        with wave.open(out, "wb") as w:
            w.setnchannels(CHANNELS)
            w.setsampwidth(SAMPLE_WIDTH)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(frames)
        return out.getvalue()

def mcp_audio_block(clip: Literal["A", "B"]) -> dict[str, str]:
    """Wire-level AudioContent; local test independent of the MCP SDK."""
    data = make_wav(clip)
    return {"type": "audio", "mimeType": "audio/wav",
            "data": base64.b64encode(data).decode("ascii")}

def audit(clip: Literal["A", "B"]) -> dict[str, object]:
    """Keep this separate from the blind audio tool; no pitch labels included."""
    data = make_wav(clip)
    return {
        "clip": clip, "mime_type": "audio/wav",
        "source_scope": "synthetic_original",
        "duration_s": round(4 * SECONDS_PER_NOTE, 2),
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
    }
