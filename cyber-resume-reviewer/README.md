# Skill guide

`cyber-resume-reviewer` reviews, tailors, scores, and rewrites resumes for IT and cybersecurity roles. It grounds edits in supplied facts and keeps unknowns visible. It does not rank candidates or predict hiring outcomes.

## Review lenses

| Lens | Question |
|---|---|
| Machine-read | Does the source extract in the expected order, and what parser risks are visible? |
| Human-skim | Does the opening establish the target, level, and useful evidence? |
| Human-believe | Do scope, ownership, technical claims, and results have support? |
| Human-act | Does the document address the stated role without turning assumptions into facts? |

## Outputs

- A full review or job-description fit report produces Markdown and a styled PDF from that Markdown.
- A quick review stays short and omits scoring unless requested.
- A rewrite produces the complete revised resume from established facts.
- JSON output follows `schemas/resume-review-report.schema.json`.

The standard report uses an assessment, prioritized findings with exact edits, target fit when a target exists, source-file checks, an optional diagnostic score, and ordered next actions. The agent removes sections that do not help the request.

## Resources

- `SKILL.md` routes the task and defines the truth, privacy, and visual evidence rules.
- `references/` covers role families, scoring, job requirements, technical claims, parser risk, leadership, transitions, bias, and sources.
- `templates/` provides adaptable review and rewrite structures.
- `scripts/analyze_resume_text.py` reports text signals without inferring qualification or ATS outcomes.
- `scripts/render_report.py` and `assets/report.css` render the PDF. Read `references/report-rendering.md` before use.
- `scripts/validate_report.py` validates optional structured JSON when `jsonschema` is available.
- `examples/` contains fictional inputs and outputs. Examples never count as candidate evidence.

## Non-negotiable rules

Keep employers, titles, dates, scope, participation level, credentials, and outcomes faithful to the source. Separate job requirements, candidate evidence, reviewer inference, and unknowns. Keep live candidate data out of this skill directory and source control.

The PDF design uses colour for finding priority and evidence provenance. It does not use match percentages, letter grades, score gauges, skill bars, or traffic-light judgments about a person.

## Local helpers

From this directory:

```bash
python3 scripts/analyze_resume_text.py --resume resume.txt --jd job.txt
python3 scripts/render_report.py /path/to/review.md /path/to/resume-review.pdf
python3 scripts/validate_report.py report.json
bash tests/smoke-test.sh
```

The analyzer uses the Python standard library. The renderer's optional dependencies are listed in `scripts/report-requirements.txt`. Generated candidate files belong outside this directory.
