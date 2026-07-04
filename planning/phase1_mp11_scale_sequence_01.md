# Phase 1 MP11 Scale Sequence 01

All scale runs completed with parseable output under the long-timeout protocol, but record yield was non-monotonic and larger contexts showed summary-collapse risk.

| Scale | Pages | Words | Worker In | Worker Out | Records | Records / 1k Words | Behavior | Direct Baseline USD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 2 | 24 | 4255 | 12747 | 4217 | 18 | 4.230 | `usable-structure-candidates` | 0.307162 |
| 4 | 48 | 11503 | 27445 | 223 | 1 | 0.087 | `severe-summary-collapse` | 0.614324 |
| 8 | 96 | 22332 | 51732 | 7301 | 27 | 1.209 | `usable-structure-candidates` | 1.228648 |
| 16 | 192 | 39414 | 91709 | 1446 | 6 | 0.152 | `large-context-under-extraction` | 2.457296 |

Interpretation:

- Long worker timeouts removed the earlier operator-cutoff problem: all four runs completed.
- Worker input tokens scaled with page and word count, but useful candidate-record yield did not scale monotonically.
- The x4 and x16 runs produced valid JSONL but under-extracted badly, which is a model/protocol quality signal rather than an execution failure.
- The strongest immediate guardrail is to avoid single-pass x16-sized document chunks for structure extraction unless the ticket uses a hierarchical map-reduce design, explicit minimum coverage targets, or smaller page windows.
- These records use an extrapolated direct-supervisor baseline and zero audited supervisor cost for the scale sequence, so they are scale-shape evidence, not a final savings claim.

Economics note:

extrapolated from the measured 12-page direct-supervisor baseline; not a paid baseline rerun for this scale series.
Per-run net savings are intentionally marked as unclaimed until supervisor audit and repair costs are added.

Measured supervisor-token cost rollup:

| Span | Supervisor USD |
| --- | ---: |
| `setup` | 0.168713 |
| `ticket_build` | 0.205313 |
| `worker_run_orchestration` | 0.092104 |
| `worker_output_summarize` | 0.165052 |
| `supervisor_audit` | 0.195233 |
| `scale_sequence_run_total` | 0.826415 |

The rollup above is the measured paid-supervisor cost for the first scale-sequence iteration as a whole.
It is not allocated per scale run yet, and it does not include the separate Agent Workbench fixture-implementation cost.
That framework update cost was measured separately at `0.591584` USD.
