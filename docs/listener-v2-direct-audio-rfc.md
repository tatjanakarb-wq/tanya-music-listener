# Listener v2: direct-audio bridge for the existing ChatGPT conversation

Status: **design RFC; not implemented or validated**  
Date: 2026-10-25  
Repository: `tatjanakarb-wq/tanya-music-listener`

## Why v1 is not enough

Current `listener.py` selects a permitted source (usually ~30 s Apple/iTunes preview), decodes a temporary mono WAV at 22,050 Hz, analyzes it with `librosa`, returns numeric features, and deletes audio. Its output is useful for rhythm/dynamics/energy checks, but does not deliver actual sound to the ChatGPT model. The existing `climax.time_sec` is relative to the examined excerpt, not necessarily to the complete song. Metadata and `archived_full_recording_features` also are not a listening experience.

The desired system is **not a second LLM or a separate persona running on an API key**. The music-listening judgment should be made by the assistant already conversing with the user, using native audio input *if the client actually makes the audio stream available to that model*. GitHub remains a trusted preparation and measurement helper.

## Architecture

```
known artist + track or authorized audio file
  -> recording identity & rights gate
  -> original audio / available preview
  -> v1 DSP measurements (keep; label the actual scope)
  -> v2 stereo audio payload (ephemeral, not committed)
  -> transport capability probe
  -> assistant receives actual audio in the same conversation
  -> blind qualitative listening notes
  -> compare with DSP + prior calibrated user responses
  -> subjective candidate judgment, then user listening and feedback
```

### Raw-audio handoff: hypothesis to test first

ChatGPT's conversation audio-file uploads support WAV/MP3 and other formats; the MCP 2026-07-28 specification defines a tool result content block `{ "type": "audio", "data": "<base64>", "mimeType": "audio/wav" }`. **Neither fact establishes that the ChatGPT plugin client will route audio returned by an MCP tool into the same model's native audio perception.** This is an explicit client-compatibility hypothesis, not an existing capability.

Prototype a narrow read-only MCP tool `get_audition_clip(request_id, index)` that returns:

- An actual audio content block, obtained from an approved source, with no transcript or audio descriptions.
- A separate text metadata block: recording ID, original track length, clip offset/duration, `source_scope`, recording/asset hash, and rights/availability.
- No spectral narrative or genre adjectives on the first (blind) pass.

If the model receives only textual labels, file URLs, base64 strings, waveform numbers, or spectrogram images, the direct-sound test has **failed**. Do not report `heard_by_model=true` in that case. Only after this works do we invest in a permanent MCP server or a secure local Mac bridge.

Fallback without substituting a different model: prepare MP3/WAV clips or full files as private conversation attachments, so the user can submit them to the same ChatGPT chat. This pathway is documented for supported ChatGPT sessions, but an automatic tool-to-composer attachment is **not** yet demonstrated. Record manual steps as a limitation, not as a successful integration.

### Capability proof: distinguish real sound from spectral inference

Make two short **synthetic** music clips generated locally with the same length, loudness envelope and approximate BPM, but different melodic direction or instrumentation, withholding track names and signal analyses.

1. Request the sound through `get_audition_clip`; ask the assistant to describe the actual melody/timbre and the time of change. Capture the answer.
2. Run a text-only control with *the same* numeric feature report but **no audio content block**. Capture the answer.
3. Swap the two audio files while leaving the textual metadata as similar as possible. A truly delivered acoustic modality should influence the answer in a way the unchanged text cannot.
4. Compare with a direct ChatGPT audio attachment of the same files. Store the exact surface, model/session and client implementation; note any unsupported modality or drop during tool execution.

Never infer native listening merely because the final answer is musically plausible.

## Perceptual pass (if the transport is proven)

The model's **first pass should be blind**: no artist, prior verdict, genre label or DSP numbers. Ask for observable, temporal features rather than the user's supposed emotional response:

- What sounds (voice/piano/drums/electronics etc.) enter, recur, dominate, or drop away?
- Is the melody a genuine line, a looping ornament, a harmonic tension, or absent?
- What is the relation between bass, percussion and other layers? Where does it reorganize?
- How are tension, release and momentum arranged over *the portion actually available*?
- Does the latter part change the meaning of the former, or is there only a stationary plateau?
- What is surprising, alive, abrasive or merely decorative, and which judgments remain uncertain?

On the **second pass** give the numeric acoustic report. It can confirm a claimed dynamic change or challenge a questionable impression. Never let the spectrum overwrite what the model detected in sound.

Only in the **third pass** retrieve user-specific calibrated feedback: strong examples such as complex, living rhythm/harmony and embodied changes; known negative examples of flat electronic loops, soft wallpaper and stalled finales. The model must explicitly distinguish "my own musical fascination" from "hypothesis about what will move this listener". Only the listener's report can certify their experience of 10/10.

## Audio capture and temporal fidelity

- Do not attempt to download or decrypt Spotify streams or bypass DRM. Spotify catalogue and playlist APIs are for identity and assembly, not a license to obtain raw sound.
- Full-track study needs a recording the user can lawfully provide or a service-authorized audio source. GitHub's Apple/iTunes preview yields only a local preview-level verdict.
- Preserve **stereo** and ordinary music-quality sampling for the model-input copy. Do not reuse v1's mono 22,050-Hz analytical downmix as the only audible representation.
- Prefer the **whole song** when legal, accessible and within client upload limits. Otherwise choose timestamped, overlapping excerpts from beginning, musical turning points and ending. A track with a late climax cannot be judged from its initial 30 seconds.
- Never normalize or independently boost each excerpt in a way that destroys its meaningful dynamic contrasts. Preserve original absolute offsets.
- Do not publish audio payloads or personal music files to this public GitHub repository. Keep audio transient or in user-authorized protected storage. Public GitHub may store source hashes and feature JSON only.

## Proposed state contract

```json
{
  "request_id": "listener-v2-probe-001",
  "recording_identity": {"artist": "...", "title": "...", "version": "..."},
  "audio_source": {
    "scope": "full_track | preview | user_supplied_excerpt | none",
    "rights": "authorized_source",
    "duration_sec": 0,
    "excerpt_start_sec": 0,
    "excerpt_end_sec": 0,
    "sha256": "..."
  },
  "dsp": {"scope": "preview", "features_uri": "..."},
  "transport": {
    "mcp_audio_block_emitted": false,
    "client_audio_consumption_verified": false
  },
  "model_audition": {
    "direct_audio_received": false,
    "reported_scope": "none",
    "listening_notes": null,
    "proposed_turning_points": []
  },
  "user_calibration": {
    "historical_matches_checked": false,
    "listener_verdict_pending": true
  }
}
```

Two important language rules: (a) `heard_official_short_preview` in v1 means the **runner** processed an audio signal, not the ChatGPT model; (b) `model_audition.direct_audio_received` may become true only after a real audio handoff, never because JSON metrics are present.

## Low-risk implementation order

**Gate A — transport probe**: 2–3 short synthetic clips, no third-party rights and no external LLM. Verify actual model audio input via the ordinary ChatGPT conversation.

**Gate B — v1 honesty/precision fix**: rename clip-relative peak / time references to `preview_peak_*` or `clip_peak_*`, separate preview and full-track provenance, reject incorrect remixes and live versions.

**Gate C — `audio_packet` preparation**: small sidecar to prepare stereo audition excerpts from authorized input. It may return a private resource link and audio bytes through MCP if Gate A works; otherwise generate private files for native in-chat attachment.

**Gate D — listening cards**: store the model's first-pass qualitative analysis separately from spectra, and only later attach its listener-specific hypothesis and the user's actual feedback.

**Gate E — playlist tests**: start with several old strong hits, several known misses and at least three novel, blind tracks. Use exact recording/version comparisons. Do not call a candidate "10/10" before the user has heard it.

## Non-goals

- New LLM API agent replacing the original conversational assistant.
- Claiming Spotify's playlist connector exposes a playable raw PCM stream.
- Publishing copyrighted full-length audio to GitHub.
- Treating a 30-second Apple preview as a full song.
- Conflating similarity, numerical feature scores, embeddings, cover art or genre metadata with direct acoustic perception.

## Sources

- OpenAI Help Center: https://help.openai.com/en/articles/8555545-uploading-files-and-audio-to-chatgpt
- MCP 2026-07-28 tool result audio content: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx
- Current code and previous evidence: `listener.py`, `requests/`, `results/`, `summaries/` in this repository.
