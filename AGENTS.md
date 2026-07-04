# Agent Contract

This repository exists to test agent delegation workflows. Agents must keep the
lab public-safe and evidence-driven.

## Operating Rules

- Do not commit raw PDFs, raw extracted text, raw transcripts, provider URLs,
  headers, credentials, or personal workstation paths.
- Keep large source documents and generated outputs under ignored `runtime/`,
  `tmp/`, `data/`, `outputs/`, or `local/` paths.
- Treat worker outputs as candidate evidence, not truth.
- Prefer chunked worker tasks with explicit schemas and stop conditions.
- Record exact commands, model IDs, token counts, validation results, and known
  limitations in sanitized benchmark notes.
- Separate worker authority from supervisor authority:
  - workers may extract, summarize, classify, and propose;
  - supervisors validate, merge, close issues, publish, and decide whether a
    benchmark result is useful.

## Useful Task Shapes

Prioritize tasks where the local worker can absorb a large amount of input:

- document metadata indexing;
- table, figure, heading, and glossary inventories;
- claim and assumption candidate extraction;
- citation and source-anchor mapping;
- repeated chunk classification;
- consistency checks across independently generated summaries.

Avoid making weak worker models do broad-context architecture planning as a
first benchmark. That is not where delegation economics are likely to win.

