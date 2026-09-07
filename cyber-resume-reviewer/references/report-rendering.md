# Render a review from one Markdown source

A full review or job-description fit report has two deliverables:

| Artifact | Purpose |
|---|---|
| `resume-review.md` | Editable source of truth |
| `resume-review.pdf` | Styled copy for reading or sharing |

Write and revise the Markdown. Generate the PDF from that file. Never maintain a second copy of the report text for the PDF.

Keep both artifacts outside the skill directory. Candidate names, source filenames, contact details, work history, and findings are runtime data. They must not enter templates, examples, tests, or source control.

## Render

From the skill root, run:

```bash
python3 scripts/render_report.py /path/to/review.md /path/to/resume-review.pdf
```

The renderer uses Python Markdown when installed and falls back to `pandoc`. It uses WeasyPrint when installed and falls back to `wkhtmltopdf`. It needs `PyYAML` and `beautifulsoup4` for metadata and styling upgrades. The optional Python dependencies are listed in `scripts/report-requirements.txt`.

Do not install software unless the host and user permit it. If the bundled renderer cannot run, use the host's PDF-generation tools with the same Markdown source and visual rules. If the host cannot create files, return the Markdown and state that the PDF remains ungenerated.

## Optional front matter

Plain Markdown renders without metadata. Add YAML front matter for the masthead and summary panel:

```yaml
---
candidate: "Candidate name"
header_name: "Candidate name"
subtitle: "Target role · findings, exact edits, and target fit"
reviewed: "YYYY-MM-DD"
source_file: "resume.pdf"
source_note: "original file"
targets:
  - label: "Primary target"
    value: "Target role"
status: "Targeted edits needed"
status_note: "One sentence grounded in the report."
chips:
  - title: "Issue area"
    body: "One sentence naming the issue."
impacts:
  - label: "Highest-impact edit"
    body: "One supported action."
footer_note: "Confidential"
---
```

Use one of these submission statuses exactly:

- `Ready for candidate review`
- `Targeted edits needed`
- `More evidence needed`
- `Submission blocked`
- `Not assessed`

The cover panel summarizes findings that also appear in the body. It does not introduce conclusions.

## Markdown conventions

The renderer upgrades these patterns. Ordinary Markdown remains valid.

| Markdown | PDF treatment |
|---|---|
| `## Assessment` | Numbered section heading |
| `**H1 - Title**` at the start of a paragraph | High-priority finding header |
| `**M1 - Title**` | Medium-priority finding header |
| `**O1 - Title**` | Optional finding header |
| `> *Original:* ...` | Red original-text block |
| `> *Supported replacement:* ...` | Green ready-to-use block |
| `> *Fill-in draft - INCOMPLETE, DO NOT SEND AS-IS:* ...` | Amber incomplete block |
| `**Ask:** ...` | Evidence question callout |
| `[VERIFY: fact]` | Visible verification token |
| Table with a `Status` column | Requirement-fit table with evidence-status labels |
| `<!-- pagebreak -->` | Explicit page break; use only after a visual check |

Use only these evidence statuses in a fit table: `Demonstrated`, `Claimed only`, `Adjacent`, `Not shown`, `Confirmed unmet`, and `Unknown`. Put nuance in the evidence or action column. An unrecognized status remains unstyled so reviewers notice it.

## Visual evidence rules

The layout must preserve the same claim boundaries as the prose.

- Do not use gauges, progress bars, percentage rings, dials, letter grades, match percentages, radar charts, proficiency bars, or confidence percentages.
- Do not assign a traffic-light colour to the candidate or resume.
- A checkmark means a check was performed. It does not mean the candidate passed a screen.
- Do not add findings or sections to balance a page. Final-page white space is acceptable.

Colour has a fixed role:

| Colour | Meaning |
|---|---|
| Red | High-priority finding or exact original text |
| Amber | Medium-priority finding or incomplete draft containing `[VERIFY]` |
| Slate | Optional finding or neutral structure |
| Green | Supported replacement, preserved strength, or performed check |
| Navy | Structure or employer-quoted requirement |

A supported replacement may contain only established facts. The renderer stops if a `[VERIFY]` token appears in a green supported-replacement block.

## Verification gate

The PDF is complete after someone checks the file, not when the render command exits.

1. Inspect every page image. The renderer writes JPEGs beside the PDF unless `--no-qa` is supplied and `pdftoppm` is unavailable.
2. Check for clipped text, split quote blocks or table rows, orphaned headings, blank pages, and poor reading order.
3. Run `pdftotext resume-review.pdf -` and confirm the full report and every `[VERIFY]` token survived.
4. Read the page count from `pdfinfo resume-review.pdf` or the renderer output.
5. Run `pdffonts resume-review.pdf` when available and check that intended fonts are embedded.
6. Recheck the visual evidence rules and canonical status values.

Adjust spacing or add a justified page break if the layout fails. Do not alter the substance to force a page count. Report only the checks performed.
