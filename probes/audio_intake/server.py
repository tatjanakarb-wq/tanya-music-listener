"""Local-only MCP audio source experiment, *not* yet connected to ChatGPT.

Python MCP SDK v2, see https://py.sdk.modelcontextprotocol.io/servers/media/
Runs Streamable HTTP on localhost ONLY for an MCP inspector or local test client.
Do NOT expose this unauthenticated demo to the Internet.
"""
from __future__ import annotations

from typing import Literal
from mcp.server import MCPServer
from mcp.server.mcpserver import Audio

from probes.audio_intake.fixture import make_wav

mcp = MCPServer("Eon Native Audio Handoff Probe")

@mcp.tool()
def audition_clip(clip: Literal["A", "B"]) -> Audio:
    """Return actual blind WAV audio in an MCP AudioContent block, not DSP data.

    The assistant must describe the melodic contour from the sound itself.
    Do not call fixture.audit or inspect the audio generator in the blind test.
    """
    return Audio(data=make_wav(clip), format="wav")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
