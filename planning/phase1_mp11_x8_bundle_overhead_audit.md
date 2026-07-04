# Phase 1 MP11 Fixed-X8 Supervisor Overhead Audit

This note audits the measured paid-supervisor overhead from the fixed-x8
bundle sequence 02 run. The goal is to identify which supervisor-token costs
materially affected the delegated task result and which costs are mostly
workflow/reporting burn.

## Measured Cost Breakdown

| Span | Fresh Input | Cached Input | Output + Reasoning | Fresh USD | Cached USD | Output USD | Total USD | Share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `worker_output_summarize` | 7,984 | 1,341,312 | 3,803 | 0.013972 | 0.234730 | 0.053242 | 0.301944 | 41.0% |
| `worker_run_orchestration` | 52,083 | 513,024 | 1,828 | 0.091145 | 0.089779 | 0.025592 | 0.206516 | 28.0% |
| `github_hygiene` | 2,124 | 488,576 | 1,046 | 0.003717 | 0.085501 | 0.014644 | 0.103862 | 14.1% |
| `supervisor_audit` | 2,677 | 305,920 | 637 | 0.004685 | 0.053536 | 0.008918 | 0.067139 | 9.1% |
| `setup` | 1,210 | 270,592 | 538 | 0.002118 | 0.047354 | 0.007532 | 0.057003 | 7.7% |
| **Total** | **66,078** | **2,919,424** | **7,852** | **0.115637** | **0.510899** | **0.109928** | **0.736464** | **100.0%** |

The direct-supervisor baseline for the same fixed input is `$1.228648`.
The measured benchmark-operation overhead including GitHub hygiene is
`$0.736464`, leaving a preliminary delta of `-$0.492184` before source-level
audit and repair are allocated.

## Materiality Classification

| Span | Material to delegated result? | Assessment |
| --- | --- | --- |
| `worker_run_orchestration` | Partly | Running workers is required, but the supervisor should not need to ingest verbose execution output. Most of this span can likely be moved into a quiet runner that writes logs under ignored runtime paths and prints only a compact status table. |
| `worker_output_summarize` | Partly | A sanitized summary is required, but much of the paid cost is supervisor-visible rendering and interpretation. Scripts should produce the tracked summary directly; the supervisor should inspect only anomaly summaries and a few high-signal metrics. |
| `supervisor_audit` | Yes | This is the most defensible paid-supervisor spend so far. It is small and directly affects interpretation of model/packaging quality. Future spending should shift toward this category, especially source-level acceptance/repair sampling. |
| `setup` | Weakly | Required to establish the run, but mostly reusable. It should amortize over larger batches. |
| `github_hygiene` | No, for task quality | Required for repository workflow discipline, but it does not improve the delegated task result. It should be batched, templated, and minimized for benchmark economics. |

## Main Finding

The largest cost center was not source-level audit. It was supervisor-visible
summarization/reporting:

- `worker_output_summarize`: `$0.301944`
- `worker_run_orchestration`: `$0.206516`
- `github_hygiene`: `$0.103862`

Together, these three spans cost `$0.612322`, or 83.1% of the measured
overhead including GitHub hygiene. Much of that appears to be paid-token burn
that does not materially improve worker output quality.

## Recommended Cost-Cutting Changes

1. Add a quiet batch runner.
   - Input: directory of manifests.
   - Output: ignored machine log plus one compact JSON status table.
   - Console output: one line per manifest with status, elapsed time, model
     status counts, and result paths.
   - Goal: reduce `worker_run_orchestration` fresh input and cached context
     costs.

2. Make summarization fully script-first.
   - The summarizer should compute all comparison metrics and write the
     planning note without requiring the supervisor to inspect large tables in
     chat.
   - Supervisor inspection should focus on anomalies only:
     parse errors, model-call failures, format deviations, and record-density
     extremes.
   - Goal: reduce `worker_output_summarize` from the largest cost center to a
     small validation step.

3. Batch GitHub hygiene.
   - Post one compact progress comment after a meaningful tranche, not after
     every micro-iteration.
   - Reuse a generated body file from the summarizer.
   - Goal: preserve issue hygiene without charging the benchmark result for
     verbose hand-written reporting.

4. Shift paid tokens toward source-level audit.
   - The next measured spend should audit accepted/rejected/repairable records
     for one selected bundle lane.
   - This is the cost that determines whether the delegation result is actually
     useful enough to count as savings.

## Next Experiment Implication

The fixed-x8 packaging test looks promising, but the next economics result
should not repeat the same overhead pattern. The next slice should:

- use a quiet runner;
- use generated summary bodies;
- audit only one high-potential lane first, probably `x8-2x48` with
  `qwen3-coder-next:latest` or `x8-4x24` with `gpt-oss:20b`;
- measure source-level audit/repair cost separately from benchmark
  bookkeeping.

