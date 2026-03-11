import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def load_dataset(path: Path) -> List[Dict]:
    items = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
            items.append(obj)
    return items


def run_eval(items: List[Dict], mode: str) -> List[Dict]:
    predictions = []
    translator_service = None

    if mode == "live":
        from translator import translator as translator_service  # lazy import

    for item in items:
        source = item.get("source_text", "")
        source_lang = item.get("source_lang", "en_US")
        target_lang = item.get("target_lang", "zh_TW")
        reference = item.get("reference", "")

        if mode == "live":
            try:
                output = translator_service.translate(source, source_lang, target_lang)
                error = ""
            except Exception as exc:
                output = ""
                error = str(exc)
        else:
            output = ""
            error = ""

        predictions.append(
            {
                "id": item.get("id", ""),
                "domain": item.get("domain", ""),
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": source,
                "reference": reference,
                "output_text": output,
                "error": error,
            }
        )

    return predictions


def compute_summary(predictions: List[Dict]) -> Dict:
    total = len(predictions)
    non_empty = sum(1 for p in predictions if (p.get("output_text") or "").strip())
    errors = sum(1 for p in predictions if (p.get("error") or "").strip())
    refs = sum(1 for p in predictions if (p.get("reference") or "").strip())
    exact = sum(
        1
        for p in predictions
        if (p.get("reference") or "").strip()
        and (p.get("reference") or "").strip() == (p.get("output_text") or "").strip()
    )

    avg_source_len = (
        sum(len(p.get("source_text", "")) for p in predictions) / total if total else 0.0
    )
    avg_output_len = (
        sum(len(p.get("output_text", "")) for p in predictions) / total if total else 0.0
    )

    by_pair: Dict[str, int] = {}
    for p in predictions:
        key = f"{p.get('source_lang','?')}->{p.get('target_lang','?')}"
        by_pair[key] = by_pair.get(key, 0) + 1

    return {
        "total_cases": total,
        "non_empty_outputs": non_empty,
        "non_empty_rate": (non_empty / total) if total else 0.0,
        "error_count": errors,
        "reference_cases": refs,
        "exact_match_count": exact,
        "exact_match_rate": (exact / refs) if refs else 0.0,
        "avg_source_chars": avg_source_len,
        "avg_output_chars": avg_output_len,
        "by_language_pair": by_pair,
    }


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: List[Dict]) -> None:
    fields = [
        "id",
        "domain",
        "source_lang",
        "target_lang",
        "source_text",
        "reference",
        "output_text",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def write_markdown(path: Path, summary: Dict, mode: str, dataset: Path) -> None:
    lines = []
    lines.append("# Eval Report")
    lines.append("")
    lines.append(f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`")
    lines.append(f"- Mode: `{mode}`")
    lines.append(f"- Dataset: `{dataset}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total cases: **{summary['total_cases']}**")
    lines.append(f"- Non-empty outputs: **{summary['non_empty_outputs']}** ({summary['non_empty_rate']:.2%})")
    lines.append(f"- Error count: **{summary['error_count']}**")
    lines.append(f"- Reference cases: **{summary['reference_cases']}**")
    lines.append(f"- Exact match count: **{summary['exact_match_count']}** ({summary['exact_match_rate']:.2%})")
    lines.append(f"- Avg source chars: **{summary['avg_source_chars']:.1f}**")
    lines.append(f"- Avg output chars: **{summary['avg_output_chars']:.1f}**")
    lines.append("")
    lines.append("## Language Pair Distribution")
    for pair, count in sorted(summary["by_language_pair"].items()):
        lines.append(f"- `{pair}`: {count}")
    lines.append("")
    lines.append("## Notes")
    lines.append("- `dry` mode does not call model inference and is used for pipeline sanity checks.")
    lines.append("- `live` mode calls the translation backend and can be used for baseline snapshots.")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run seed evaluation for TranslateGemma.")
    parser.add_argument(
        "--dataset",
        default="datasets/eval/seed_v1.jsonl",
        help="Path to JSONL dataset.",
    )
    parser.add_argument(
        "--outdir",
        default="reports/eval",
        help="Output directory for evaluation artifacts.",
    )
    parser.add_argument(
        "--mode",
        choices=["dry", "live"],
        default="dry",
        help="dry: no model calls; live: run actual translation.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit for number of cases (0 means all).",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=-1,
        help="Fail when error_count is greater than this value. Use -1 to disable.",
    )
    parser.add_argument(
        "--min-non-empty-rate",
        type=float,
        default=-1.0,
        help="Fail when non_empty_rate is lower than this value (0.0~1.0). Use -1 to disable.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    items = load_dataset(dataset_path)
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    predictions = run_eval(items, args.mode)
    summary = compute_summary(predictions)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = outdir / f"eval_predictions_{args.mode}_{ts}.jsonl"
    csv_path = outdir / f"eval_predictions_{args.mode}_{ts}.csv"
    md_path = outdir / f"eval_report_{args.mode}_{ts}.md"

    write_jsonl(jsonl_path, predictions)
    write_csv(csv_path, predictions)
    write_markdown(md_path, summary, args.mode, dataset_path)

    print("Evaluation completed.")
    print(f"- JSONL: {jsonl_path}")
    print(f"- CSV:   {csv_path}")
    print(f"- Report:{md_path}")
    print(f"- Cases: {summary['total_cases']}, Errors: {summary['error_count']}, Non-empty rate: {summary['non_empty_rate']:.2%}")

    gate_failures = []
    if args.max_errors >= 0 and summary["error_count"] > args.max_errors:
        gate_failures.append(
            f"error_count={summary['error_count']} exceeds max_errors={args.max_errors}"
        )
    if args.min_non_empty_rate >= 0 and summary["non_empty_rate"] < args.min_non_empty_rate:
        gate_failures.append(
            f"non_empty_rate={summary['non_empty_rate']:.4f} below min_non_empty_rate={args.min_non_empty_rate:.4f}"
        )

    if gate_failures:
        print("Gate check failed:")
        for failure in gate_failures:
            print(f"- {failure}")
        sys.exit(2)

    print("Gate check passed.")


if __name__ == "__main__":
    main()
