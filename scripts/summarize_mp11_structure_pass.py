"""Summarize ignored MP11 structure-pass worker outputs into tracked evidence."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_ID = "tfl6_mp11_202606_public_pdf"
SOURCE_SHA256 = "44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b"
INPUT_DIR = Path("runtime/mp11_document_metadata_index/structure_pass")
OUTPUT_JSON = Path("benchmarks/mp11_document_metadata_index/structure_pass_summary.json")
OUTPUT_MD = Path("planning/phase1_mp11_structure_pass_iteration.md")


def main() -> None:
    bundle_summaries = []
    totals = Counter()
    token_totals = Counter()
    model_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for summary_path in sorted(INPUT_DIR.glob("*/eval/summary.json")):
        bundle_summary = summarize_bundle(summary_path)
        bundle_summaries.append(bundle_summary)
        for run in bundle_summary["runs"]:
            totals["runs"] += 1
            model_counts[run["model"]][run["outcome"]] += 1
            if run["status"] == "completed":
                totals["completed_runs"] += 1
            if run["outcome"] == "timeout":
                totals["timeouts"] += 1
            totals["records"] += run["record_count"]
            totals["format_issue_runs"] += 1 if run["format_issue"] else 0
            totals["wrong_worker_model_labels"] += run["wrong_worker_model_labels"]
            token_totals["input_tokens"] += run["input_tokens"] or 0
            token_totals["output_tokens"] += run["output_tokens"] or 0

    summary = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "benchmark": "mp11_structure_pass_ab_iteration_1",
        "run_count": totals["runs"],
        "completed_run_count": totals["completed_runs"],
        "timeout_count": totals["timeouts"],
        "candidate_record_count": totals["records"],
        "format_issue_run_count": totals["format_issue_runs"],
        "wrong_worker_model_label_count": totals["wrong_worker_model_labels"],
        "observed_worker_tokens": {
            "input_tokens": token_totals["input_tokens"],
            "output_tokens": token_totals["output_tokens"],
            "cash_cost": 0,
            "note": "Local Ollama worker tokens only; supervisor-token accounting not included.",
        },
        "model_outcomes": {model: dict(counts) for model, counts in model_counts.items()},
        "bundles": bundle_summaries,
        "supervisor_spot_check": {
            "status": "sample_grounded_with_caveats",
            "samples_checked": [
                {
                    "bundle_id": "appendix-a-opening-structure",
                    "page": 46,
                    "result": "component boundary matched the Appendix A title-page chunk",
                },
                {
                    "bundle_id": "appendix-a-late-structure",
                    "page": 180,
                    "result": "table and ROPE-test figure records matched the page text",
                },
                {
                    "bundle_id": "appendix-b-opening-structure",
                    "page": 247,
                    "result": "section 1 and section 1.1 heading records matched the page text",
                },
            ],
            "caveats": [
                "qwen3-coder:latest timed out on every tested bundle",
                "qwen3-coder-next:latest timed out on the main plan bundle",
                "one qwen3-coder-next run filled worker_model with gpt-4o-mini",
                "one qwen3-coder-next record had a malformed source_sha256",
                "qwen3-coder-next sometimes returned a JSON array instead of JSONL",
            ],
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON}")
    print(f"wrote {OUTPUT_MD}")


def summarize_bundle(summary_path: Path) -> dict[str, Any]:
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    bundle_id = summary_path.parents[1].name
    runs = []
    for row in data["rows"]:
        raw_path = Path(row["result_file"])
        raw_text = raw_path.read_text(encoding="utf-8-sig") if raw_path.exists() else ""
        records, parse_error, output_shape = parse_records(row["assistant_message"])
        type_counts = Counter(str(record.get("object_type", "<missing>")) for record in records)
        pages = [
            int(record["pdf_page"])
            for record in records
            if isinstance(record.get("pdf_page"), int)
        ]
        wrong_worker_model = sum(
            1 for record in records if record.get("worker_model") != row["model"]
        )
        malformed_source = sum(
            1 for record in records if record.get("source_sha256") != SOURCE_SHA256
        )
        duplicate_record_ids = duplicate_count(
            str(record.get("record_id", "")) for record in records
        )
        input_tokens, output_tokens = usage_tokens(raw_text)
        outcome = classify_run(row, records, parse_error)
        format_issue = bool(parse_error and row["status"] == "completed")
        if output_shape == "json_array":
            format_issue = True
        if wrong_worker_model or malformed_source or duplicate_record_ids:
            format_issue = True
        runs.append(
            {
                "model": row["model"],
                "status": row["status"],
                "blocker": row["blocker"],
                "outcome": outcome,
                "record_count": len(records),
                "object_type_counts": dict(sorted(type_counts.items())),
                "page_min": min(pages) if pages else None,
                "page_max": max(pages) if pages else None,
                "parse_error": parse_error,
                "format_issue": format_issue,
                "output_shape": output_shape,
                "wrong_worker_model_labels": wrong_worker_model,
                "malformed_source_sha256_records": malformed_source,
                "duplicate_record_id_count": duplicate_record_ids,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
    return {"bundle_id": bundle_id, "runs": runs}


def parse_records(message: str) -> tuple[list[dict[str, Any]], str, str]:
    text = message.strip()
    if not text or text == "_No assistant messages captured._":
        return [], "no assistant message", "none"
    if text.startswith("["):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            return [], f"json array parse error: {exc.msg}", "json_array_invalid"
        if not isinstance(value, list):
            return [], "json array root was not a list", "json_array_invalid"
        return [record for record in value if isinstance(record, dict)], "", "json_array"

    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line.rstrip(","))
        except json.JSONDecodeError as exc:
            return records, f"jsonl parse error: {exc.msg}", "jsonl_invalid"
        if isinstance(value, dict):
            records.append(value)
    return records, "", "jsonl"


def usage_tokens(text: str) -> tuple[int | None, int | None]:
    input_values = re.findall(r'"input_tokens"\s*:\s*(\d+)', text)
    output_values = re.findall(r'"output_tokens"\s*:\s*(\d+)', text)
    input_tokens = int(input_values[-1]) if input_values else None
    output_tokens = int(output_values[-1]) if output_values else None
    return input_tokens, output_tokens


def duplicate_count(values: Any) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def classify_run(row: dict[str, Any], records: list[dict[str, Any]], parse_error: str) -> str:
    if row["blocker"] == "session-idle-timeout":
        return "timeout"
    if row["status"] != "completed":
        return row["blocker"] or "blocked"
    if parse_error:
        return "completed-unparseable"
    if records:
        return "completed-parseable"
    return "completed-empty"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 MP11 Structure-Pass Iteration",
        "",
        "This checkpoint records the first model-backed structure-pass A/B run for",
        "the MP11 document metadata-indexing benchmark.",
        "",
        "## Result",
        "",
        f"- run count: `{summary['run_count']}`",
        f"- completed runs: `{summary['completed_run_count']}`",
        f"- timeouts: `{summary['timeout_count']}`",
        f"- candidate records parsed: `{summary['candidate_record_count']}`",
        f"- format-issue runs: `{summary['format_issue_run_count']}`",
        f"- wrong worker-model labels: `{summary['wrong_worker_model_label_count']}`",
        "- observed local-worker tokens: "
        f"`{summary['observed_worker_tokens']['input_tokens']}` input, "
        f"`{summary['observed_worker_tokens']['output_tokens']}` output, cash cost `0`",
        "",
        "## Model Outcomes",
        "",
        "| Model | Outcome | Count |",
        "| --- | --- | ---: |",
    ]
    for model, outcomes in summary["model_outcomes"].items():
        for outcome, count in sorted(outcomes.items()):
            lines.append(f"| `{model}` | `{outcome}` | {count} |")

    lines.extend(
        [
            "",
            "## Bundle Summary",
            "",
            "| Bundle | Model | Outcome | Records | Page Span | Input Tokens | Output Tokens | Caveats |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    for bundle in summary["bundles"]:
        for run in bundle["runs"]:
            caveats = []
            if run["parse_error"]:
                caveats.append(run["parse_error"])
            if run["wrong_worker_model_labels"]:
                caveats.append(f"{run['wrong_worker_model_labels']} wrong worker_model labels")
            if run["malformed_source_sha256_records"]:
                caveats.append(f"{run['malformed_source_sha256_records']} malformed source SHA records")
            if run["duplicate_record_id_count"]:
                caveats.append(f"{run['duplicate_record_id_count']} duplicate record ids")
            page_span = (
                f"{run['page_min']}-{run['page_max']}"
                if run["page_min"] is not None and run["page_max"] is not None
                else ""
            )
            lines.append(
                "| "
                f"`{bundle['bundle_id']}` | "
                f"`{run['model']}` | "
                f"`{run['outcome']}` | "
                f"{run['record_count']} | "
                f"`{page_span}` | "
                f"{run['input_tokens'] or 0} | "
                f"{run['output_tokens'] or 0} | "
                f"{'; '.join(caveats)} |"
            )

    lines.extend(
        [
            "",
            "## Supervisor Spot Check",
            "",
            "Sampled records were checked against ignored source chunks for Appendix A",
            "opening, Appendix A late, and Appendix B opening pages. The checked records",
            "were grounded in the supplied text, but the run is not clean enough to",
            "promote without a stricter second-pass ticket.",
            "",
            "## Interpretation",
            "",
            "`qwen3-coder-next:latest` is the only useful candidate from this run. It",
            "returned parseable records for three of four bundles and consumed large",
            "zero-cash local-worker token volumes. `qwen3-coder:latest` timed out on",
            "all four bundles and should not be used for this task shape without much",
            "smaller tickets or a different timeout strategy.",
            "",
            "The next iteration should split tickets more finely, require strict JSONL",
            "again, and add automated validation for constants, worker_model, duplicate",
            "record IDs, source SHA, and object_type values before any index records are",
            "accepted.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
