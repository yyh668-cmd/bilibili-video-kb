# Tasks

## In Progress

- stabilize the simplified `video-kb` workflow
- keep the `bilibili-video-kb` skill aligned with the underlying pipeline
- validate more real Bilibili knowledge videos
- improve non-OpenAI extractive quality
- tune XMind richness and visual hierarchy

## Next Likely Tasks

- test videos with official subtitles
- test videos with AI subtitles
- test videos with no subtitles but downloadable audio
- test multi-part Bilibili videos
- improve Bilibili subtitle track selection
- generalize the current Harness-specific extractive logic into a reusable topic-template mechanism
- test whether the new XMind detail/styling approach works well outside Harness videos
- improve note-to-note relation detection

## Explicitly Not In Scope

- vector database integration
- speaker diarization as the default path
- rebuilding a complex topic/concept/transcript structure in Obsidian

## Done

- added `pyproject.toml` and the `src/video_kb/` package
- added `scripts/setup_video_kb.ps1`
- added `scripts/run_video_kb.ps1`
- added the reusable skill `.agents/skills/bilibili-video-kb`
- implemented `video_kb.cli doctor`
- implemented URL and local-media dual input
- implemented Bilibili metadata extraction
- implemented subtitle-first plus ASR fallback
- implemented OpenAI plus extractive dual backend
- implemented desktop `.xmind` export
- enriched XMind export with branch styling and deeper recall-oriented nodes
- wrapped the workflow as the reusable `bilibili-video-kb` skill
- simplified Obsidian to notes plus navigation only
- implemented automatic related-video links
- added and updated unit tests
- reprocessed real video `BV1Zk9FBwELs` into the new structure

## Parallel Advisory Tasks: Control Agent

- keep promoted checkpoint fixed at `llm_autonomy_v2_phase2d_activation_neutrality_v4`
- do not resume full live `Phase 2D` yet
- do not expand `controller family` yet
- next control-roadmap task:
  - continue slice-stratified `solver_invocation` containment validation
  - focus `B02 measurement_noise_medium`: narrower `repair-branch quality / score-dominance` follow-up under `seed_first`
  - keep `C01 nominal_boundary`: `BO evaluation realization floor follow-up` only as a secondary candidate
- reject current cost-amplifying containment candidates:
  - `seed_bundle`
  - `seed_bundle_repair_follow`
- reject current over-constraining candidate:
  - `invocation_selected_seed_only_contained`
- reject current low-value candidate:
  - `a01_probe_count_parity_followup`
