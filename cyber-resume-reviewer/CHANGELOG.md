# v4.1.0 — 2026-09-07

- Added a two-artifact contract for full reviews: editable Markdown plus a styled PDF rendered from the same source.
- Added a generic PDF renderer, print stylesheet, metadata contract, visual evidence rules, dependency list, and automated renderer tests.
- Added an explicit privacy invariant: reusable skill files and source history may not contain live candidate data.
- Updated the standard report structure with renderer-aware finding, evidence, and verification patterns.
- Added clean `.skill` and wrapped ZIP packaging, release automation, and separate public and skill-maintainer documentation.

# v4.0.0 — 2026-09-07

Reviewed all 30 files in the supplied v3 archive. Revised every original component, retaining the skill name and the useful four-lens approach. Added focused references and validation resources where the original had a concrete gap.

## Main changes

- Expanded from cybersecurity-only framing to explicit IT and cybersecurity coverage, including support, systems, networking, endpoint engineering, platform/SRE, and IT leadership.
- Replaced “fatal flaws,” fixed recruiter timing, and guaranteed ATS rejection claims with evidence-based submission triage and stated limitations.
- Removed assumed achievements from rewrite instructions and examples. A clean rewrite uses candidate facts; optional missing details stay in questions.
- Made output proportional to the request. A rewrite request produces the rewrite; a quick review does not force a lengthy report, scorecard, or learning plan. No target no longer blocks general improvements.
- Rebuilt scoring with nine distinct categories and five explicit profiles that each total 100. The original ten category weights totaled 102, while its stated stage totals and example scores disagreed. Unassessed categories now remain null, and normalized scores disclose assessed coverage.
- Distinguished mandatory/preferred requirements, AND/OR alternatives, timing, and candidate evidence status. A missing resume example is not automatically missing experience or dishonesty.
- Corrected federal-resume, clearance/suitability, credential-status, and retired-certification guidance; added primary-source links and refresh rules.
- Replaced the heuristic analyzer, introduced a strict v4 report schema and semantic validator, and expanded tests beyond “emits valid JSON.”

## Audit of original components

| Original file | Improvement implemented |
|---|---|
| `SKILL.md` | Shorter entrypoint; practical routing; requested-action completion; no assumed facts or unavailable named-tool dependency |
| `references/bias-and-ethics-guardrails.md` | Redaction, privacy, source-instruction boundaries, fair treatment of gaps and nontraditional paths |
| `references/job-requirement-triage.md` | Two-axis importance/evidence model; Boolean alternatives and timing; no arbitrary apply percentage |
| `references/fatal-flaws-and-kill-checks.md` | Observed blockers vs risks/unknowns; filename retained for compatibility |
| `references/scoring-rubric.md` | Correct arithmetic, explicit profiles, null handling, coverage disclosure, no letter grades or score cap |
| `references/cybersecurity-role-taxonomy.md` | IT families, threat intelligence, senior IC distinctions, actual scope instead of title/headcount assumptions |
| `references/anti-pattern-gallery.md` | Replaced exaggerating examples and ridicule with 32 bounded source-to-edit patterns |
| `references/recruiter-reader-psychology.md` | First-impression assessment without mind-reading, fixed timings, or fabricated visual layout |
| `references/ats-formatting-and-parser-risk.md` | Separates upload, extraction, field mapping, ranking, and screening; actual document checks |
| `references/outcome-bullet-rewrite-guide.md` | Supported edits plus optional evidence questions; qualitative proof and accurate contribution verbs |
| `references/career-transition-translation.md` | Removes invented security work and corporate rank equivalence; preserves transferable seniority |
| `references/certifications-and-learning.md` | Confirm gap before training; issuer status/retirement checks; no compulsory cert shopping list |
| `references/executive-and-leadership-resumes.md` | Preserves technical differentiation; separates influence/authority, board access, advisory and operational responsibility |
| `references/review-framework.md` | Compact evidence map, source isolation, confidence by dimension, no repeated grading workflow |
| `references/keyword-and-fit-mapping.md` | Lexical presence vs experience; product renames vs adjacent tools; precise placement advice |
| `schemas/resume-review-report.schema.json` | Versioned strict fields, optional scoring, nulls, source references, questions, rewrite status |
| `scripts/analyze_resume_text.py` | Non-duplicated dates; Markdown sections; wrapped bullets; aliases; version-number exclusions; input errors; no page or fit guess |
| `examples/sample-resume-redacted.txt` | Clearly redacted fictional source with both useful achievements and intentionally thin evidence |
| `examples/sample-job-description-cloud-security.txt` | Explicit alternatives and preferences; no stale named credential recommendation |
| `examples/example-output-summary.md` | Source-faithful edits, correct score/coverage, no invented tools, outcomes, compliance scope, or recruiter verdict |
| `templates/resume-change-log-template.md` | Applied vs proposed changes with provenance |
| `templates/quick-review-template.md` | Short optional structure; no forced scoring, issue counts, or learning plan |
| `templates/rewritten-resume-template.md` | Delivers supported complete rewrites; incomplete status only when needed; real document QA |
| `templates/rewrite-table-template.md` | Source-backed additions, accurate quotes, bounded replacement claims |
| `templates/interview-story-bank-template.md` | Preserves team attribution, unknown details, and disclosure limits |
| `templates/report-template.md` | Reduced duplication; clear evidence and limitations; optional score/fit sections |
| `templates/prompt-intake-template.md` | Minimum necessary intake; useful work before optional questions |
| `tests/smoke-test.sh` | Unique temporary workspace, cleanup, configurable interpreter, regression suite |
| `README.md` | Current package usage, dependencies, limitations, and breaking JSON-contract changes |
| `CHANGELOG.md` | Replaces repetitive prior release claims with a reviewable component audit |

## Added resources

- Technical claim checks for cyber metrics, control coverage, audit terminology, recovery, OAuth, attribution, and unmeasured prevention claims.
- Federal/cleared-role guidance and primary-source refresh policy.
- Analyzer interpretation and a bounded, maintainable alias vocabulary.
- Report validator for shape, weights, normalized arithmetic, IDs, references, and placeholder occurrences.
- Valid JSON example, substantive analyzer/report regression tests, and optional Codex UI metadata.

## Validation scope

Automated checks exercise deterministic behavior and report invariants. Independent sample-request runs check clean transition rewriting and leadership review behavior. Neither establishes universal ATS compatibility, verified credentials, or hiring outcomes. Current factual guidance includes checked dates and links so later uses can refresh it.

## Prior package

The input identifies itself as v3 (2026-05-02), following v1/v2. This release deliberately changes both JSON contracts; update downstream consumers rather than treating v4 as a drop-in schema replacement.
