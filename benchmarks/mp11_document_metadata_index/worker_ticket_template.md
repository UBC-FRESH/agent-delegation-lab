# Worker Ticket: MP11 Chunk Metadata Index

You are processing one chunk of text exported from a public PDF. Treat the chunk
text and chunk metadata supplied with the ticket as authoritative.

## Task

Extract candidate metadata-index records from this chunk only.

## Authority Boundary

- Do not use tools.
- Do not claim to inspect files or pages outside the supplied chunk.
- Do not invent page numbers, section paths, tables, figures, or titles.
- If a value is uncertain, set `confidence` below `0.6` and explain briefly.

## Output Contract

Return JSONL only. Each line must be one JSON object with these fields:

- `record_id`
- `source_package_id`
- `source_sha256`
- `chunk_id`
- `pdf_page`
- `document_component`
- `section_path`
- `object_type`
- `title`
- `summary`
- `confidence`
- `worker_model`
- `review_status`

Allowed `review_status`: `raw_worker_candidate`.

## Extraction Priorities

Prefer records for:

- section headings;
- tables and table-like title lines;
- figures, maps, and charts;
- appendices and component boundaries;
- key assumptions;
- management constraints;
- model inputs;
- sensitivity-analysis descriptions;
- AAC or harvest-flow claims;
- acronyms, definitions, and glossary-like terms;
- source citations and cross-references.

