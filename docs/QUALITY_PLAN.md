# Quality Plan

## Quality Dimensions
- Accuracy
- Fluency
- Terminology consistency
- Format preservation

## Evaluation Datasets
- Current baseline dataset:
  - `datasets/eval/seed_v1.jsonl` (32 cases, mixed domains/language pairs)
- Planned dataset split:
  - `datasets/eval/text/`
  - `datasets/eval/pdf/`
  - `datasets/eval/ocr/`
  - `datasets/eval/voice/`

## Metrics
- Automatic (planned): BLEU / COMET
- Human (planned): adequacy / fluency rubric
- Current lightweight gates:
  - `error_count`
  - `non_empty_rate`

## Regression Strategy
- Smoke tests on every PR
- CI dry eval gate on every PR:
  - `python tools/eval_runner.py --mode dry --limit 32 --max-errors 0 --min-non-empty-rate 0.0`
- Weekly live benchmark run (manual or scheduled):
  - `python tools/eval_runner.py --mode live --limit 32 --max-errors 0 --min-non-empty-rate 0.95`

## Eval Commands
- Dry-run (pipeline sanity):
  - `python tools/eval_runner.py --mode dry --limit 32 --max-errors 0 --min-non-empty-rate 0.0`
- Live-run (real translation quality snapshot):
  - `python tools/eval_runner.py --mode live --limit 32 --max-errors 0 --min-non-empty-rate 0.95`

## Release Gate
- Suggested minimum thresholds (live mode):
  - `error_count = 0`
  - `non_empty_rate >= 0.95`
  - Human review pass for domain-critical samples
