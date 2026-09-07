# IT and Cybersecurity Resume Reviewer

An Agent Skill for evidence-led resume reviews, job-description tailoring, exact edits, diagnostic scoring, and complete rewrites across IT and cybersecurity roles.

A full review produces an editable Markdown report and a styled PDF generated from the same source. The skill does not rank candidates, predict interviews, or invent missing achievements.

## Prompt it

Attach the original resume when possible. A PDF or DOCX lets the agent check extraction and visible layout; pasted text supports content review only.

With a job description:

> Use the cyber-resume-reviewer skill to review my attached resume against the attached job description. Give me a candid fit assessment, prioritized findings, and exact edits supported by my resume. Do not invent metrics or experience. Deliver the full report as Markdown and PDF.

Without a job description:

> Use the cyber-resume-reviewer skill to review my attached resume for IT and cybersecurity roles. Identify the strongest evidence, the highest-value fixes, and one or two plausible target directions. Mark layout checks you cannot perform as not assessed. Deliver the full report as Markdown and PDF.

For a rewrite:

> Use the cyber-resume-reviewer skill to rewrite my resume for a security engineering role. Use only facts in the source. Put questions for stronger claims outside the clean resume.

## Download and install

Tagged releases publish two clean archives on the [Releases page](https://github.com/mubix/cyber-resume-reviewer-skill/releases):

- `cyber-resume-reviewer.skill` has `SKILL.md` at the archive root for `.skill` tooling.
- `cyber-resume-reviewer-claude.zip` wraps the files in a `cyber-resume-reviewer/` folder for Claude's web uploader.

Neither archive contains repository documentation, tests, workflow files, the changelog, or `.gitignore`.

| Host | Install and invoke | Support notes |
|---|---|---|
| Codex CLI or IDE | Extract the `.skill` contents to `~/.agents/skills/cyber-resume-reviewer/`, then use `$cyber-resume-reviewer` or let Codex select it. | [Codex supports local Agent Skills](https://developers.openai.com/codex/skills). Standalone and plugin distribution differ by surface. |
| Claude Code | Extract to `~/.claude/skills/cyber-resume-reviewer/` for personal use or `.claude/skills/cyber-resume-reviewer/` in a project. Invoke `/cyber-resume-reviewer`. | Claude Code follows the Agent Skills format and supports bundled files and scripts. See [Claude Code skills](https://code.claude.com/docs/en/skills). |
| Claude web | Upload `cyber-resume-reviewer-claude.zip` under Customize > Skills. | Custom skills require Skills and code execution to be enabled. Account and workspace controls apply. See [Claude custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills). |
| ChatGPT | In the desktop app, open Skills in the sidebar and select an installed skill with `@`. | OpenAI documents standalone skills for ChatGPT desktop, but its public guide does not promise direct `.skill` upload. ChatGPT web and mobile require plugin distribution, which this repository does not provide. See [OpenAI skill docs](https://developers.openai.com/codex/skills). |
| Gemini CLI | Run `gemini skills install ./cyber-resume-reviewer.skill`, then `/skills reload`. | Gemini CLI accepts local `.skill` packages. See [Gemini CLI skill management](https://geminicli.com/docs/cli/using-agent-skills/). |
| Gemini Spark | Copy or rename the `.skill` file to `.zip`, then upload it from Spark's Skills page. | Spark accepts a ZIP with `SKILL.md` at its root. Region, subscription, and account limits apply. See [Gemini Apps skills](https://support.google.com/gemini/answer/17094296?hl=en). |

The core format follows the [Agent Skills specification](https://agentskills.io/specification). Install paths, upload rules, script permissions, and feature availability remain host-specific.

## What the review covers

The skill uses four lenses:

| Lens | Intent |
|---|---|
| Machine-read | Check text extraction, reading order, and parser risks without claiming an ATS outcome. |
| Human-skim | Test the first impression, hierarchy, clarity, and positioning. |
| Human-believe | Check whether scope, ownership, technical claims, and results have evidence. |
| Human-act | Align the document with a stated target while preserving requirement wording and unknowns. |

A standard report selects from these sections:

| Section | Intent |
|---|---|
| Assessment | State the target, main conclusion, strongest evidence, and highest-impact repair. |
| Prioritized findings and exact edits | Connect each observation to source text and give a supported action or replacement. |
| Target fit | Separate employer requirements from candidate evidence and reviewer inference. |
| First impression and format | Report checks performed on the source file and mark unavailable checks unassessed. |
| Diagnostic score | Provide an optional editorial score with the selected profile and assessed coverage. |
| Next actions | Order the smallest set of changes that improves the submission. |

## Package map

- This root `README.md` is the public guide to prompting, installation, portability, dependencies, and releases.
- `cyber-resume-reviewer/README.md` is the maintainer guide to the skill's behavior and local helpers. Release archives exclude it.
- `cyber-resume-reviewer/SKILL.md` contains the workflow, truth rules, output routing, and quality gate.
- `references/` holds role taxonomy, evidence checks, scoring, parser risk, transitions, leadership guidance, and PDF rules.
- `templates/` provides report, quick-review, exact-edit, rewrite, interview-story, and change-log structures.
- `scripts/analyze_resume_text.py` reports local text signals without making hiring or ATS claims.
- `scripts/render_report.py` and `assets/report.css` turn a Markdown review into the styled PDF.
- `schemas/` and `scripts/validate_report.py` support optional JSON output.

## PDF requirements

The review instructions work without the bundled renderer. Matching the supplied PDF design requires code execution plus:

- Python 3.9+, `PyYAML`, and `beautifulsoup4`
- Python Markdown or `pandoc`
- WeasyPrint or `wkhtmltopdf`
- `pdftoppm`, `pdftotext`, `pdfinfo`, and `pdffonts` for the full visual check

Install the optional Python set with:

```bash
python3 -m pip install -r cyber-resume-reviewer/scripts/report-requirements.txt
```

The bundled rendering path does not require network access. It writes page images beside the PDF so the agent can inspect every page before delivery.

## Releases

Pushing a `v*` tag runs `.github/workflows/publish-skill.yml`. The workflow builds both archives from a runtime allowlist, records SHA-256 checksums, and attaches the files to the matching GitHub Release. A manual run builds the same files as a workflow artifact for testing.
