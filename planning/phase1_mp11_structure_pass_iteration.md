# Phase 1 MP11 Structure-Pass Iteration

This checkpoint records the first model-backed structure-pass A/B run for
the MP11 document metadata-indexing benchmark.

## Result

- run count: `8`
- completed runs: `3`
- timeouts: `5`
- candidate records parsed: `80`
- format-issue runs: `3`
- wrong worker-model labels: `13`
- observed local-worker tokens: `72862` input, `19893` output, cash cost `0`

## Model Outcomes

| Model | Outcome | Count |
| --- | --- | ---: |
| `qwen3-coder:latest` | `timeout` | 4 |
| `qwen3-coder-next:latest` | `completed-parseable` | 3 |
| `qwen3-coder-next:latest` | `timeout` | 1 |

## Bundle Summary

| Bundle | Model | Outcome | Records | Page Span | Input Tokens | Output Tokens | Caveats |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| `appendix-a-late-structure` | `qwen3-coder:latest` | `timeout` | 0 | `` | 0 | 0 | no assistant message |
| `appendix-a-late-structure` | `qwen3-coder-next:latest` | `completed-parseable` | 42 | `180-224` | 22391 | 11509 | 1 duplicate record ids |
| `appendix-a-opening-structure` | `qwen3-coder:latest` | `timeout` | 0 | `` | 0 | 0 | no assistant message |
| `appendix-a-opening-structure` | `qwen3-coder-next:latest` | `completed-parseable` | 25 | `46-57` | 20708 | 5463 | 1 malformed source SHA records |
| `appendix-b-opening-structure` | `qwen3-coder:latest` | `timeout` | 0 | `` | 0 | 0 | no assistant message |
| `appendix-b-opening-structure` | `qwen3-coder-next:latest` | `completed-parseable` | 13 | `230-250` | 29763 | 2921 | 13 wrong worker_model labels; 2 duplicate record ids |
| `main-plan-structure` | `qwen3-coder:latest` | `timeout` | 0 | `` | 0 | 0 | no assistant message |
| `main-plan-structure` | `qwen3-coder-next:latest` | `timeout` | 0 | `` | 0 | 0 | no assistant message |

## Supervisor Spot Check

Sampled records were checked against ignored source chunks for Appendix A
opening, Appendix A late, and Appendix B opening pages. The checked records
were grounded in the supplied text, but the run is not clean enough to
promote without a stricter second-pass ticket.

## Interpretation

`qwen3-coder-next:latest` is the only useful candidate from this run. It
returned parseable records for three of four bundles and consumed large
zero-cash local-worker token volumes. `qwen3-coder:latest` timed out on
all four bundles and should not be used for this task shape without much
smaller tickets or a different timeout strategy.

The next iteration should split tickets more finely, require strict JSONL
again, and add automated validation for constants, worker_model, duplicate
record IDs, source SHA, and object_type values before any index records are
accepted.
