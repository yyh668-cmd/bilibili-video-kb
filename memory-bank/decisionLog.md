# Decision Log

## 2026-03-28

### Repository files are the source of truth

Project state should live in repository files, not in chat history, so a fresh thread can recover context reliably.

### Start simple with file-based memory

Do not introduce vector databases or external memory systems before the core workflow is proven.

### Open a new thread at milestone boundaries

Prefer updating handoff files and then starting a fresh thread rather than stuffing every task into one giant conversation.

## 2026-04-20

### Default repo focus is the Bilibili video knowledge workflow

The old demo/control material remains in the repo, but the default working focus is now processing Bilibili knowledge videos into reusable study assets.

### Cache artifacts stay outside the vault

Intermediate downloads, transcripts, analysis files, and manifests live under `.cache/video_kb/`. Only end-user reading assets are written into Obsidian and the desktop XMind folder.

### Bilibili acquisition is fixed as subtitle-first plus ASR fallback

Subtitle availability is too unstable to depend on it. The workflow must keep a local ASR fallback path.

### Extraction is fixed as OpenAI-first with extractive fallback

If `OPENAI_API_KEY` exists, prefer OpenAI for better study-note quality. If not, fall back automatically to extractive mode without breaking the whole run.

### Obsidian is intentionally simplified to two modules

The vault should contain only:

- `01 知识笔记`
- `02 索引导航`

Topic pages, concept cards, transcript notes, and Markdown mind maps were removed as unnecessary complexity for the user.

### XMind files live in one desktop folder

All generated `.xmind` files are exported to:

- `C:\Users\yy198\Desktop\B站视频XMind`

This keeps them easy to open with the installed XMind client.

### XMind archives must be repaired after save

The current Python `xmind` library writes only `content.xml`, `styles.xml`, and `comments.xml` for new workbooks. The installed XMind desktop client rejects that archive as corrupted. The exporter therefore post-processes every generated `.xmind` and adds:

- `meta.xml`
- `META-INF/manifest.xml`

### XMind should carry the extra study density, not a more complex Obsidian structure

The user wants richer review support, but not by rebuilding topic pages, concept-card folders, or other multi-layer Obsidian structures. The correct direction is:

- keep Obsidian as `知识笔记 + 索引导航`
- enrich the `.xmind` output with one more layer of distilled explanation where it helps recall
- add visual hierarchy through branch-level styling and color, instead of expanding vault complexity

### The workflow should be exposed as a reusable skill, not only as raw scripts

The video knowledge workflow is now important and recurring enough that it should be invoked through a dedicated skill. The skill should:

- trigger on Bilibili link-to-note/XMind requests
- reuse the canonical repo scripts instead of duplicating pipeline logic
- live in the repo so it can be versioned and pushed with the codebase

### Related-note links are written directly into knowledge notes

Instead of using separate topic/concept pages, videos that overlap in topics or concepts should link directly to each other from their own `关联视频` section.

### Specialized extractive branches are allowed when generic extractive quality clearly fails

Real video `BV1Zk9FBwELs` showed that a pure generic extractive path can collapse on mixed Chinese-English technical content. For high-value recurring topic families, specialized extraction logic is preferable to shipping bad notes.

### Control-roadmap advisory work uses slice-stratified screening once residual drift becomes heterogeneous

For the external control-project advisory thread driven by `docs/CONTROL_AGENT_ROADMAP_CN.md`, once residual drift no longer shares one global breakpoint and instead separates into slice-specific breakpoints such as `candidate_count_changed`, `repair_gate_outcome_changed`, and `selection_mse_changed`, the next-step strategy should switch from global containment tuning to slice-stratified screening. Cost-amplifying but non-locking candidates should still be rejected from the mainline candidate set.

### Once slice-stratified screening is established, execution priority should follow compression likelihood, not symmetry

For the control-roadmap advisory thread, once `A01`, `B02 measurement_noise_medium`, and `C01 nominal_boundary` are confirmed as non-same-source residual slices, the next step should not spend equal effort on all three. Priority should follow the slice with the highest observed compression likelihood. Current order is:

- `B02 measurement_noise_medium` first
- `A01` next
- `C01 nominal_boundary` after that

This is a deliberate efficiency choice, not a change in the overall roadmap.

### B02-first follow-up did not yet make B02 the first stably compressed slice

In the control-roadmap advisory thread, the `B02-first` slice-prioritized follow-up confirmed that `B02 measurement_noise_medium` remains the highest-priority slice, but the tested `repair-gate follow-up under seed_first` did not move the breakpoint past `repair_gate_outcome_changed` and did not align `repair_applied` with fixed execution. At the same time:

- `A01 probe-count parity follow-up` should be retired as `cost-amplifying`
- `C01 BO evaluation realization floor follow-up` should remain only as a secondary slice-specific candidate
- `struct_ladder_relax_min_stage_zero` still remains `shadow-positive, live-not-yet-cleared`

### When B02 remains highest priority but generic B02 follow-up stalls, narrow to gate-level audit instead of widening the candidate pool

For the control-roadmap advisory thread, if `B02 measurement_noise_medium` remains the most compressible slice but broad follow-up under `seed_first` fails to move the breakpoint past `repair_gate_outcome_changed`, the next efficient move is not to add more global or broad B02 candidates. The next step should narrow to a gate-level audit of `repair / local_refine` decision points under the existing containment. This is a scope-narrowing efficiency decision, not a retreat from the roadmap.

### Once B02 gate-level audit confirms the breakpoint is specifically repair_gate_outcome, shift to branch-quality and score-dominance analysis

For the control-roadmap advisory thread, once `B02` is narrowed further and `repair_gate_outcome_changed` is confirmed as the actual breakpoint while `local_refine` is only downstream, the next step should no longer treat `repair` and `local_refine` as equal candidates. If the contained shadow path already evaluates as `success`, then the key question becomes why forced repair probing still fails to produce a score-dominating repaired branch. At that point the efficient next step is `repair-branch quality / score-dominance` follow-up, not broader gate expansion.

### The B02 gate-level main breakpoint is repair-gate outcome, not local-refine

In the control-roadmap advisory thread, targeted gate-level audit under `seed_first` showed that `B02 measurement_noise_medium` still diverges from fixed execution first at `repair_gate_outcome_changed`. The fixed `v4` raw run for `B02_noise_promoted` seed 0 has:

- `repair_applied = True`
- `local_refine_applied = False`

but current contained shadow execution remains:

- `repair_applied = False`
- `local_refine_applied = False`

Forcing a repair-gate probe on success did not align `repair_applied`, which means the mismatch is not explained only by the "success => skip repair" short-circuit. Forcing local-refine on success made `local_refine_applied = True` and slightly lowered `selection_mse`, but it left the main breakpoint unchanged and amplified cost, so local refine should be treated as a downstream branch, not the current primary gate-level problem.
