"""Build ignored MP11 fixed-x8 bundled worker tickets and eval manifests."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


SOURCE_ID = "tfl6_mp11_202606_public_pdf"
SOURCE_SHA256 = "44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b"
DEFAULT_MANIFEST = "benchmarks/mp11_document_metadata_index/chunk_manifest.json"
DEFAULT_OUTPUT_DIR = "runtime/mp11_document_metadata_index/x8_bundle_sequence_02"
DEFAULT_AGENT_WORKBENCH = "../agent-workbench"
DEFAULT_PYTHON = "../agent-workbench/.venv/Scripts/python.exe"
DEFAULT_TIMEOUT_SECONDS = 7200
MODELS = ["qwen3-coder-next:latest", "gpt-oss:20b"]


@dataclass(frozen=True)
class BundlePart:
    strategy_id: str
    part_id: str
    title: str
    start_page: int
    end_page: int


PARTS = [
    BundlePart("x8-2x48", "part01", "MP11 x8 bundle 2x48 part 1", 46, 93),
    BundlePart("x8-2x48", "part02", "MP11 x8 bundle 2x48 part 2", 94, 141),
    BundlePart("x8-4x24", "part01", "MP11 x8 bundle 4x24 part 1", 46, 69),
    BundlePart("x8-4x24", "part02", "MP11 x8 bundle 4x24 part 2", 70, 93),
    BundlePart("x8-4x24", "part03", "MP11 x8 bundle 4x24 part 3", 94, 117),
    BundlePart("x8-4x24", "part04", "MP11 x8 bundle 4x24 part 4", 118, 141),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--agent-workbench-root", type=Path, default=Path(DEFAULT_AGENT_WORKBENCH))
    parser.add_argument("--python-executable", type=Path, default=Path(DEFAULT_PYTHON))
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    chunks_by_page = {int(chunk["pdf_page"]): chunk for chunk in manifest["chunks"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": 1,
        "series_id": "mp11-document-structure-x8-bundle-sequence-02",
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "fixed_input": {
            "benchmark_id": "mp11-scale-x8",
            "start_page": 46,
            "end_page": 141,
            "page_count": 96,
            "direct_baseline_cost_usd": 1.228648,
            "direct_baseline_cost_source": (
                "same fixed x8 page definition as scale_sequence_01; "
                "extrapolated from the measured 12-page direct-supervisor baseline"
            ),
        },
        "models": MODELS,
        "timeout_seconds": args.timeout_seconds,
        "parts": [],
    }

    for part in PARTS:
        part_dir = args.output_dir / part.strategy_id / part.part_id
        ticket_path = part_dir / f"mp11-{part.strategy_id}-{part.part_id}.ticket.md"
        manifest_path = part_dir / f"mp11-{part.strategy_id}-{part.part_id}.manifest.json"
        output_dir = part_dir / "eval"
        part_dir.mkdir(parents=True, exist_ok=True)
        if not args.force and (ticket_path.exists() or manifest_path.exists()):
            raise SystemExit(f"Refusing to overwrite existing bundle part: {part_dir}")

        chunks = [chunks_by_page[page] for page in range(part.start_page, part.end_page + 1)]
        ticket_path.write_text(render_ticket(part, chunks), encoding="utf-8")
        eval_manifest = {
            "evaluation_id": f"mp11_x8_bundle_{part.strategy_id}_{part.part_id}",
            "ticket": ticket_path.as_posix(),
            "expected_marker": "",
            "required_sections": [],
            "forbidden_phrases": ["I cannot", "I can't", "would do", "would have"],
            "allow_unexpected_sections": True,
            "allow_preamble": True,
            "require_patch": False,
            "allowed_patch_files": [],
            "models": MODELS,
            "repeats": 1,
            "timeout_seconds": args.timeout_seconds,
            "output_dir": output_dir.as_posix(),
            "probe_script": "scripts/copilot_sdk_ollama_probe.py",
            "python_executable": args.python_executable.resolve().as_posix(),
            "base_url": "",
            "base_url_file": (args.agent_workbench_root / "runtime/ollama_openai_base_url.txt")
            .resolve()
            .as_posix(),
            "provider_headers_file": (
                args.agent_workbench_root / "runtime/local_provider_headers.json"
            )
            .resolve()
            .as_posix(),
            "wire_api": "completions",
            "mode": "empty",
            "base_directory": (part_dir / "copilot_sdk_home").as_posix(),
            "sdk_source": "",
        }
        manifest_path.write_text(json.dumps(eval_manifest, indent=2) + "\n", encoding="utf-8")
        index["parts"].append(
            {
                "strategy_id": part.strategy_id,
                "part_id": part.part_id,
                "task_id": f"mp11-{part.strategy_id}-{part.part_id}",
                "title": part.title,
                "start_page": part.start_page,
                "end_page": part.end_page,
                "page_count": len(chunks),
                "ticket": ticket_path.as_posix(),
                "manifest": manifest_path.as_posix(),
                "output_dir": output_dir.as_posix(),
                "word_count": sum(int(chunk["word_count"]) for chunk in chunks),
                "char_count": sum(int(chunk["char_count"]) for chunk in chunks),
            }
        )
    index_path = args.output_dir / "x8_bundle_sequence_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {index_path}")


def render_ticket(part: BundlePart, chunks: list[dict[str, object]]) -> str:
    chunk_text_blocks = []
    for chunk in chunks:
        path = Path(str(chunk["runtime_text_path"]))
        text = path.read_text(encoding="utf-8")
        chunk_text_blocks.append(
            "\n".join(
                [
                    f"### Chunk {chunk['chunk_id']}",
                    "",
                    f"- pdf_page: {chunk['pdf_page']}",
                    f"- document_component: {chunk['component']}",
                    f"- text_sha256: {chunk['text_sha256']}",
                    "",
                    "```text",
                    text.rstrip(),
                    "```",
                    "",
                ]
            )
        )

    task_id = f"mp11-{part.strategy_id}-{part.part_id}"
    min_records = max(8, len(chunks) // 2)
    return "\n".join(
        [
            f"# MP11 Fixed-X8 Bundle Ticket: {part.title}",
            "",
            "You are processing one bounded page-window from a fixed 96-page benchmark input.",
            "Use only the chunk text supplied in this ticket.",
            "",
            "## Task",
            "",
            "Infer candidate document-structure records from these chunks only.",
            "Return JSONL only. Do not include Markdown, commentary, summaries, or code fences.",
            "Aim for useful coverage across the whole page window instead of a short global summary.",
            f"Unless the text is genuinely structure-poor, produce at least {min_records} records.",
            "",
            "Each JSON object must have these fields:",
            "",
            "- record_id",
            "- source_package_id",
            "- source_sha256",
            "- bundle_id",
            "- chunk_id",
            "- pdf_page",
            "- document_component",
            "- section_path",
            "- object_type",
            "- title",
            "- summary",
            "- confidence",
            "- worker_model",
            "- review_status",
            "",
            "Use these exact constants:",
            "",
            f"- source_package_id: {SOURCE_ID}",
            f"- source_sha256: {SOURCE_SHA256}",
            f"- bundle_id: {task_id}",
            "- review_status: raw_worker_candidate",
            "",
            "Set worker_model to the model identifier used for this run.",
            "",
            "Allowed object_type values:",
            "",
            "- component_boundary",
            "- heading",
            "- table",
            "- figure",
            "- map",
            "- appendix",
            "- acronym",
            "- definition",
            "- cross_reference",
            "- assumption",
            "- claim",
            "- other",
            "",
            "Extraction priorities:",
            "",
            "- component and appendix boundaries",
            "- numbered section headings and section hierarchy",
            "- table, figure, map, chart, and appendix labels",
            "- model assumptions, constraints, sensitivity descriptions, and AAC or harvest-flow claims",
            "- source citations and cross-references",
            "- acronyms only when the source explicitly defines the term or the term is central to interpretation",
            "",
            "Rules:",
            "",
            "- Do not invent pages, headings, labels, acronyms, section paths, or definitions.",
            "- If section hierarchy is unclear, use the best local section path and set confidence below 0.6.",
            "- Use one JSON object per record.",
            "- If a chunk has no useful structure, output no record for that chunk.",
            "- Stop after the JSONL records.",
            "",
            "## Bundle Metadata",
            "",
            f"- fixed_benchmark_id: mp11-scale-x8",
            f"- strategy_id: {part.strategy_id}",
            f"- part_id: {part.part_id}",
            f"- bundle_id: {task_id}",
            f"- page_range: {part.start_page}-{part.end_page}",
            f"- chunk_count: {len(chunks)}",
            f"- total_words: {sum(int(chunk['word_count']) for chunk in chunks)}",
            f"- total_characters: {sum(int(chunk['char_count']) for chunk in chunks)}",
            "",
            "## Chunks",
            "",
            *chunk_text_blocks,
        ]
    )


if __name__ == "__main__":
    main()
