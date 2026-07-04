# Delegation Experiment Synthesis

This report summarizes sanitized delegation experiment observations.
Raw inputs, outputs, traces, provider URLs, headers, and personal paths
are excluded by contract.

## Summary

- records: 4

## Observation Table

| Record | Series | Task | Scale | Model | Status | Worker In | Worker Out | Supervisor USD | Direct USD | Net USD | BCR |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| mp11-x8-bundle-x8-2x48-gpt_oss_20b-run01 | mp11-document-structure-x8-bundle-sequence-02 | mp11-x8-bundle-x8-2x48 | 8 | gpt-oss:20b | completed-with-parse-errors | 51870 | 19848 | 0.000000 | 1.228648 | 1.228648 | `undefined-no-audited-delegated-cost` |
| mp11-x8-bundle-x8-2x48-qwen3_coder_next_latest-run01 | mp11-document-structure-x8-bundle-sequence-02 | mp11-x8-bundle-x8-2x48 | 8 | qwen3-coder-next:latest | completed-parseable | 54317 | 19547 | 0.000000 | 1.228648 | 1.228648 | `undefined-no-audited-delegated-cost` |
| mp11-x8-bundle-x8-4x24-gpt_oss_20b-run01 | mp11-document-structure-x8-bundle-sequence-02 | mp11-x8-bundle-x8-4x24 | 8 | gpt-oss:20b | completed-parseable | 60362 | 19996 | 0.000000 | 1.228648 | 1.228648 | `undefined-no-audited-delegated-cost` |
| mp11-x8-bundle-x8-4x24-qwen3_coder_next_latest-run01 | mp11-document-structure-x8-bundle-sequence-02 | mp11-x8-bundle-x8-4x24 | 8 | qwen3-coder-next:latest | completed-with-salvageable-model-failures | 59319 | 16313 | 0.000000 | 1.228648 | 1.228648 | `undefined-no-audited-delegated-cost` |
