from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import librosa
import numpy as np
import requests


USER_AGENT = os.getenv(
    "MUSIC_LISTENER_USER_AGENT",
    "TanyaMusicListener/0.2 (personal noncommercial music research)"
)
TIMEOUT = (15, 90)
MAX_BYTES = 80 * 1024 * 1024
MAX_SECONDS = 900


def finite(value: Any, digits: int = 5) -> Any:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return [finite(item, digits) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        value = float(value)
        if not math.isfinite(value):
            return None
        return round(value, digits)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"\b(feat|featuring|ft)\.?\b.*$", "", text)
    text = re.sub(r"[^a-z0-9а-яё]+", " ", text)
    return " ".join(text.split())


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def slugify(text: str) -> str:
    value = normalize(text).replace(" ", "-")
    value = re.sub(r"[^a-z0-9а-яё-]+", "", value)
    return value[:100] or "result"


def get_json(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def musicbrainz_candidates(artist: str, track: str) -> list[dict[str, Any]]:
    payload = get_json(
        "https://musicbrainz.org/ws/2/recording/",
        params={
            "query": f'recording:"{track}" AND artist:"{artist}"',
            "fmt": "json",
            "limit": 8,
        },
    )
    output: list[dict[str, Any]] = []
    for rec in payload.get("recordings", []):
        credits = " ".join(
            credit.get("name") or credit.get("artist", {}).get("name", "")
            for credit in rec.get("artist-credit", [])
        ).strip()
        score = (
            0.58 * similarity(track, rec.get("title", ""))
            + 0.42 * similarity(artist, credits)
        )
        output.append(
            {
                "mbid": rec.get("id"),
                "title": rec.get("title"),
                "artist": credits,
                "duration_ms": rec.get("length"),
                "first_release_date": rec.get("first-release-date"),
                "disambiguation": rec.get("disambiguation", ""),
                "musicbrainz_score": rec.get("score"),
                "local_match_score": round(score, 4),
            }
        )
    return sorted(output, key=lambda item: item["local_match_score"], reverse=True)


def acousticbrainz_summary(mbid: str) -> dict[str, Any] | None:
    urls = [
        f"https://acousticbrainz.org/{mbid}/low-level",
        f"https://acousticbrainz.org/api/v1/{mbid}/low-level",
    ]
    payload = None
    for url in urls:
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=TIMEOUT,
            )
            if response.status_code == 200:
                payload = response.json()
                break
        except (requests.RequestException, ValueError):
            continue

    if not payload:
        return None

    low = payload.get("lowlevel", {})
    rhythm = payload.get("rhythm", {})
    tonal = payload.get("tonal", {})
    metadata = payload.get("metadata", {})
    audio_props = metadata.get("audio_properties", {})

    def mean_of(name: str) -> Any:
        value = low.get(name)
        if isinstance(value, dict):
            return value.get("mean")
        return value

    return {
        "analysis_kind": "archived_full_recording_features",
        "source": "AcousticBrainz",
        "mbid": mbid,
        "duration_sec": audio_props.get("length"),
        "sample_rate": audio_props.get("sample_rate"),
        "tempo_bpm": rhythm.get("bpm"),
        "danceability": rhythm.get("danceability"),
        "onset_rate": rhythm.get("onset_rate"),
        "beats_count": rhythm.get("beats_count"),
        "key": tonal.get("key_key"),
        "scale": tonal.get("key_scale"),
        "chords_changes_rate": tonal.get("chords_changes_rate"),
        "dynamic_complexity": low.get("dynamic_complexity"),
        "average_loudness": low.get("average_loudness"),
        "spectral_centroid_mean": mean_of("spectral_centroid"),
        "spectral_flux_mean": mean_of("spectral_flux"),
        "spectral_rolloff_mean": mean_of("spectral_rolloff"),
        "dissonance_mean": mean_of("dissonance"),
        "warning": (
            "This is an archived third-party feature profile. "
            "Recording/version identity must be checked against duration and release."
        ),
    }


def itunes_candidates(artist: str, track: str) -> list[dict[str, Any]]:
    payload = get_json(
        "https://itunes.apple.com/search",
        params={
            "term": f"{artist} {track}",
            "media": "music",
            "entity": "song",
            "limit": 25,
            "country": "US",
        },
    )
    candidates: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        title_score = similarity(track, item.get("trackName", ""))
        artist_score = similarity(artist, item.get("artistName", ""))
        combined = 0.62 * title_score + 0.38 * artist_score
        candidates.append(
            {
                "artist": item.get("artistName"),
                "track": item.get("trackName"),
                "album": item.get("collectionName"),
                "duration_ms": item.get("trackTimeMillis"),
                "release_date": item.get("releaseDate"),
                "preview_url": item.get("previewUrl"),
                "store_url": item.get("trackViewUrl"),
                "match_score": round(combined, 4),
                "title_score": round(title_score, 4),
                "artist_score": round(artist_score, 4),
            }
        )
    return sorted(candidates, key=lambda item: item["match_score"], reverse=True)


def download_audio(url: str, target: Path) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError("Only HTTPS audio URLs are accepted")

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        stream=True,
        allow_redirects=True,
    )
    response.raise_for_status()

    total = 0
    with target.open("wb") as handle:
        for chunk in response.iter_content(256 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_BYTES:
                raise RuntimeError("Audio payload exceeded the configured size limit")
            handle.write(chunk)

    if total < 1024:
        raise RuntimeError("Downloaded payload is too small to be audio")

    return {
        "resolved_url": response.url,
        "bytes": total,
        "content_type": response.headers.get("Content-Type", ""),
    }


def decode_audio(source: Path, wav: Path) -> None:
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-t",
        str(MAX_SECONDS),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "22050",
        "-c:a",
        "pcm_s16le",
        str(wav),
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if process.returncode != 0:
        raise RuntimeError((process.stderr or "ffmpeg failed")[-1200:])


def segment_means(feature: np.ndarray, segments: int = 12) -> list[float]:
    flat = np.asarray(feature).reshape(-1)
    if flat.size == 0:
        return [0.0] * segments
    bounds = np.linspace(0, flat.size, segments + 1, dtype=int)
    result: list[float] = []
    for start, end in zip(bounds[:-1], bounds[1:]):
        end = max(end, start + 1)
        result.append(float(np.mean(flat[start:end])))
    return result


def zscore(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    std = float(np.std(values))
    if std < 1e-12:
        return np.zeros_like(values)
    return (values - float(np.mean(values))) / std


def analyze_wav(wav_path: Path) -> dict[str, Any]:
    y, sr = librosa.load(wav_path, sr=22050, mono=True)
    if y.size < sr:
        raise RuntimeError("Decoded audio is shorter than one second")

    duration = float(librosa.get_duration(y=y, sr=sr))
    hop = 512
    stft = librosa.stft(y, n_fft=2048, hop_length=hop)
    magnitude = np.abs(stft)
    power = magnitude ** 2
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=2048)

    rms = librosa.feature.rms(S=magnitude, frame_length=2048, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(S=magnitude, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(S=magnitude, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(
        S=magnitude, sr=sr, roll_percent=0.85
    )[0]
    flatness = librosa.feature.spectral_flatness(S=magnitude)[0]
    contrast = librosa.feature.spectral_contrast(S=magnitude, sr=sr)
    onset_strength = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)

    tempo_value, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_strength, sr=sr, hop_length=hop
    )
    tempo = float(np.asarray(tempo_value).reshape(-1)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    beat_intervals = np.diff(beat_times)
    beat_interval_cv = None
    if beat_intervals.size >= 2 and np.mean(beat_intervals) > 0:
        beat_interval_cv = float(np.std(beat_intervals) / np.mean(beat_intervals))

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_strength, sr=sr, hop_length=hop
    )
    onset_rate = float(len(onset_frames) / duration)

    harmonic, percussive = librosa.effects.hpss(y)
    harmonic_rms = float(np.sqrt(np.mean(harmonic ** 2)))
    percussive_rms = float(np.sqrt(np.mean(percussive ** 2)))
    percussive_share = percussive_rms / (
        harmonic_rms + percussive_rms + 1e-12
    )

    total_energy = float(np.sum(power) + 1e-12)
    low = float(np.sum(power[frequencies < 150]) / total_energy)
    mid = float(
        np.sum(power[(frequencies >= 150) & (frequencies < 2000)])
        / total_energy
    )
    high = float(np.sum(power[frequencies >= 2000]) / total_energy)

    rms_db = librosa.amplitude_to_db(np.maximum(rms, 1e-12), ref=1.0)
    dynamic_range = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 10))
    crest_factor = float(
        20
        * np.log10(
            (np.max(np.abs(y)) + 1e-12)
            / (np.sqrt(np.mean(y ** 2)) + 1e-12)
        )
    )

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    chroma_mean = np.mean(chroma, axis=1)
    chroma_probability = chroma_mean / (np.sum(chroma_mean) + 1e-12)
    tonal_entropy = float(
        -np.sum(chroma_probability * np.log2(chroma_probability + 1e-12))
    )

    rms_segments = np.asarray(segment_means(rms))
    centroid_segments = np.asarray(segment_means(centroid))
    onset_segments = np.asarray(segment_means(onset_strength))
    flatness_segments = np.asarray(segment_means(flatness))

    climax_score = (
        0.55 * zscore(rms_segments)
        + 0.25 * zscore(onset_segments)
        + 0.20 * zscore(centroid_segments)
    )
    climax_index = int(np.argmax(climax_score))
    segment_seconds = duration / len(rms_segments)

    timeline = []
    for index in range(len(rms_segments)):
        timeline.append(
            {
                "time_sec": finite((index + 0.5) * segment_seconds, 2),
                "rms": finite(rms_segments[index]),
                "spectral_centroid_hz": finite(centroid_segments[index], 2),
                "onset_strength": finite(onset_segments[index]),
                "spectral_flatness": finite(flatness_segments[index]),
            }
        )

    return {
        "analysis_kind": "direct_audio_signal",
        "heard_seconds": finite(duration, 3),
        "sample_rate": sr,
        "tempo_bpm": finite(tempo, 3),
        "beat_interval_cv": finite(beat_interval_cv),
        "onset_rate_per_sec": finite(onset_rate),
        "dynamic_range_db_p95_p10": finite(dynamic_range, 3),
        "crest_factor_db": finite(crest_factor, 3),
        "rms_mean": finite(float(np.mean(rms))),
        "rms_std": finite(float(np.std(rms))),
        "spectral_centroid_hz_mean": finite(float(np.mean(centroid)), 2),
        "spectral_centroid_hz_std": finite(float(np.std(centroid)), 2),
        "spectral_bandwidth_hz_mean": finite(float(np.mean(bandwidth)), 2),
        "spectral_rolloff_hz_mean": finite(float(np.mean(rolloff)), 2),
        "spectral_flatness_mean": finite(float(np.mean(flatness))),
        "spectral_contrast_mean": finite(float(np.mean(contrast))),
        "energy_share": {
            "below_150_hz": finite(low),
            "150_to_2000_hz": finite(mid),
            "above_2000_hz": finite(high),
        },
        "percussive_share": finite(percussive_share),
        "tonal_entropy_bits": finite(tonal_entropy),
        "climax": {
            "segment": climax_index + 1,
            "time_sec": finite((climax_index + 0.5) * segment_seconds, 2),
            "relative_score": finite(climax_score[climax_index]),
        },
        "timeline_12_segments": timeline,
    }


def analyze_url(url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        raw = folder / "source_audio"
        wav = folder / "decoded.wav"
        download = download_audio(url, raw)
        decode_audio(raw, wav)
        analysis = analyze_wav(wav)
        return download, analysis


def choose_itunes_match(
    artist: str,
    track: str,
    mb_candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    candidates = itunes_candidates(artist, track)
    if not candidates:
        return None

    best = candidates[0]
    if best["title_score"] < 0.72 or best["artist_score"] < 0.62:
        return None

    expected_durations = [
        item["duration_ms"]
        for item in mb_candidates[:3]
        if isinstance(item.get("duration_ms"), int)
    ]
    if expected_durations and isinstance(best.get("duration_ms"), int):
        closest = min(
            abs(best["duration_ms"] - expected) for expected in expected_durations
        )
        best["duration_difference_to_musicbrainz_ms"] = closest
        # Large differences are allowed only when the title/artist match is extremely strong.
        if closest > 30_000 and best["match_score"] < 0.93:
            return None

    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", required=True)
    parser.add_argument("--track", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result: dict[str, Any] = {
        "request": {
            "artist": args.artist,
            "track": args.track,
            "request_id": args.request_id,
        },
        "status": "started",
        "warnings": [],
    }

    try:
        mb_candidates = musicbrainz_candidates(args.artist, args.track)
    except Exception as exc:
        mb_candidates = []
        result["warnings"].append(f"MusicBrainz lookup failed: {exc}")

    result["musicbrainz_candidates"] = mb_candidates[:5]

    # 1. Explicit public audio URL, if supplied.
    if args.source_url:
        try:
            download, analysis = analyze_url(args.source_url)
            result.update(
                {
                    "status": "heard_direct_public_audio",
                    "source": {
                        "kind": "explicit_public_https_audio",
                        "download": download,
                    },
                    "analysis": analysis,
                }
            )
        except Exception as exc:
            result["warnings"].append(f"Direct URL analysis failed: {exc}")

    # 2. Archived full-recording features.
    if result["status"] == "started":
        for candidate in mb_candidates[:5]:
            if candidate.get("local_match_score", 0) < 0.75:
                continue
            try:
                profile = acousticbrainz_summary(candidate["mbid"])
            except Exception as exc:
                result["warnings"].append(
                    f"AcousticBrainz lookup failed for {candidate['mbid']}: {exc}"
                )
                continue
            if profile:
                result.update(
                    {
                        "status": "analyzed_archived_full_recording_features",
                        "matched_recording": candidate,
                        "source": {
                            "kind": "AcousticBrainz",
                            "audio_was_not_downloaded": True,
                        },
                        "analysis": profile,
                    }
                )
                break

    # 3. Official short preview, processed transiently.
    if result["status"] == "started":
        try:
            preview = choose_itunes_match(
                args.artist, args.track, mb_candidates
            )
            if preview and preview.get("preview_url"):
                download, analysis = analyze_url(preview["preview_url"])
                result.update(
                    {
                        "status": "heard_official_short_preview",
                        "matched_recording": preview,
                        "source": {
                            "kind": "Apple_iTunes_official_preview",
                            "store_url": preview.get("store_url"),
                            "download": download,
                            "retained_audio": False,
                        },
                        "analysis": analysis,
                    }
                )
                result["warnings"].append(
                    "Only the official short preview was heard; this is not a full-track analysis."
                )
        except Exception as exc:
            result["warnings"].append(f"Official preview analysis failed: {exc}")

    if result["status"] == "started":
        result["status"] = "no_usable_open_features_or_permitted_audio_found"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
