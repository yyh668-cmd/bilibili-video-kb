# Progress

## Current State

The repository now contains a working Bilibili-to-Obsidian workflow that turns a URL or local media file into:

- one complete knowledge note
- one simple navigation index
- one desktop XMind file

## Milestones

- completed Python package structure in `src/video_kb/`
- completed PowerShell setup and run entry points
- completed subtitle-first / ASR-fallback acquisition
- completed OpenAI / extractive dual extraction
- completed XMind exporter
- completed simplified Obsidian exporters
- completed relation-link refresh logic
- completed base unit tests
- completed installation and usage docs

## Recent Updates

### 2026-04-20

- removed redundant Obsidian layers: topic pages, concept cards, transcript notes, Markdown mind maps
- reduced the vault structure to `01 知识笔记` and `02 索引导航`
- added desktop XMind output to `C:\Users\yy198\Desktop\B站视频XMind`
- added automatic related-video links between notes with overlapping topics/concepts
- migrated the existing library into the new structure
- re-ran real video `BV1Zk9FBwELs`
- verified the codebase with `pytest -q`
- debugged XMind open failure and found the generated archive was missing `META-INF/manifest.xml` and `meta.xml`
- added post-save package repair in `src/video_kb/xmind_export.py`
- confirmed the repaired `BV1Zk9FBwELs` file is accepted by the installed XMind client
- deepened the Harness-specific knowledge tree so the six Harness layers now include explanatory child nodes
- upgraded XMind export from plain black topics to branch-colored styles with depth-based visual hierarchy
- added tests that verify style injection and richer knowledge-tree detail nodes
- reprocessed `BV1Zk9FBwELs` again so the shipped desktop `.xmind` matches the new richer/styled export
- created the reusable repo skill `.agents/skills/bilibili-video-kb`
- installed the same skill into `C:\Users\yy198\.codex\skills\bilibili-video-kb`
- added a skill wrapper script that reuses the canonical setup/run entry points
- validated the skill with `quick_validate.py` and a real Bilibili ingest run
- configured local git identity for this repo
- connected remote `origin` to `https://github.com/yyh668-cmd/bilibili-video-kb.git`
- committed the workflow and pushed it to `origin/master`

### 2026-04-20 Parallel Advisory: Control Agent

- used this repository's control-roadmap docs as the decision hub for the external control project
- confirmed the promoted checkpoint stays at `llm_autonomy_v2_phase2d_activation_neutrality_v4`
- narrowed residual control-route drift from broad invocation mismatch to slice-specific breakpoints:
  - `A01`: `warm_start_probe_path / candidate_count_changed`
  - `B02 measurement_noise_medium`: `repair_gate_outcome_changed`
  - `C01 nominal_boundary`: `selection_mse_changed`
- confirmed that `seed_bundle` and `seed_bundle_repair_follow` are not good next-step candidates because they amplify cost without enough drift compression
- concluded the next efficient move is slice-stratified `solver_invocation` screening instead of another global containment tweak
- confirmed the three slices are not same-source residuals:
  - `A01` and `C01` still share a higher-level warm-start/probe family but already require different follow-ups
  - `B02 measurement_noise_medium` should be handled independently
- identified next slice-specific candidates:
  - `B02 measurement_noise_medium`: `repair-gate follow-up under seed_first`
  - `C01 nominal_boundary`: `BO evaluation realization floor follow-up`
- identified `B02 measurement_noise_medium` as the closest slice to being compressed first
- confirmed `struct_ladder_relax_min_stage_zero` still only shows the weakest aligned signal on `B02 measurement_noise_medium` and remains `shadow-positive, live-not-yet-cleared`
- confirmed `A01 probe-count parity follow-up` should be retired from the main candidate pool because it increased `candidate_count` and raised cost without moving toward fixed behavior
- confirmed `B02-first` work still has not stably compressed `B02`; next step should narrow from generic follow-up to targeted `repair/local_refine gate` audit under `seed_first`
- confirmed `C01 BO evaluation realization floor follow-up` remains only a secondary candidate because it moves the breakpoint but increases cost
- confirmed the `B02` gate-level breakpoint is specifically `repair_gate_outcome_changed`, not generic `repair/local_refine gate`
- confirmed `repair_applied` is still misaligned because the contained shadow path already scores as `success`, so the default repair branch early-stops and forced probing has not yet produced a score-dominating repaired path
- concluded the next step should narrow again from gate audit to `B02 repair-branch quality / score-dominance` follow-up under `seed_first`

## Next Milestones

- validate more real knowledge videos under different subtitle conditions
- improve extractive quality on additional topic families
- validate the new XMind richness/styling approach on another topic family
- improve relation-link precision
