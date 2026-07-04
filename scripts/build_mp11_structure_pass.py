"""Build ignored MP11 structure-pass worker tickets and eval manifests."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


SOURCE_ID = "tfl6_mp11_202606_public_pdf"
SOURCE_SHA256 = "44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b"
DEFAULT_MANIFEST = "benchmarks/mp11_document_metadata_index/chunk_manifest.json"
DEFAULT_OUTPUT_DIR = "runtime/mp11_document_metadata_index/structure_pass"
DEFAULT_AGENT_WORKBENCH = "../agent-workbench"
DEFAULT_PYTHON = "../agent-workbench/.venv/Scripts/python.exe"
MODELS = ["qwen3-coder:latest", "qwen3-coder-next:latest"]


@dataclass(frozen=True)
class Bundle:
    task_id: str
    title: str
    start_page: int
    end_page: int


BUNDLES = [
    Bundle("main-plan-structure", "Main management plan structure", 1, 44),
    Bundle("appendix-a-opening-structure", "Appendix A opening structure", 46, 80),
    Bundle("appendix-a-late-structure", "Appendix A late structure", 180, 226),
    Bundle("appendix-b-opening-structure", "Appendix B opening structure", 230, 275),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--agent-workbench-root", type=Path, default=Path(DEFAULT_AGENT_WORKBENCH))
    parser.add_argument("--python-executable", type=Path, default=Path(DEFAULT_PYTHON))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    chunks_by_page = {int(chunk["pdf_page"]): chunk for chunk in manifest["chunks"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    index = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "models": MODELS,
        "bundles": [],
    }

    for bundle in BUNDLES:
        bundle_dir = args.output_dir / bundle.task_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        ticket_path = bundle_dir / f"{bundle.task_id}.ticket.md"
        manifest_path = bundle_dir / f"{bundle.task_id}.manifest.json"
        output_dir = bundle_dir / "eval"

        if not args.force and (ticket_path.exists() or manifest_path.exists()):
            raise SystemExit(f"Refusing to overwrite existing bundle: {bundle.task_id}")

        chunks = [chunks_by_page[page] for page in range(bundle.start_page, bundle.end_page + 1)]
        ticket_path.write_text(render_ticket(bundle, chunks), encoding="utf-8")

        eval_manifest = {
            "evaluation_id": f"mp11_structure_pass_{bundle.task_id}",
            "ticket": ticket_path.as_posix(),
            "expected_marker": "",
            "required_sections": [],
            "forbidden_phrases": [
                "I cannot",
                "I can't",
                "would do",
                "would have",
                "ready for",
            ],
            "allow_unexpected_sections": True,
            "allow_preamble": True,
            "require_patch": False,
            "allowed_patch_files": [],
            "models": MODELS,
            "repeats": 1,
            "timeout_seconds": 360,
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
            "base_directory": (bundle_dir / "copilot_sdk_home").as_posix(),
            "sdk_source": "",
        }
        manifest_path.write_text(json.dumps(eval_manifest, indent=2) + "\n", encoding="utf-8")

        index["bundles"].append(
            {
                "task_id": bundle.task_id,
                "title": bundle.title,
                "start_page": bundle.start_page,
                "end_page": bundle.end_page,
                "page_count": len(chunks),
                "ticket": ticket_path.as_posix(),
                "manifest": manifest_path.as_posix(),
                "output_dir": output_dir.as_posix(),
                "word_count": sum(int(chunk["word_count"]) for chunk in chunks),
                "char_count": sum(int(chunk["char_count"]) for chunk in chunks),
            }
        )

    index_path = args.output_dir / "structure_pass_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {index_path}")


def render_ticket(bundle: Bundle, chunks: list[dict[str, object]]) -> str:
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

    return "\n".join(
        [
            f"# MP11 Structure Pass Ticket: {bundle.title}",
            "",
            "You are processing exported text chunks from one public PDF.",
            "Use only the chunk text supplied in this ticket.",
            "",
            "## Task",
            "",
            "Infer candidate document-structure records from these chunks only.",
            "Return JSONL only. Do not include Markdown, commentary, summaries, or code fences.",
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
            f"- bundle_id: {bundle.task_id}",
            "- review_status: raw_worker_candidate",
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
            "- acronyms, definitions, and glossary-like terms",
            "- source citations and cross-references",
            "- model assumptions, constraints, sensitivity descriptions, and AAC or harvest-flow claims",
            "",
            "Rules:",
            "",
            "- Do not invent pages, headings, labels, or section paths.",
            "- If section hierarchy is unclear, use the best local section path and set confidence below 0.6.",
            "- Use one JSON object per record.",
            "- If a chunk has no useful structure, output no record for that chunk.",
            "- Stop after the JSONL records.",
            "",
            "## Bundle Metadata",
            "",
            f"- bundle_id: {bundle.task_id}",
            f"- page_range: {bundle.start_page}-{bundle.end_page}",
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
