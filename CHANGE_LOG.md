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
