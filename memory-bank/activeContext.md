# Active Context

## Current Situation

This repository now runs a simplified Bilibili video knowledge workflow with:

- link-first ingest
- subtitle-first acquisition
- ASR fallback
- OpenAI-first extraction with extractive fallback
- simplified Obsidian export
- desktop XMind export
- automatic related-video links

## Most Recent Work

On 2026-04-20, the storage model was simplified:

- Obsidian was reduced to `01 知识笔记` and `02 索引导航`
- desktop folder `C:\Users\yy198\Desktop\B站视频XMind` was added for all `.xmind` files
- legacy topic/concept/transcript/mindmap layers were removed
- note-to-note relation blocks were added
- real video `BV1Zk9FBwELs` was reprocessed into the new structure

Later on 2026-04-20, XMind open-failure debugging found a second issue:

- the generated `.xmind` archive only contained `content.xml`, `styles.xml`, and `comments.xml`
- the current XMind desktop client rejected it as corrupted because `META-INF/manifest.xml` and `meta.xml` were missing
- `src/video_kb/xmind_export.py` now repairs the archive after save and writes those files back in
- the repaired `BV1Zk9FBwELs` file was accepted by the installed XMind client

Later on 2026-04-20, XMind readability was improved without changing the simplified vault model:

- the Harness-specific knowledge tree was deepened so `成熟 Harness 的六层` now has explanatory child nodes instead of bare labels
- `src/video_kb/xmind_export.py` now enriches some leaf nodes with short recall-oriented detail lines
- the exporter now injects branch palettes and depth-based topic styles into `styles.xml` and applies matching `style-id` values in `content.xml`
- real video `BV1Zk9FBwELs` was reprocessed again so the desktop `.xmind` file reflects the richer structure and color styling

Later on 2026-04-20, the workflow was wrapped as a reusable skill:

- repo skill created at `.agents/skills/bilibili-video-kb`
- local installed copy created at `C:\Users\yy198\.codex\skills\bilibili-video-kb`
- helper script `run-video-kb.ps1` now resolves the repo root and reuses the canonical setup/run scripts
- the skill was validated with `quick_validate.py` and exercised against the real `BV1Zk9FBwELs` link
- a git branch `codex/bilibili-video-kb-skill` was created and the relevant files were staged
- GitHub upload is currently blocked because this repo has no configured remote and Git has no `user.name` / `user.email`

Current validated artifacts:

- `D:\Document\Win_Obsidian知识库\YYH个人知识库\08 视频知识库\01 知识笔记\2026\BV1Zk9FBwELs 最近爆火的 Harness Engineering 到底是啥？一期讲透！.md`
- `D:\Document\Win_Obsidian知识库\YYH个人知识库\08 视频知识库\02 索引导航\总索引.md`
- `C:\Users\yy198\Desktop\B站视频XMind\BV1Zk9FBwELs 最近爆火的 Harness Engineering 到底是啥？一期讲透！.xmind`

## Current Priorities

- validate more real Bilibili knowledge videos
- keep the new `bilibili-video-kb` skill in sync with the underlying pipeline
- finish commit/push once the user provides remote and git identity
- improve subtitle hit rate
- improve extractive quality on non-Harness topics
- tune XMind richness and styling against more topic families
- improve relation detection between overlapping videos

## Next Step For A Fresh Thread

Read:

1. `AGENTS.md`
2. `README.md`
3. `memory-bank/activeContext.md`
4. `memory-bank/tasks.md`
5. `memory-bank/progress.md`
6. `docs/VIDEO_KB_AUTOMATION.md`

Then continue with:

- another real video ingest
- extractor improvements for another topic family
- XMind style and detail tuning on another real topic family
- relation-link quality improvements

## Parallel Advisory Context: Control Agent Roadmap

There is also an active advisory thread using this repository as the decision hub for the external control project described in:

- `docs/CONTROL_AGENT_ROADMAP_CN.md`
- `docs/CONTROL_PIPELINE_DEMO_MAP.md`

Latest confirmed advisory state on 2026-04-20:

- promoted checkpoint remains `llm_autonomy_v2_phase2d_activation_neutrality_v4`
- residual control-route drift is no longer treated as one global issue
- current residual breakpoints are slice-specific and not same-source:
  - `A01`: `candidate_count_changed`
  - `B02 measurement_noise_medium`: `repair_gate_outcome_changed`
  - `C01 nominal_boundary`: `selection_mse_changed`
- current best next-step candidates by slice are:
  - `B02 measurement_noise_medium`: `repair-gate follow-up under seed_first`
  - `C01 nominal_boundary`: `BO evaluation realization floor follow-up`
- rejected candidates:
  - `invocation_selected_seed_only_contained`
  - `seed_bundle`
  - `seed_bundle_repair_follow`
  - `a01_probe_count_parity_followup`
- `B02 measurement_noise_medium` is currently the closest slice to being compressed first
- `struct_ladder_relax_min_stage_zero` still only has the weakest aligned signal on `B02 measurement_noise_medium` and remains `shadow-positive, live-not-yet-cleared`
- latest advisory judgment:
  - `B02` still has not been stably compressed
  - next efficient move is narrower `B02 repair-branch quality / score-dominance` follow-up
  - `C01` stays only as a secondary candidate
  - `repair_gate_outcome_changed` is now the confirmed gate-level breakpoint for `B02`
  - `local_refine` is currently downstream, not the main breakpoint
