"""Export MP11 PDF page text chunks and a sanitized tracked manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "tfl6_mp11_202606_public_pdf"
SOURCE_TITLE = "Tree Farm Licence 6 Management Plan 11"
SOURCE_URL = (
    "https://www.westernforest.com/wp-content/uploads/2026/06/"
    "TFL6_MP_11_202606_w_Appendices_Web-compressed.pdf"
)
EXPECTED_SHA256 = "44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b"
EXPECTED_BYTE_SIZE = 9_147_004
EXPECTED_PAGE_COUNT = 475

DEFAULT_SOURCE_HINT = (
    "../femic/external/femic-tfl6-instance/runtime/mp11/source/"
    "TFL6_MP_11_202606_w_Appendices_Web-compressed.pdf"
)
DEFAULT_OUTPUT_DIR = "runtime/mp11_document_metadata_index/chunks"
DEFAULT_MANIFEST = "benchmarks/mp11_document_metadata_index/chunk_manifest.json"

COMPONENTS = [
    ("management_plan_main", 1, 44),
    ("appendix_a_divider", 45, 45),
    ("appendix_a_timber_supply_analysis", 46, 226),
    ("appendix_a_trailing_blank", 227, 227),
    ("appendix_b_divider", 228, 228),
    ("appendix_b_acceptance_letter", 229, 229),
    ("appendix_b_information_package", 230, 475),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def component_for_page(page_number: int) -> str:
    for name, start, end in COMPONENTS:
        if start <= page_number <= end:
            return name
    return "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-path", default=DEFAULT_SOURCE_HINT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    output_dir = Path(args.output_dir)
    manifest_path = Path(args.manifest)

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required: python -m pip install pymupdf") from exc

    byte_size = pdf_path.stat().st_size
    source_sha256 = sha256_file(pdf_path)
    if byte_size != EXPECTED_BYTE_SIZE:
        raise SystemExit(f"Unexpected byte size: {byte_size}")
    if source_sha256 != EXPECTED_SHA256:
        raise SystemExit(f"Unexpected SHA256: {source_sha256}")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    if document.page_count != EXPECTED_PAGE_COUNT:
        raise SystemExit(f"Unexpected page count: {document.page_count}")

    chunks = []
    for page_index in range(document.page_count):
        page_number = page_index + 1
        text = document.load_page(page_index).get_text("text")
        chunk_id = f"mp11_page_{page_number:04d}"
        chunk_path = output_dir / f"{chunk_id}.txt"
        chunk_path.write_text(text, encoding="utf-8")

        lines = text.splitlines()
        words = text.split()
        chunks.append(
            {
                "chunk_id": chunk_id,
                "pdf_page": page_number,
                "component": component_for_page(page_number),
                "runtime_text_path": chunk_path.as_posix(),
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "char_count": len(text),
                "word_count": len(words),
                "line_count": len(lines),
                "is_empty": not text.strip(),
            }
        )

    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "source_id": SOURCE_ID,
            "title": SOURCE_TITLE,
            "source_url": SOURCE_URL,
            "source_pdf_filename": pdf_path.name,
            "source_path_hint": DEFAULT_SOURCE_HINT,
            "source_path_recorded": False,
            "byte_size": byte_size,
            "sha256": source_sha256,
            "page_count": document.page_count,
        },
        "component_ranges": [
            {"component": name, "start_page": start, "end_page": end}
            for name, start, end in COMPONENTS
        ],
        "runtime_output": {
            "raw_text_tracked": False,
            "chunk_path_pattern": f"{output_dir.as_posix()}/mp11_page_####.txt",
        },
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {output_dir}")
    print(f"Wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
