# Product Context

## Audience

The user watches dense knowledge videos on Bilibili and wants a repeatable way to turn them into reusable study material.

## User Value

The workflow should reduce "watched but forgotten" by producing:

- one complete knowledge note per video
- one professional XMind map per video
- one simple Obsidian index page for navigation
- related-note jump links when different videos overlap

## UX Intent

- Link in, note out
- Obsidian should stay simple
- XMind files should live in one obvious desktop folder
- Navigation should stay lightweight as the library grows

## Current Product Shape

The repository now exports:

- complete knowledge notes to `01 知识笔记`
- a simplified index note to `02 索引导航`
- XMind files to the desktop XMind folder
- cache-side manifests for reruns and debugging

## Likely Future Work

- better subtitle hit rate
- better extractive quality on more topic families
- stronger note-to-note relation detection
