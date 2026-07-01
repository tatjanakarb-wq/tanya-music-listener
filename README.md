# Tanya Music Listener — GitHub Actions pilot

A small personal, noncommercial music-analysis pipeline.

## What it does

For an artist and track name, the workflow:

1. Resolves candidate recordings through MusicBrainz.
2. Checks archived AcousticBrainz full-recording features.
3. If no archived profile is available, searches the official Apple/iTunes
   catalogue for a high-confidence short preview.
4. Processes permitted audio transiently with ffmpeg + librosa.
5. Writes a compact JSON profile to `results/`.
6. Deletes temporary audio automatically when the GitHub runner ends.

It does not bypass DRM, logins, paywalls, or protected streams.

## First manual pilot

1. Create a **public** GitHub repository.
2. Upload all files and folders from this package, including `.github`.
3. Open the repository's **Actions** tab.
4. Select **Listen to a track**.
5. Choose **Run workflow** and enter an artist and track.
6. Wait for the green check.
7. Open `results/latest.json`.

## Why the repository is public

Standard GitHub-hosted runners are free for public repositories.
The repository contains code and acoustic result JSON only—no audio and no
passwords.

## Automatic Google gateway

After the manual pilot works, paste `apps_script/Code.gs` into a new Google
Apps Script project. Store the GitHub token and other values in Script
Properties; never commit the token to this repository.

The gateway invokes `workflow_dispatch`; GitHub writes the result; the caller
reads the public raw JSON URL.
