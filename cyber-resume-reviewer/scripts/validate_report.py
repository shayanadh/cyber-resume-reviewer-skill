#!/usr/bin/env python3
"""Validate v4 report shape, score arithmetic, IDs, and placeholder bookkeeping.

Requires the optional jsonschema package; does not verify candidate facts.
Usage: python3 scripts/validate_report.py report.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys

CATEGORIES = ['document', 'clarity', 'positioning', 'fit', 'outcomes', 'depth', 'scope', 'requirements', 'development']
WEIGHTS = {
    'general': [10, 10, 10, 20, 15, 15, 10, 5, 5],
    'early_career': [10, 10, 10, 20, 15, 15, 5, 5, 10],
    'senior_ic': [10, 10, 10, 20, 15, 20, 10, 3, 2],
    'leadership': [10, 10, 10, 20, 15, 10, 20, 3, 2],
    'advisory': [10, 10, 10, 20, 15, 10, 15, 5, 5],
}
PLACEHOLDER = re.compile(r'\[VERIFY: [^\]\n]+\]')
LEGACY_PLACEHOLDER = re.compile(r'\[(?:Assumed:|Unknown:|[^\]\n]*[—-]\s*verify)', re.I)
SCHEMA = Path(__file__).resolve().parents[1] / 'schemas' / 'resume-review-report.schema.json'


def close(a, b):
    return isinstance(a, (int, float)) and not isinstance(a, bool) and math.isfinite(a) and math.isclose(a, b, abs_tol=1e-6)


def semantic_errors(report):
    errors = []
    scorecard = report['scorecard']
    if scorecard is not None:
        rows = scorecard['rows']
        categories = [row['category'] for row in rows]
        if set(categories) != set(CATEGORIES) or len(set(categories)) != len(categories):
            errors.append('scorecard must contain each of the nine categories exactly once')
        if not close(sum(row['weight'] for row in rows), 100):
            errors.append('scorecard weights must total 100')
        expected = dict(zip(CATEGORIES, WEIGHTS[scorecard['profile']])) if scorecard['profile'] != 'custom' else None
        earned, assessed = 0.0, 0.0
        for row in rows:
            if expected and not close(row['weight'], expected[row['category']]):
                errors.append(f"wrong weight for {row['category']} in selected profile")
            if row['rating'] is None:
                if row['points'] is not None:
                    errors.append(f"unassessed {row['category']} must have null points")
            else:
                points = row['weight'] * row['rating'] / 5
                if not close(row['points'], points):
                    errors.append(f"incorrect points for {row['category']}")
                earned += points
                assessed += row['weight']
        if not close(scorecard['assessed_weight'], assessed):
            errors.append('assessed_weight does not equal assessed row weights')
        overall = round(100 * earned / assessed, 1) if assessed else None
        if (overall is None and scorecard['overall_score'] is not None) or (overall is not None and not close(scorecard['overall_score'], overall)):
            errors.append('overall_score must use normalized assessed weights and one-decimal rounding')
        if scorecard['provisional'] != (assessed < 100):
            errors.append('provisional must be true whenever assessed coverage is below 100')
    for collection in ['findings', 'edits', 'questions']:
        ids = [item['id'] for item in report[collection]]
        if len(ids) != len(set(ids)):
            errors.append(f'{collection} IDs must be unique')
    question_ids = {q['id'] for q in report['questions']}
    for edit in report['edits']:
        text = edit['replacement_text'] or ''
        if edit['action'] in {'replace', 'add'}:
            if not text.strip():
                errors.append(f"{edit['id']}: add/replace needs replacement text")
            if not edit['source_refs']:
                errors.append(f"{edit['id']}: add/replace needs a source reference")
        if edit['action'] in {'replace', 'delete', 'retain', 'move'} and not edit['original_text']:
            errors.append(f"{edit['id']}: action needs original text")
        if any(q not in question_ids for q in edit['verification_question_ids']):
            errors.append(f"{edit['id']}: unresolved question reference")
        if edit['status'] == 'supported' and (PLACEHOLDER.search(text) or LEGACY_PLACEHOLDER.search(text) or edit['verification_question_ids']):
            errors.append(f"{edit['id']}: supported edit cannot depend on unresolved facts")
        if edit['status'] == 'needs_verification' and not edit['verification_question_ids']:
            errors.append(f"{edit['id']}: needs_verification requires a linked question")
        if LEGACY_PLACEHOLDER.search(text):
            errors.append(f"{edit['id']}: use explicit VERIFY placeholders; no assumed facts")
    rewritten = report.get('rewritten_resume')
    if rewritten:
        actual = Counter(PLACEHOLDER.findall(rewritten['text']))
        listed = Counter(p['token'] for p in rewritten['placeholders'])
        if actual != listed:
            errors.append('rewrite placeholder table must account for every occurrence')
        if LEGACY_PLACEHOLDER.search(rewritten['text']):
            errors.append('rewrite contains legacy assumption/unknown placeholders')
        if rewritten['status'] == 'clean' and (actual or rewritten['placeholders']):
            errors.append('clean rewrite cannot contain unresolved placeholders')
        if any(p['question_id'] not in question_ids for p in rewritten['placeholders']):
            errors.append('rewrite has unresolved question references')
    return errors


def validate(report):
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError('JSON report validation requires the optional jsonschema package. The text analyzer has no external dependencies.') from exc
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = [f"{'/'.join(map(str, e.absolute_path)) or 'report'}: {e.message}" for e in validator.iter_errors(report)]
    if errors:
        return errors
    return semantic_errors(report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', help='Report JSON file')
    args = parser.parse_args(argv)
    try:
        report = json.loads(Path(args.report).read_text(encoding='utf-8-sig'), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f'non-finite JSON number {value}')))
        errors = validate(report)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f'error: {exc}\n')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Report valid: schema, arithmetic, references, and placeholder bookkeeping. Candidate facts still require human review.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
