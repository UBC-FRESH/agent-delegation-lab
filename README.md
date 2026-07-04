# Agent Delegation Lab

This repository is a public-safe sandbox for testing high-volume, low-cash-cost
agent delegation tasks.

The goal is to find task shapes where a local worker model can grind through
large inputs and produce structured intermediate artifacts while a paid
supervisor agent spends fewer tokens on orchestration, review, and final
decision-making.

## Benchmark Strategy

Good benchmark tasks should be:

- input-heavy;
- chunkable;
- evidence-oriented;
- easy to validate by sampling;
- tolerant of imperfect but useful worker output; and
- expensive for a paid supervisor to do directly.

Poor first targets include broad API design, ambiguous architecture decisions,
and tasks where most value comes from high-level judgement rather than
high-volume extraction.

## First Benchmark

The first planned benchmark is MP11 document metadata indexing:

- source document: `Tree Farm Licence 6 Management Plan 11`
- source package ID: `tfl6_mp11_202606_public_pdf`
- page count: `475`
- byte size: `9147004`
- SHA256: `44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b`

Raw PDFs, extracted text, worker transcripts, and provider configuration belong
under ignored local paths. The tracked repo records benchmark plans, task
contracts, schemas, acceptance criteria, and sanitized summaries only.

