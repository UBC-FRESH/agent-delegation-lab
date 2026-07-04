# Phase 1 MP11 Economics Iteration 02

This checkpoint is the first supervisor-token-instrumented MP11 delegation
economics test.

## Test Target

- benchmark id: `mp11_p1_iteration_02`
- bundle: `appendix-a-opening-structure`
- source pages: `46-57`
- source package: `tfl6_mp11_202606_public_pdf`
- source SHA256: `44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b`

## Lanes

Direct supervisor baseline:

- producer: paid Codex supervisor
- output: 26 derived structure records
- fresh supervisor input tokens: `4343`
- cached supervisor input tokens: `445056`
- supervisor output tokens: `4376`
- supervisor reasoning output tokens: `488`
- measured cost: `$0.153581`

Delegated lane:

- worker model: `qwen3-coder-next:latest`
- worker output: 25 candidate records
- worker input tokens: `20708`
- worker output tokens: `5463`
- worker cash cost: `$0`
- supervisor audit fresh input tokens: `9246`
- supervisor audit cached input tokens: `630272`
- supervisor audit output tokens: `2568`
- supervisor audit reasoning output tokens: `647`
- supervisor audit cost: `$0.171488`

Audit outcome:

- accepted records: `15`
- repairable records: `6`
- rejected records: `4`
- needs-review records: `0`
- accepted or repairable records: `21`
- accepted or repairable fraction: `0.84`

## Economics Result

This specific protocol did not win.

```text
direct supervisor baseline cost = $0.153581
delegated lane audit cost        = $0.171488
worker cash cost                 = $0
net savings                      = -$0.017907
```

The worker output was mostly useful, but full supervisor record-by-record audit
cost more than direct supervisor extraction for this 12-page bundle.

Setup/orientation cost was also measured separately:

- setup fresh supervisor input tokens: `89054`
- setup cached supervisor input tokens: `305792`
- setup supervisor output tokens: `952`
- setup supervisor reasoning output tokens: `273`
- setup cost: `$0.226508`

Setup is not assigned solely to this bundle because it should be amortized over
repeated benchmark iterations.

Tracked reporting/update overhead was also measured:

- tracked-update fresh supervisor input tokens: `17419`
- tracked-update cached supervisor input tokens: `2746880`
- tracked-update supervisor output tokens: `6337`
- tracked-update supervisor reasoning output tokens: `974`
- tracked-update cost: `$0.613541`

This is currently the dominant paid-supervisor cost. It is not lane-local
extraction cost, but it is real workflow overhead. Agent Workbench will not win
economically unless this reporting/update cost is reduced, automated, or
amortized across larger batches.

## Interpretation

The result is useful precisely because it is a measured loss, not a guess.

What appears promising:

- `qwen3-coder-next:latest` can extract mostly grounded structure records from
  MP11 page chunks.
- The useful-record rate was high enough that the task class still deserves
  more testing.
- Local worker token volume was non-trivial and still zero cash cost.

What failed economically:

- A full paid supervisor audit of every worker record was too expensive.
- The selected 12-page bundle was probably too small to amortize ticket,
  context, and audit overhead.
- The worker produced low-value acronym guesses from the acknowledgements page,
  which increased audit burden.
- The reporting/update ritual itself cost more than the extraction comparison,
  so future runs need compact auto-generated reports instead of verbose
  supervisor-written narration.

## Protocol Changes

The next iteration should:

- use long worker timeouts by default;
- treat previous 360-second stops as operator cutoffs, not model failures;
- use larger page bundles or multiple bundles per supervisor audit;
- require workers to suppress low-value acronym expansion unless the source
  explicitly defines the term;
- use stratified audit sampling plus automated schema checks before falling
  back to full record-by-record audit; and
- compare cost per accepted-or-repairable record, not just total run cost.
- minimize tracked-update narration and let scripts render standard economics
  reports from runtime ledgers.

## Public-Safety Boundary

Raw PDF chunks, raw worker outputs, direct baseline JSONL, and detailed audit
ledgers remain ignored under `runtime/`. The tracked summary records only
sanitized counts, token deltas, costs, and interpretation.
