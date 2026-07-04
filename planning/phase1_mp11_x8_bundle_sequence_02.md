# Phase 1 MP11 Fixed-X8 Bundle Sequence 02

At least one bundle lane needs format or execution inspection.

Fixed benchmark input:

- pages: 46-141
- direct supervisor baseline: `$1.228648`

| Strategy | Model | Parts | Worker In | Worker Out | Records | Records / Page | Records / 1k Words | Behavior |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| x8-single-ticket | `qwen3-coder-next:latest` | 1 | 51732 | 7301 | 27 | 0.281 | 1.209 | `usable-structure-candidates` |
| x8-2x48 | `gpt-oss:20b` | 2 | 51870 | 19848 | 48 | 0.500 | 2.149 | `needs-format-debug` |
| x8-2x48 | `qwen3-coder-next:latest` | 2 | 54317 | 19547 | 70 | 0.729 | 3.135 | `high-coverage-candidates` |
| x8-4x24 | `gpt-oss:20b` | 4 | 60362 | 19996 | 61 | 0.635 | 2.732 | `high-coverage-candidates` |
| x8-4x24 | `qwen3-coder-next:latest` | 4 | 59319 | 16313 | 64 | 0.667 | 2.866 | `high-coverage-candidates` |

Part-level yields:

| Strategy | Model | Part | Pages | Worker In | Worker Out | Records | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| x8-2x48 | `gpt-oss:20b` | part01 | 46-93 | 26370 | 12271 | 20 | `completed-unparseable` |
| x8-2x48 | `gpt-oss:20b` | part02 | 94-141 | 25500 | 7577 | 28 | `completed-parseable` |
| x8-2x48 | `qwen3-coder-next:latest` | part01 | 46-93 | 27526 | 6509 | 23 | `completed-parseable` |
| x8-2x48 | `qwen3-coder-next:latest` | part02 | 94-141 | 26791 | 13038 | 47 | `completed-parseable` |
| x8-4x24 | `gpt-oss:20b` | part01 | 46-69 | 13227 | 4908 | 13 | `completed-parseable` |
| x8-4x24 | `gpt-oss:20b` | part02 | 70-93 | 17391 | 6876 | 16 | `completed-parseable` |
| x8-4x24 | `gpt-oss:20b` | part03 | 94-117 | 14725 | 3464 | 13 | `completed-parseable` |
| x8-4x24 | `gpt-oss:20b` | part04 | 118-141 | 15019 | 4748 | 19 | `completed-parseable` |
| x8-4x24 | `qwen3-coder-next:latest` | part01 | 46-69 | 12830 | 4583 | 18 | `completed-parseable` |
| x8-4x24 | `qwen3-coder-next:latest` | part02 | 70-93 | 17191 | 3092 | 12 | `model-call-failure-with-parseable-output` |
| x8-4x24 | `qwen3-coder-next:latest` | part03 | 94-117 | 14547 | 5522 | 22 | `completed-parseable` |
| x8-4x24 | `qwen3-coder-next:latest` | part04 | 118-141 | 14751 | 3116 | 12 | `completed-parseable` |

Economics note:

- The direct-supervisor baseline is reused because this experiment keeps the exact x8 input definition.
- The single-ticket x8 reference is included for shape comparison only; it is the prior sequence-01 qwen run on the same pages.
- Worker token cash cost remains zero under local Ollama.
- Benefit-cost ratios remain unclaimed until measured source-level audit/repair costs are allocated to the bundle lanes.

Measured supervisor-token cost rollup:

| Span | Supervisor USD |
| --- | ---: |
| `setup_and_ticket_build` | 0.057003 |
| `worker_run_orchestration` | 0.206516 |
| `worker_output_summarize` | 0.301944 |
| `supervisor_audit_interpretation` | 0.067139 |
| `x8_bundle_sequence_run_total` | 0.632602 |
| `direct_supervisor_baseline` | 1.228648 |
| `preliminary_overhead_delta` | -0.596046 |

The preliminary overhead delta compares measured benchmark operation overhead to the reused direct-supervisor baseline.
It is favorable for this run, but it is not a final win claim because source-level audit/repair is still unallocated.
