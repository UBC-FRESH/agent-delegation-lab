"""Summarize ignored MP11 scale-sequence outputs into experiment records."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SOURCE_SHA256 = "44591c1024254e36d8989df45a2b489a624d5669c5ae01a6ebfd961b50a7321b"
INPUT_DIR = Path("runtime/mp11_document_metadata_index/scale_sequence_01")
OUTPUT_DIR = Path("benchmarks/mp11_document_metadata_index/scale_sequence_01")
SUMMARY_JSON = OUTPUT_DIR / "summary.json"
SUMMARY_MD = Path("planning/phase1_mp11_scale_sequence_01.md")
DIRECT_BASELINE_COST_PER_PAGE_USD = 0.153581 / 12
DIRECT_BASELINE_SOURCE = (
    "extrapolated from the measured 12-page direct-supervisor baseline; "
    "not a paid baseline rerun for this scale series"
)
SUPERVISOR_SPAN_COSTS_USD = {
    "setup": 0.168713,
    "ticket_build": 0.205313,
    "worker_run_orchestration": 0.092104,
    "worker_output_summarize": 0.165052,
    "supervisor_audit": 0.195233,
}
FRAMEWORK_UPDATE_COST_USD = 0.591584


def main() -> None:
    index = json.loads((INPUT_DIR / "scale_sequence_index.json").read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for run in index["runs"]:
        record = summarize_run(index, run)
        records.append(record)
        record_path = OUTPUT_DIR / f"{run['task_id']}.experiment.json"
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    summary = {
        "schema_version": 1,
        "series_id": index["series_id"],
        "generated_utc": now_utc(),
        "records": records,
        "supervisor_accounting": supervisor_accounting(),
        "interpretation": interpret(records),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(f"wrote {SUMMARY_JSON}")
    print(f"wrote {SUMMARY_MD}")


def summarize_run(index: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    eval_summary_path = Path(run["output_dir"]) / "summary.json"
    eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
    row = eval_summary["rows"][0]
    raw_path = Path(row["result_file"])
    raw_text = raw_path.read_text(encoding="utf-8-sig") if raw_path.exists() else ""
    records, parse_error, output_shape = parse_records(row["assistant_message"])
    type_counts = Counter(str(record.get("object_type", "<missing>")) for record in records)
    input_tokens, output_tokens = usage_tokens(raw_text)
    direct_baseline = round(DIRECT_BASELINE_COST_PER_PAGE_USD * int(run["page_count"]), 6)
    supervisor_cost = 0.0
    status = classify(row, records, parse_error)
    metrics = derived_metrics(
        records=len(records),
        worker_input_tokens=input_tokens or 0,
        worker_output_tokens=output_tokens or 0,
        words=int(run["word_count"]),
        pages=int(run["page_count"]),
    )
    return {
        "record_id": f"{run['task_id']}-qwen3-coder-next-run01",
        "schema_version": 1,
        "generated_utc": now_utc(),
        "experiment": {
            "experiment_id": f"{run['task_id']}-run01",
            "series_id": index["series_id"],
            "project": "agent-delegation-lab",
            "phase": "p1",
        },
        "task": {
            "task_id": run["task_id"],
            "task_family": "long-document-structure-pass",
            "scale_factor": run["scale_factor"],
            "input_pages": run["page_count"],
            "input_words": run["word_count"],
            "input_characters": run["char_count"],
        },
        "model": {
            "model_id": index["model"],
            "provider": "local-ollama",
            "cash_cost_per_token_usd": 0,
        },
        "protocol": {
            "authority_level": "L0",
            "timeout_seconds": index["timeout_seconds"],
            "audit_strategy": "not-yet-audited",
            "ticket_template": "mp11-structure-scale-jsonl",
        },
        "outcome": {
            "status": status,
            "records_produced": len(records),
            "accepted_records": 0,
            "repairable_records": 0,
            "rejected_records": 0,
            "needs_review_records": len(records),
            "object_type_counts": dict(sorted(type_counts.items())),
            "output_shape": output_shape,
            "parse_error": parse_error,
            "scale_behavior": scale_behavior(run["scale_factor"], len(records)),
        },
        "economics": {
            "economics_status": "worker-only-scale-signal",
            "worker_input_tokens": input_tokens or 0,
            "worker_output_tokens": output_tokens or 0,
            "worker_cost_usd": 0,
            "supervisor_cost_usd": supervisor_cost,
            "direct_baseline_cost_usd": direct_baseline,
            "direct_baseline_cost_source": DIRECT_BASELINE_SOURCE,
            "net_savings_usd": direct_baseline - supervisor_cost,
            "net_savings_status": "not-claimed-until-supervisor-audit-cost-is-added",
            "derived_metrics": metrics,
        },
        "links": {
            "runtime_eval_summary": str(eval_summary_path),
            "runtime_result_file": str(raw_path),
            "source_summary": str(SUMMARY_JSON),
        },
        "public_safety": {
            "raw_inputs_excluded": True,
            "raw_outputs_excluded": True,
            "raw_traces_excluded": True,
            "provider_urls_excluded": True,
            "headers_excluded": True,
            "personal_paths_excluded": True,
        },
    }


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


def classify(row: dict[str, Any], records: list[dict[str, Any]], parse_error: str) -> str:
    if row["status"] != "completed":
        return row["blocker"] or "blocked"
    if parse_error:
        return "completed-unparseable"
    if records:
        return "completed-parseable"
    return "completed-empty"


def derived_metrics(
    *, records: int, worker_input_tokens: int, worker_output_tokens: int, words: int, pages: int
) -> dict[str, float]:
    return {
        "records_per_1000_worker_input_tokens": safe_rate(records, worker_input_tokens, 1000),
        "records_per_1000_words": safe_rate(records, words, 1000),
        "worker_input_tokens_per_word": safe_rate(worker_input_tokens, words, 1),
        "worker_output_tokens_per_record": safe_rate(worker_output_tokens, records, 1),
        "records_per_page": safe_rate(records, pages, 1),
    }


def safe_rate(numerator: int, denominator: int, multiplier: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * multiplier, 6)


def scale_behavior(scale_factor: int, records: int) -> str:
    if records == 0:
        return "empty-output"
    if scale_factor >= 4 and records <= 1:
        return "severe-summary-collapse"
    if scale_factor >= 16 and records < 10:
        return "large-context-under-extraction"
    return "usable-structure-candidates"


def interpret(records: list[dict[str, Any]]) -> str:
    completed = sum(1 for record in records if record["outcome"]["status"] == "completed-parseable")
    collapses = [
        record
        for record in records
        if record["outcome"]["scale_behavior"]
        in {"severe-summary-collapse", "large-context-under-extraction"}
    ]
    if completed == len(records) and collapses:
        return (
            "All scale runs completed with parseable output under the long-timeout protocol, "
            "but record yield was non-monotonic and larger contexts showed summary-collapse risk."
        )
    if completed == len(records):
        return (
            "All scale runs completed with parseable output under the long-timeout protocol, "
            "with no immediate parse failures."
        )
    return "At least one scale run needs inspection before economics interpretation."


def supervisor_accounting() -> dict[str, Any]:
    run_total = round(sum(SUPERVISOR_SPAN_COSTS_USD.values()), 6)
    return {
        "status": "measured-span-rollup-not-per-run-allocation",
        "span_costs_usd": SUPERVISOR_SPAN_COSTS_USD,
        "scale_sequence_run_total_usd": run_total,
        "framework_update_cost_usd": FRAMEWORK_UPDATE_COST_USD,
        "framework_update_cost_note": (
            "Agent Workbench fixture implementation cost is tracked separately from "
            "the repeatable benchmark run cost."
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    supervisor = summary["supervisor_accounting"]
    lines = [
        "# Phase 1 MP11 Scale Sequence 01",
        "",
        summary["interpretation"],
        "",
        "| Scale | Pages | Words | Worker In | Worker Out | Records | Records / 1k Words | Behavior | Direct Baseline USD |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for record in summary["records"]:
        task = record["task"]
        outcome = record["outcome"]
        economics = record["economics"]
        metrics = economics["derived_metrics"]
        lines.append(
            "| {scale} | {pages} | {words} | {worker_in} | {worker_out} | "
            "{records} | {records_per_words:.3f} | `{behavior}` | {direct:.6f} |".format(
                scale=task["scale_factor"],
                pages=task["input_pages"],
                words=task["input_words"],
                worker_in=economics["worker_input_tokens"],
                worker_out=economics["worker_output_tokens"],
                records=outcome["records_produced"],
                records_per_words=metrics["records_per_1000_words"],
                behavior=outcome["scale_behavior"],
                direct=economics["direct_baseline_cost_usd"],
            )
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- Long worker timeouts removed the earlier operator-cutoff problem: all four runs completed.",
            "- Worker input tokens scaled with page and word count, but useful candidate-record yield did not scale monotonically.",
            "- The x4 and x16 runs produced valid JSONL but under-extracted badly, which is a model/protocol quality signal rather than an execution failure.",
            "- The strongest immediate guardrail is to avoid single-pass x16-sized document chunks for structure extraction unless the ticket uses a hierarchical map-reduce design, explicit minimum coverage targets, or smaller page windows.",
            "- These records use an extrapolated direct-supervisor baseline and zero audited supervisor cost for the scale sequence, so they are scale-shape evidence, not a final savings claim.",
            "",
            "Economics note:",
            "",
            DIRECT_BASELINE_SOURCE + ".",
            "Per-run net savings are intentionally marked as unclaimed until supervisor audit and repair costs are added.",
            "",
            "Measured supervisor-token cost rollup:",
            "",
            "| Span | Supervisor USD |",
            "| --- | ---: |",
        ]
    )
    for span, cost in supervisor["span_costs_usd"].items():
        lines.append(f"| `{span}` | {cost:.6f} |")
    lines.extend(
        [
            f"| `scale_sequence_run_total` | {supervisor['scale_sequence_run_total_usd']:.6f} |",
            "",
            "The rollup above is the measured paid-supervisor cost for the first scale-sequence iteration as a whole.",
            "It is not allocated per scale run yet, and it does not include the separate Agent Workbench fixture-implementation cost.",
            f"That framework update cost was measured separately at `{supervisor['framework_update_cost_usd']:.6f}` USD.",
            "",
        ]
    )
    return "\n".join(lines)


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
