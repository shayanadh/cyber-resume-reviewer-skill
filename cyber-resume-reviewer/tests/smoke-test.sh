#!/usr/bin/env bash
set -euo pipefail
REVIEW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REVIEW_TMP="$(mktemp -d)"
trap 'rm -rf "$REVIEW_TMP"' EXIT
"${REVIEW_PYTHON:-python3}" "$REVIEW_ROOT/scripts/analyze_resume_text.py" \
  --resume "$REVIEW_ROOT/examples/sample-resume-redacted.txt" \
  --jd "$REVIEW_ROOT/examples/sample-job-description-cloud-security.txt" \
  --target-title "Senior Cloud Security Engineer" > "$REVIEW_TMP/analysis.json"
"${REVIEW_PYTHON:-python3}" -m json.tool "$REVIEW_TMP/analysis.json" > /dev/null
"${REVIEW_PYTHON:-python3}" -m unittest discover -s "$REVIEW_ROOT/tests" -p 'test_*.py' -v
