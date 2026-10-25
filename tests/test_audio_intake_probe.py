"""Probe 1: syntax, sound bytes and MCP-native AudioContent round-trip.

This verifies a correctly shaped MCP result *at the server/tool layer only*.
Whether ChatGPT forwards the block into a model's native audio perception is
a separate client-level experiment, not covered by these unit tests.
"""
from __future__ import annotations
import base64
import io
import unittest
import wave
from probes.audio_intake.fixture import make_wav, mcp_audio_block, audit

class TestAudioBytes(unittest.TestCase):
    def test_variants_are_valid_stereo_wav(self):
        for choice in ("A", "B"):
            data = make_wav(choice)
            self.assertTrue(data.startswith(b"RIFF"))
            with wave.open(io.BytesIO(data), "rb") as wav:
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getframerate(), 24000)
                self.assertAlmostEqual(wav.getnframes() / wav.getframerate(), 1.68, places=2)
    def test_same_length_different_music(self):
        self.assertEqual(len(make_wav("A")), len(make_wav("B")))
        self.assertNotEqual(make_wav("A"), make_wav("B"))
    def test_wire_content_is_real_sound(self):
        block = mcp_audio_block("B")
        self.assertEqual(block["type"], "audio")
        self.assertEqual(block["mimeType"], "audio/wav")
        self.assertEqual(base64.b64decode(block["data"]), make_wav("B"))
        self.assertEqual(audit("B")["source_scope"], "synthetic_original")
    def test_file_access_cannot_be_injected(self):
        with self.assertRaises(ValueError):
            make_wav("../secrets")

try:
    from mcp import Client
    from mcp.types import AudioContent
    from probes.audio_intake.server import mcp as server
except ImportError:
    Client = None

@unittest.skipIf(Client is None, "MCP SDK v2 is not installed (byte-level tests still run)")
class TestMcpRoundTrip(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_client_receives_audio_content_not_json(self):
        async with Client(server) as client:
            first = await client.call_tool("audition_clip", {"clip": "A"})
            second = await client.call_tool("audition_clip", {"clip": "B"})
        for obj in (first, second):
            self.assertEqual(len(obj.content), 1)
            block = obj.content[0]
            self.assertIsInstance(block, AudioContent)
            self.assertEqual(block.type, "audio")
            self.assertEqual(block.mime_type, "audio/wav")
        self.assertEqual(base64.b64decode(first.content[0].data), make_wav("A"))
        self.assertEqual(base64.b64decode(second.content[0].data), make_wav("B"))
        self.assertNotEqual(first.content[0].data, second.content[0].data)

if __name__ == "__main__":
    unittest.main()
