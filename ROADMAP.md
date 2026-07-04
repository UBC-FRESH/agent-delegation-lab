# Roadmap

This roadmap tracks synthetic and real-document delegation benchmarks.

## Issue Map

| Phase | Title | Issue | Branch | Status |
| --- | --- | --- | --- | --- |
| P0 | Repository scaffold and benchmark boundaries | #1 | `main` | Complete |
| P1 | MP11 document metadata indexing benchmark | #2 | `feature/p1-mp11-document-index` | Active |

## Phase 0: Repository Scaffold And Benchmark Boundaries

Status: complete.

Goal: create a public-safe benchmark lab for delegated agent experiments.

Tasks:

- [x] Add repository purpose and public-safety boundary.
- [x] Add agent operating contract.
- [x] Add roadmap and changelog.
- [x] Add ignore rules for raw source documents, extracted text, runtime
      outputs, transcripts, and credentials.
- [x] Add the first benchmark plan around MP11 document metadata indexing.

## Phase 1: MP11 Document Metadata Indexing Benchmark

Status: active.

Goal: test whether local Ollama worker agents can grind through a long,
complex PDF-derived text corpus and produce a useful structured metadata index
at much lower paid-supervisor token cost.

Target source:

- document: `Tree Farm Licence 6 Management Plan 11`
- source package ID: `tfl6_mp11_202606_public_pdf`
- pages: `475`
- byte size: `9147004`
- SHA256: `44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b`

Planned tasks:

- [ ] P1.1 Source registration and extraction boundary
  - [x] Record public source metadata and local source hints.
  - [x] Keep PDF and extracted text untracked.
- [ ] P1.2 Chunked text export and manifest
  - [x] Export PDF text into page chunks under ignored runtime paths.
  - [x] Create a tracked sanitized chunk-manifest contract.
- [ ] P1.3 Worker structure pass
  - [ ] Ask local workers to infer document structure from chunks.
  - [ ] Produce candidate component, section, table, figure, and appendix maps.
- [ ] P1.4 Worker metadata extraction pass
  - [ ] Extract page-anchored metadata index records from chunks.
  - [ ] Emit JSONL or CSV candidate rows under ignored runtime paths.
- [ ] P1.5 Supervisor audit and economics comparison
  - [ ] Sample worker output against source text and existing FEMIC evidence.
  - [ ] Record worker token counts, supervisor audit cost, failure modes, and
        whether the delegation shape looks profitable.

Acceptance criteria:

- Worker tasks are chunked and repeatable.
- Raw source text is not tracked.
- Metadata index rows preserve page/component/source provenance.
- Supervisor can audit a sample without rereading the full 475-page document.
- Benchmark conclusion distinguishes output usefulness from token economics.
