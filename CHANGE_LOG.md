# Change Log

Entries are append-only, newest entries last.

## 2026-07-04 - Initial delegation benchmark lab scaffold

- Created the public-safe Agent Delegation Lab repository.
- Added a governance contract for high-volume delegated extraction benchmarks.
- Added the first benchmark plan for MP11 PDF document metadata indexing.
- Established ignore rules so raw PDFs, raw text extracts, transcripts, runtime
  outputs, and provider credentials remain untracked.

## 2026-07-04 - GitHub issue map initialized

- Created P0 issue #1 for repository scaffold and benchmark boundaries.
- Created P1 issue #2 for the MP11 document metadata indexing benchmark.
- Updated the roadmap issue map so the benchmark lab has a concrete public
  tracker before deeper delegation experiments begin.

## 2026-07-04 - Started P1 MP11 chunk substrate

- Opened `feature/p1-mp11-document-index`.
- Added `scripts/extract_mp11_chunks.py` to export MP11 page text chunks into
  ignored runtime space and write a sanitized tracked manifest.
- Extracted 475 MP11 page chunks from the verified public PDF source.
- Added `benchmarks/mp11_document_metadata_index/chunk_manifest.json` with
  page IDs, component ranges, text hashes, word counts, character counts, and
  runtime paths without committing raw text.
- Recorded the first substrate statistics: 105811 extracted words, 723498
  extracted characters, and 3 effectively empty pages.
- Opened draft PR #3 as the P1 review surface without close wording.

## 2026-07-04 - Ran P1 MP11 structure-pass A/B iteration

- Added `scripts/build_mp11_structure_pass.py` to generate ignored structure
  pass worker tickets and eval manifests from the tracked chunk manifest plus
  ignored runtime chunks.
- Ran four structure-pass bundles against `qwen3-coder:latest` and
  `qwen3-coder-next:latest` with one repeat per model and bundle.
- Added `scripts/summarize_mp11_structure_pass.py` plus tracked sanitized
  outputs summarizing aggregate outcomes, token counts, field-compliance
  issues, and supervisor spot-check results.
- Observed that `qwen3-coder:latest` hit the first-run operator cutoff on all
  four tested bundles, while `qwen3-coder-next:latest` completed three of four
  and produced 80 parseable candidate structure records.
- Recorded 72862 observed local-worker input tokens and 19893 output tokens at
  zero cash cost for completed `qwen3-coder-next:latest` runs.

## 2026-07-04 - Ran P1 supervisor-token economics iteration

- Measured the first paid-supervisor-token baseline for the
  `appendix-a-opening-structure` bundle.
- Produced a direct supervisor baseline with 26 derived structure records at a
  measured cost of `$0.153581`.
- Audited the existing `qwen3-coder-next:latest` worker output: 15 accepted
  records, 6 repairable records, and 4 rejected records from 25 candidates.
- Measured delegated audit cost at `$0.171488` plus zero-cash local worker
  tokens, yielding a measured net loss of `$0.017907` for this small bundle and
  full-audit protocol.
- Measured tracked reporting/update overhead at `$0.613541`, identifying
  supervisor-written reporting as the dominant cost to reduce or amortize.
- Increased the structure-pass worker timeout default to 7200 seconds and
  reclassified previous 360-second stops as operator cutoffs rather than
  evidence of stalled or failed Ollama runs.

## 2026-07-04 - Ran P1 MP11 scale-sequence iteration

- Added a scale-sequence ticket builder for the MP11 structure-pass benchmark.
- Ran `qwen3-coder-next:latest` on x2, x4, x8, and x16 page-window bundles
  with 7200-second worker timeouts and no operator cutoffs.
- Recorded structured, sanitized experiment observations under
  `benchmarks/mp11_document_metadata_index/scale_sequence_01/`.
- Observed that worker input tokens scaled with document size, but candidate
  record yield did not scale monotonically: x4 and x16 returned valid JSONL
  with severe under-extraction.
- Measured the paid-supervisor scale-sequence span rollup at `$0.826415` for
  setup, ticket build, worker orchestration, output summarization, and audit
  interpretation, excluding separate Agent Workbench fixture implementation
  cost.

## 2026-07-04 - Ran P1 fixed-x8 bundle packaging iteration

- Added fixed-x8 bundled ticket generation for the same MP11 pages 46-141 used
  by the prior x8 single-ticket run.
- Tested `x8-2x48` and `x8-4x24` packaging with `qwen3-coder-next:latest` and
  `gpt-oss:20b` after the Ollama keep-alive restart.
- Reused the existing `$1.228648` direct-supervisor baseline because the input
  definition did not change.
- Observed materially higher candidate yield than the prior x8 single-ticket
  run: 48-70 bundle records versus 27 single-ticket records.
- Observed that `gpt-oss:20b` produced useful candidate density but had a
  format issue in the `x8-2x48` first part, while `qwen3-coder-next:latest`
  had one salvageable model-call failure in the `x8-4x24` second part.
- Measured benchmark-operation supervisor overhead at `$0.632602`, which is
  `$0.596046` below the reused direct-supervisor baseline before source-level
  audit/repair allocation.

## 2026-07-04 - Audited P1 fixed-x8 supervisor overhead

- Added `planning/phase1_mp11_x8_bundle_overhead_audit.md`.
- Broke the fixed-x8 sequence 02 supervisor overhead into span-level fresh
  input, cached input, output, reasoning, and cash-cost components.
- Identified `worker_output_summarize`, `worker_run_orchestration`, and
  `github_hygiene` as the dominant cost centers that likely include
  reducible paid-token burn.
- Recorded the next optimization direction: quiet batch runners,
  script-first summaries, batched GitHub hygiene, and shifting paid tokens
  toward source-level audit/repair.
