"""Summarize ignored MP11 fixed-x8 bundled outputs into experiment records."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


INPUT_DIR = Path("runtime/mp11_document_metadata_index/x8_bundle_sequence_02")
OUTPUT_DIR = Path("benchmarks/mp11_document_metadata_index/x8_bundle_sequence_02")
SUMMARY_JSON = OUTPUT_DIR / "summary.json"
SUMMARY_MD = Path("planning/phase1_mp11_x8_bundle_sequence_02.md")
SUPERVISOR_SPAN_COSTS_USD: dict[str, float] = {
    "setup_and_ticket_build": 0.057003,
    "worker_run_orchestration": 0.206516,
    "worker_output_summarize": 0.301944,
    "supervisor_audit_interpretation": 0.067139,
}
PRIOR_SINGLE_PASS_X8 = {
    "strategy": "x8-single-ticket",
    "model": "qwen3-coder-next:latest",
    "worker_input_tokens": 51732,
    "worker_output_tokens": 7301,
    "records_produced": 27,
    "records_per_page": 0.28125,
    "records_per_1000_words": 1.209027,
    "behavior": "usable-structure-candidates",
    "source": "scale_sequence_01",
}


def main() -> None:
    index = json.loads((INPUT_DIR / "x8_bundle_sequence_index.json").read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    strategy_records = summarize_strategies(index)
    for record in strategy_records:
        record_path = OUTPUT_DIR / f"{record['record_id']}.experiment.json"
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    summary = {
        "schema_version": 1,
        "series_id": index["series_id"],
        "generated_utc": now_utc(),
        "fixed_input": index["fixed_input"],
        "records": strategy_records,
        "supervisor_accounting": supervisor_accounting(),
        "interpretation": interpret(strategy_records),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(f"wrote {SUMMARY_JSON}")
    print(f"wrote {SUMMARY_MD}")


def summarize_strategies(index: dict[str, Any]) -> list[dict[str, Any]]:
    rows_by_strategy_model: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    part_by_task = {part["task_id"]: part for part in index["parts"]}

    for part in index["parts"]:
        eval_summary_path = Path(part["output_dir"]) / "summary.json"
        eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
        for row in eval_summary["rows"]:
            row = dict(row)
            row["part"] = part
            row["eval_summary_path"] = str(eval_summary_path)
            rows_by_strategy_model[(part["strategy_id"], row["model"])].append(row)

    records = []
    for (strategy_id, model), rows in sorted(rows_by_strategy_model.items()):
        records.append(summarize_strategy_model(index, strategy_id, model, rows, part_by_task))
    return records


def summarize_strategy_model(
    index: dict[str, Any],
    strategy_id: str,
    model: str,
    rows: list[dict[str, Any]],
    part_by_task: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    part_summaries = []
    worker_input_tokens = 0
    worker_output_tokens = 0
    parse_errors = []
    statuses = []
    object_type_counts: Counter[str] = Counter()
    worker_model_mismatches = 0
    source_sha_mismatches = 0
    duplicate_record_ids = 0
    record_ids: set[str] = set()

    for row in sorted(rows, key=lambda item: item["part"]["part_id"]):
        part = row["part"]
        records, parse_error, output_shape = parse_records(row.get("assistant_message", ""))
        raw_path = Path(row["result_file"])
        raw_text = raw_path.read_text(encoding="utf-8-sig") if raw_path.exists() else ""
        input_tokens, output_tokens = usage_tokens(raw_text)
        worker_input_tokens += input_tokens or 0
        worker_output_tokens += output_tokens or 0
        statuses.append(classify(row, records, parse_error))
        if parse_error:
            parse_errors.append(f"{part['part_id']}: {parse_error}")
        for record in records:
            all_records.append(record)
            object_type_counts[str(record.get("object_type", "<missing>"))] += 1
            if record.get("worker_model") != model:
                worker_model_mismatches += 1
            if record.get("source_sha256") != index["source_sha256"]:
                source_sha_mismatches += 1
            record_id = str(record.get("record_id", ""))
            if record_id in record_ids:
                duplicate_record_ids += 1
            record_ids.add(record_id)
        part_summaries.append(
            {
                "part_id": part["part_id"],
                "task_id": part["task_id"],
                "page_range": f"{part['start_page']}-{part['end_page']}",
                "input_pages": part["page_count"],
                "input_words": part["word_count"],
                "worker_input_tokens": input_tokens or 0,
                "worker_output_tokens": output_tokens or 0,
                "records_produced": len(records),
                "status": statuses[-1],
                "output_shape": output_shape,
                "runtime_eval_summary": str(row["eval_summary_path"]),
                "runtime_result_file": str(raw_path),
            }
        )

    page_count = fixed_pages(index)
    word_count = fixed_words(index, strategy_id, part_by_task)
    status = aggregate_status(statuses)
    economics_status = "worker-only-scale-signal"
    return {
        "record_id": f"mp11-x8-bundle-{strategy_id}-{model_slug(model)}-run01",
        "schema_version": 1,
        "generated_utc": now_utc(),
        "experiment": {
            "experiment_id": f"mp11-x8-bundle-{strategy_id}-{model_slug(model)}-run01",
            "series_id": index["series_id"],
            "project": "agent-delegation-lab",
            "phase": "p1",
        },
        "task": {
            "task_id": f"mp11-x8-bundle-{strategy_id}",
            "task_family": "long-document-structure-pass",
            "scale_factor": 8,
            "input_pages": page_count,
            "input_words": word_count,
            "input_characters": fixed_characters(index, strategy_id, part_by_task),
            "packaging_strategy": strategy_id,
            "part_count": len(rows),
        },
        "model": {
            "model_id": model,
            "provider": "local-ollama",
            "cash_cost_per_token_usd": 0,
        },
        "protocol": {
            "authority_level": "L0",
            "timeout_seconds": index["timeout_seconds"],
            "audit_strategy": "not-yet-audited",
            "ticket_template": "mp11-fixed-x8-bundle-jsonl",
        },
        "outcome": {
            "status": status,
            "records_produced": len(all_records),
            "accepted_records": 0,
            "repairable_records": 0,
            "rejected_records": 0,
            "needs_review_records": len(all_records),
            "object_type_counts": dict(sorted(object_type_counts.items())),
            "parse_errors": parse_errors,
            "part_summaries": part_summaries,
            "worker_model_mismatches": worker_model_mismatches,
            "source_sha_mismatches": source_sha_mismatches,
            "duplicate_record_ids": duplicate_record_ids,
            "scale_behavior": scale_behavior(len(all_records), page_count, statuses),
        },
        "economics": {
            "economics_status": economics_status,
            "worker_input_tokens": worker_input_tokens,
            "worker_output_tokens": worker_output_tokens,
            "worker_cost_usd": 0,
            "supervisor_cost_usd": 0.0,
            "direct_baseline_cost_usd": index["fixed_input"]["direct_baseline_cost_usd"],
            "direct_baseline_cost_source": index["fixed_input"]["direct_baseline_cost_source"],
            "net_savings_usd": index["fixed_input"]["direct_baseline_cost_usd"],
            "net_savings_status": "not-claimed-until-supervisor-audit-cost-is-added",
            "derived_metrics": derived_metrics(
                records=len(all_records),
                worker_input_tokens=worker_input_tokens,
                worker_output_tokens=worker_output_tokens,
                words=word_count,
                pages=page_count,
            ),
        },
        "links": {
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
            adjacent_records, adjacent_error = parse_adjacent_json_objects(text)
            if not adjacent_error:
                return adjacent_records, "", "adjacent_json_objects"
            return records, f"jsonl parse error: {exc.msg}; {adjacent_error}", "jsonl_invalid"
        if isinstance(value, dict):
            records.append(value)
    return records, "", "jsonl"


def parse_adjacent_json_objects(text: str) -> tuple[list[dict[str, Any]], str]:
    decoder = json.JSONDecoder()
    records = []
    position = 0
    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text):
            break
        try:
            value, end = decoder.raw_decode(text, position)
        except json.JSONDecodeError as exc:
            return records, f"adjacent-json parse error: {exc.msg}"
        if isinstance(value, dict):
            records.append(value)
        position = end
    return records, ""


def usage_tokens(text: str) -> tuple[int | None, int | None]:
    input_values = re.findall(r'"input_tokens"\s*:\s*(\d+)', text)
    output_values = re.findall(r'"output_tokens"\s*:\s*(\d+)', text)
    input_tokens = int(input_values[-1]) if input_values else None
    output_tokens = int(output_values[-1]) if output_values else None
    return input_tokens, output_tokens


def classify(row: dict[str, Any], records: list[dict[str, Any]], parse_error: str) -> str:
    if row["status"] != "completed":
        if records and not parse_error:
            return f"{row['blocker'] or 'blocked'}-with-parseable-output"
        return row["blocker"] or "blocked"
    if parse_error:
        return "completed-unparseable"
    if records:
        return "completed-parseable"
    return "completed-empty"


def aggregate_status(statuses: list[str]) -> str:
    if all(status == "completed-parseable" for status in statuses):
        return "completed-parseable"
    if all(status == "completed-parseable" or status.endswith("-with-parseable-output") for status in statuses):
        return "completed-with-salvageable-model-failures"
    if any(status == "blocked" or status.endswith("timeout") for status in statuses):
        return "partially-blocked"
    if any(status == "completed-unparseable" for status in statuses):
        return "completed-with-parse-errors"
    return "completed-with-low-yield"


def scale_behavior(records: int, pages: int, statuses: list[str]) -> str:
    if not all(status == "completed-parseable" or status.endswith("-with-parseable-output") for status in statuses):
        return "needs-format-debug"
    records_per_page = records / pages if pages else 0
    if records_per_page >= 0.6:
        return "high-coverage-candidates"
    if records_per_page >= 0.25:
        return "usable-structure-candidates"
    if records > 0:
        return "under-extraction"
    return "empty-output"


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


def fixed_pages(index: dict[str, Any]) -> int:
    return int(index["fixed_input"]["page_count"])


def fixed_words(
    index: dict[str, Any],
    strategy_id: str,
    part_by_task: dict[str, dict[str, Any]],
) -> int:
    del index
    return sum(part["word_count"] for part in part_by_task.values() if part["strategy_id"] == strategy_id)


def fixed_characters(
    index: dict[str, Any],
    strategy_id: str,
    part_by_task: dict[str, dict[str, Any]],
) -> int:
    del index
    return sum(part["char_count"] for part in part_by_task.values() if part["strategy_id"] == strategy_id)


def safe_rate(numerator: int, denominator: int, multiplier: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * multiplier, 6)


def supervisor_accounting() -> dict[str, Any]:
    run_total = round(sum(SUPERVISOR_SPAN_COSTS_USD.values()), 6)
    return {
        "status": "measured-run-overhead-not-source-level-audit-allocation",
        "span_costs_usd": SUPERVISOR_SPAN_COSTS_USD,
        "x8_bundle_sequence_run_total_usd": run_total,
        "direct_supervisor_baseline_usd": 1.228648,
        "preliminary_overhead_delta_usd": round(run_total - 1.228648, 6),
        "note": (
            "This measures benchmark operation overhead through interpretation, "
            "not a per-record source-level audit or repair pass."
        ),
    }


def interpret(records: list[dict[str, Any]]) -> str:
    if not records:
        return "No bundle records were available for interpretation."
    completed = [record for record in records if record["outcome"]["status"] == "completed-parseable"]
    if len(completed) != len(records):
        return "At least one bundle lane needs format or execution inspection."
    best = max(
        records,
        key=lambda record: record["economics"]["derived_metrics"]["records_per_page"],
    )
    return (
        "All fixed-x8 bundle lanes completed with parseable output. "
        f"The highest candidate density came from `{best['task']['packaging_strategy']}` "
        f"with `{best['model']['model_id']}`."
    )


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 MP11 Fixed-X8 Bundle Sequence 02",
        "",
        summary["interpretation"],
        "",
        "Fixed benchmark input:",
        "",
        f"- pages: {summary['fixed_input']['start_page']}-{summary['fixed_input']['end_page']}",
        f"- direct supervisor baseline: `${summary['fixed_input']['direct_baseline_cost_usd']:.6f}`",
        "",
        "| Strategy | Model | Parts | Worker In | Worker Out | Records | Records / Page | Records / 1k Words | Behavior |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        "| {strategy} | `{model}` | 1 | {worker_in} | {worker_out} | {records} | {records_per_page:.3f} | {records_per_words:.3f} | `{behavior}` |".format(
            strategy=PRIOR_SINGLE_PASS_X8["strategy"],
            model=PRIOR_SINGLE_PASS_X8["model"],
            worker_in=PRIOR_SINGLE_PASS_X8["worker_input_tokens"],
            worker_out=PRIOR_SINGLE_PASS_X8["worker_output_tokens"],
            records=PRIOR_SINGLE_PASS_X8["records_produced"],
            records_per_page=PRIOR_SINGLE_PASS_X8["records_per_page"],
            records_per_words=PRIOR_SINGLE_PASS_X8["records_per_1000_words"],
            behavior=PRIOR_SINGLE_PASS_X8["behavior"],
        ),
    ]
    for record in summary["records"]:
        task = record["task"]
        model = record["model"]
        outcome = record["outcome"]
        economics = record["economics"]
        metrics = economics["derived_metrics"]
        lines.append(
            "| {strategy} | `{model}` | {parts} | {worker_in} | {worker_out} | "
            "{records} | {records_per_page:.3f} | {records_per_words:.3f} | `{behavior}` |".format(
                strategy=task["packaging_strategy"],
                model=model["model_id"],
                parts=task["part_count"],
                worker_in=economics["worker_input_tokens"],
                worker_out=economics["worker_output_tokens"],
                records=outcome["records_produced"],
                records_per_page=metrics["records_per_page"],
                records_per_words=metrics["records_per_1000_words"],
                behavior=outcome["scale_behavior"],
            )
        )
    lines.extend(
        [
            "",
            "Part-level yields:",
            "",
            "| Strategy | Model | Part | Pages | Worker In | Worker Out | Records | Status |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for record in summary["records"]:
        for part in record["outcome"]["part_summaries"]:
            lines.append(
                "| {strategy} | `{model}` | {part} | {pages} | {worker_in} | {worker_out} | {records} | `{status}` |".format(
                    strategy=record["task"]["packaging_strategy"],
                    model=record["model"]["model_id"],
                    part=part["part_id"],
                    pages=part["page_range"],
                    worker_in=part["worker_input_tokens"],
                    worker_out=part["worker_output_tokens"],
                    records=part["records_produced"],
                    status=part["status"],
                )
            )
    lines.extend(
        [
            "",
            "Economics note:",
            "",
        "- The direct-supervisor baseline is reused because this experiment keeps the exact x8 input definition.",
        "- The single-ticket x8 reference is included for shape comparison only; it is the prior sequence-01 qwen run on the same pages.",
        "- Worker token cash cost remains zero under local Ollama.",
        "- Benefit-cost ratios remain unclaimed until measured source-level audit/repair costs are allocated to the bundle lanes.",
        "",
    ]
    )
    supervisor = summary["supervisor_accounting"]
    if supervisor["span_costs_usd"]:
        lines.extend(
            [
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
                f"| `x8_bundle_sequence_run_total` | {supervisor['x8_bundle_sequence_run_total_usd']:.6f} |",
                f"| `direct_supervisor_baseline` | {supervisor['direct_supervisor_baseline_usd']:.6f} |",
                f"| `preliminary_overhead_delta` | {supervisor['preliminary_overhead_delta_usd']:.6f} |",
                "",
                "The preliminary overhead delta compares measured benchmark operation overhead to the reused direct-supervisor baseline.",
                "It is favorable for this run, but it is not a final win claim because source-level audit/repair is still unallocated.",
                "",
            ]
        )
    return "\n".join(lines)


def model_slug(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", model).strip("_").lower()


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
