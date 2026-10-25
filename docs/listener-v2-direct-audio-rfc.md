# Listener v2: direct-audio bridge for the existing ChatGPT conversation

Status: **isolated MCP AudioContent prototype implemented and tested; ChatGPT tool-to-model transport untested**  
Date: 2026-10-25  
Repository: `tatjanakarb-wq/tanya-music-listener`

## Correction, 25 October: existing hearing works; autonomous intake is missing

This is an important correction to the original framing. In a real 7 October session the conversational assistant could directly interpret music when the user attached an MP3 (Rival Consoles — Recovery) to the chat. An MP3 selected from ChatGPT Library did **not** enter the same audio modality. Do **not** spend development effort proving the ability to interpret a user-uploaded track again. The unsolved problem is the **transport from assistant-selected source to the current chat's native audio input before a Spotify playlist exists**.

The minimum successful user story: Eon selects a previously unheard candidate from a catalogue, invokes a read-only audio tool **without asking Tanya to upload or drag a file**, hears the musical signal in the **same continuing ChatGPT conversation**, gives its own temporal description, then only later decides whether to add it to a Spotify playlist. An acoustic JSON response, a link, a transient download in a runner, or audio that only plays on Tanya's device does **not** satisfy this story.

### Simplest viable source-to-model route (to implement/probe)

1. **Discovery:** Spotify catalog / MusicBrainz provides exact artist-title and release/version metadata. This is not audio delivery. Cross-check existing playlists and the candidate stop-list before audition.
2. **Cloud previews, no Mac required:** reuse `listener.py`'s Apple/iTunes permitted-preview resolver. A **long-lived authenticated audio-gateway MCP service** (not a short-lived GitHub Actions job) fetches the authorized short audio into volatile memory when asked. It should not commit MP3s to the public repository.
3. **Private full recordings, optional Mac:** for files Tanya already has the right to use, extend the gateway with an authenticated Mac/Eon Hands local relay when the Mac is reachable. Only expose explicit allowlisted local music directories/file handles. Never scrape or decrypt Spotify playback.
4. **Tool response:** return the *audio bytes themselves* as MCP `{ "type": "audio", "mimeType": "audio/wav"|"audio/mpeg", "data": "<base64>" }` plus a small, untrusted metadata block (identity, scope, recording hash, start/end seconds). This MIME structure is supported by the MCP specification, **but ChatGPT's connector may or may not inject tool-result audio into the model's native perception**. Test that one client hop before writing full pipelines.
5. **Same assistant does the judgment:** after it actually receives raw acoustic input, first record a blind temporal account with NO metadata, genre or DSP hints. Only then retrieve DSP metrics and Tanya's history. No second LLM, API substitute or independent listener persona.
6. **Playlist comes last:** audition a sufficiently broad new batch, compare candidates to known hits and dislikes, revise selection, then create and verify the Spotify playlist through its already-connected write plugin.

What the test proves is **automatic intake**, not that Eon is capable of hearing. If the ChatGPT MCP layer silently strips audio from tool results, mark the route `UNSUPPORTED_CLIENT_TRANSPORT`. Next test should be whether ChatGPT Work's cloud computer can natively attach the downloaded audio to the *same task/conversation*; do not assume this from its ability to download files. If that also fails, an external music-analysis model would solve a different problem and is **not** an acceptable substitute. Manual upload is the proven temporary fallback, not the goal.

Acceptance test: select **one** artist/title unseen in chat, obtain a legal preview in the gateway, call the tool in the same normal ChatGPT conversation, compare the model's content-dependent description against the deliberately blind numerical-only control. If content-dependent acoustic details arrived, proceed with 10–20 tracks before creating any playlist. If no sound arrived, stop and repair delivery rather than upgrading spectrum models.

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

### Transport proof: does tool-result sound reach the already capable listener?

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

**Gate A — autonomous intake probe**: the model's native musical perception from a user-attached MP3 was already shown on 7 October. Verify instead that a *tool-sourced audio block* reaches that same modality in the ordinary conversation without Tanya attaching it. Use a short synthetic clip to isolate routing, then one legal real preview. Do not claim autonomous listening if only metadata/JSON arrives.

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


## Execution receipt — 25 October 2026

A self-contained read-only **synthetic-audio server** and MCP-client integration tests were added to this repository, without touching `listener.py`, Spotify, or Eon Hands production:

- `probes/audio_intake/fixture.py`: two distinct short stereo PCM WAV clips, identical notes/timing/timbre but different melodic ordering; WAV, 24 kHz, 16-bit, ~1.68 seconds, generated in memory with the standard library.
- `probes/audio_intake/server.py`: SDK v2 `MCPServer` tool `audition_clip(A|B)` returns actual `Audio(data=wav_bytes, format="wav")`. Development transport binds to **127.0.0.1 only**, no public listener or authentication bypass.
- `tests/test_audio_intake_probe.py`: protocol and byte-identity checks, plus native `Client(mcp)` round-trip asserting `AudioContent(type="audio", mime_type="audio/wav")`.
- `.github/workflows/audio-intake-probe.yml`: official MCP SDK v2 runtime in GitHub Actions. Run https://github.com/tatjanakarb-wq/tanya-music-listener/actions/runs/40167305644, job 121090880018, result **SUCCESS: 5 tests passed** at 2026-10-25T05:56:16Z. Check the Actions log rather than relying on an assistant assertion.

**What is proven:** the server produces real, valid WAV data, and a native MCP test client receives and decodes the two distinct audio payloads as *audio blocks*, not spectral reports.

**What is NOT proven:** the currently connected ChatGPT client delivers `AudioContent` returned by a tool to the GPT-6 native audio perception path. The prototype is not deployed as an authenticated remote plugin, nor discovered as a tool in this ChatGPT conversation. Do **not** infer that the assistant heard the two samples. App UI extensions `ui/update-model-context` and `ui/message` explicitly mark audio as unsupported; this does not necessarily settle the separate question of direct MCP tool-result handling (see https://github.com/openai/mcp-extensions/blob/main/docs/spec.md).

A bounded research handoff to Mira has been queued, `mirareq_610c45cbd3634aaa89501216`: examine safe audio-tool integration via existing Eon Hands or Secure MCP Tunnel without modifying production or exposing public unauthenticated audio. Initial receipt status `queued`, **not** a technical confirmation. The next required stage is tool registration and one audio-block call in an ordinary ChatGPT chat. A truly *blind* musical-perception test needs an opaque randomized variant selection not visible in the current model context (the initial A/B fixture source has already been seen by its author).

Do not expand to real music, run a second LLM, or claim autonomous intake success before the client-modality hop is observed.


## Google Drive audio handoff test — 2026-10-25

Tanya suggested using private Google Drive as an automatic staging area before the assistant selects songs for a playlist. We tested the file transport in the existing connected Drive account, using existing **user-provided audio** in the private project folder [01_аудио](https://drive.google.com/drive/folders/1wn0ub5C28IgkKShJLhEshSe21LwYZJtn).

1. Found full `Aufgang - Kyrie.mp3` (4,667,024 bytes; 297.72 sec; stereo MP3 44.1 kHz) among seven existing recordings. Read via the Google Drive connector with `download_raw_file=true, include_base64=false`. The tool returned a genuine authenticated `file_uri`, not a spectral JSON report; it mounted the 4.5 MB file in the current working environment.
2. Prepared an **18.05-second, 44.1-kHz stereo MP3** excerpt locally, `eon-listener-v2-drive-test-kyrie-18s.mp3`, 361,614 bytes, SHA-256 `c5344b8a19d19074972d3330cb428714a54e7f3727a2ad494486edcec8f71d36`.
3. Uploaded the excerpt via connected Files Library (Google Drive mount) to the original private project's `01_аудио` folder. Drive ID `1AVpnmpcRiRZEuT7hYJfJOxf0HtjiViiV`, [file link](https://drive.google.com/file/d/1AVpnmpcRiRZEuT7hYJfJOxf0HtjiViiV/view?usp=drivesdk). Metadata confirms `audio/mpeg`, 361,614 bytes, user-only/non-shared.
4. Fetched the new Drive file back using the Google Drive connector, received the raw `file_uri` and container copy. The SHA-256 remained **exactly the same** and `ffprobe` decoded the intended duration. **Storage + upload + full audio-byte fetch passed.** No private audio was committed to this GitHub repository.
5. Tried the Files read route for the returned audio attachment. The returned message was `No readable content was found in this file for the requested mode.` The Google Drive tool returns a file reference and empty text, **not an MCP AudioContent block passed to the model's native audio perception.** Therefore ChatGPT's ability to analyze the sound directly from a Drive-fetched tool result **remains unverified**; the assistant must not pretend to have listened to Kyrie by ear in this test.

Conclusion: Drive is a viable **persistent buffer of full recordings and clips**, potentially allowing GitHub to stage candidates and Eon to download them without Tanya carrying files. The remaining obstacle is converting the tool-fetched file reference into a **native audio attachment or content block for the same conversational assistant**. A user-driven composer attachment from Drive might use the known native-audio path, but it does not satisfy autonomous intake. Need test client-level auto-attachment or MCP audio delivery; do not confuse the working Drive byte transport with the unproven perception handoff.
