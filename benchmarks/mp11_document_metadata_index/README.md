# MP11 Document Metadata Index Benchmark

This benchmark tests a grind-heavy delegation target: compiling a detailed
metadata index from a long public planning PDF.

## Source

- source package ID: `tfl6_mp11_202606_public_pdf`
- document title: `Tree Farm Licence 6 Management Plan 11`
- version/date: `Version 1, June 2026`
- publisher: `Western Forest Products Inc.`
- source URL:
  `https://www.westernforest.com/wp-content/uploads/2026/06/TFL6_MP_11_202606_w_Appendices_Web-compressed.pdf`
- byte size: `9147004`
- page count: `475`
- SHA256: `44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b`

## Local Source Hints

Do not commit the PDF or extracted text to this repository.

When the FEMIC TFL6 instance is available as a sibling checkout, the source PDF
is expected at:

`../femic/external/femic-tfl6-instance/runtime/mp11/source/TFL6_MP_11_202606_w_Appendices_Web-compressed.pdf`

Existing FEMIC reference surfaces that can be used for supervisor audit, not as
worker input unless explicitly allowed:

- `planning/tfl6_mp11_source_package_manifest.md`
- `planning/tfl6_mp11_document_components.csv`
- `planning/tfl6_mp11_extraction_inventory.csv`
- `planning/tfl6_mp11_extraction_inventory_summary.md`

## Why This Is A Good Delegation Target

This task is likely dominated by high-volume input reading and structured output
generation. That is exactly where local zero-cash worker models may be useful,
even if their output needs sample-based supervisor audit.

The supervisor should not spend paid tokens reading the whole PDF directly.
The supervisor should define schemas, launch worker passes, audit samples, and
decide whether the resulting index is useful.

## Proposed Output

The final candidate index should be a structured table or JSONL stream with
records such as:

- document component;
- PDF page;
- printed page label, if available;
- section path;
- object type: heading, table, figure, map, appendix, glossary item, claim,
  assumption, sensitivity, acronym, citation, or cross-reference;
- title or label;
- concise summary;
- extraction confidence;
- source chunk ID;
- worker model;
- review status.

Raw records should remain under ignored runtime paths until sanitized and
reviewed.

## Chunk Manifest

The first tracked manifest is:

`benchmarks/mp11_document_metadata_index/chunk_manifest.json`

It records sanitized page-level extraction metadata only. The raw extracted page
text stays ignored under:

`runtime/mp11_document_metadata_index/chunks/`

Current manifest facts:

- chunks: `475`
- extracted words: `105811`
- extracted characters: `723498`
- effectively empty pages: `3`
- source PDF SHA256:
  `44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b`

This is the first useful delegation substrate: workers can receive selected
chunks or chunk bundles, while the supervisor can audit against stable page IDs,
component ranges, text hashes, and runtime paths without committing raw source
text.

## Structure-Pass Iteration 1

The first worker-backed structure pass is summarized in:

`benchmarks/mp11_document_metadata_index/structure_pass_summary.json`

The companion planning note is:

`planning/phase1_mp11_structure_pass_iteration.md`

This iteration ran four bounded page bundles against `qwen3-coder:latest` and
`qwen3-coder-next:latest`. The tracked summary records aggregate outcomes,
token counts, and validation caveats only. Raw tickets, raw worker outputs, SDK
events, provider details, and extracted text remain ignored under `runtime/`.
