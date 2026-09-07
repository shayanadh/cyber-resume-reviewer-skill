# Text analyzer contract

Run `python3 scripts/analyze_resume_text.py --resume resume.txt [--jd jd.txt] [--target-title "Title"]`. Python 3.9+; standard library only; no network or file writes. Input is UTF-8 text (BOM allowed), not PDF/DOCX bytes. Extract documents first. CLI errors return nonzero with a readable message. `--include-excerpts` optionally includes matched bullet/date text; leave it off when minimizing private content in logs.

Output version is `4.0.0`; this deliberately replaces the old heuristic JSON contract. It is **not** the structured review-report schema.

## What signals mean

- **Length:** actual character/word/line counts. No inferred page count or layout verdict.
- **Contact:** candidate email/phone/link presence only, not validity, reachability, ownership, or eligibility. International numbers are best-effort; unusual formatting can be missed.
- **Sections:** known plain/Markdown heading variants. Custom headings and extraction damage need manual review.
- **Dates:** non-overlapping range matches with precision and reversed-range candidates. No employment-duration calculation, overlap accusation, or claim that every role has dates.
- **Bullets:** recognized markers with indented continuation lines joined. Unindented extraction wraps may remain incomplete. Counts include bullets outside employment; interpret section labels. Present/past contribution verbs are signals, not merit ratings.
- **Numbers:** all-digit presence is separate from quantity candidates. Technology/version strings such as SOC 2, ISO 27001, Windows 11, CVE identifiers and ATT&CK technique IDs do not count as quantified results. Quantity candidates still require manual interpretation of scope versus outcome, units, baseline, and attribution.
- **Terms:** bounded, explicit aliases in `term-aliases.json`; no general semantic matching. No substring match inside unrelated words. Same-product renames are normalized; competitors are not interchangeable. Nearby negation/learning cues flag mentions for review, with possible false positives and false negatives.
- **Skills:** terms mentioned only in Skills versus elsewhere. A repeated mention is not proof; a skills-only mention is not dishonesty. Multiword phrases and slash-containing terms remain intact because matching uses the vocabulary, not comma/slash splitting.
- **Whitespace/glyphs:** formatting hints in text, not observations of the original document.

Every term occurrence has a source line and section. Resolve context in the source; do not mechanically add “missing” terms to a resume. The helper does not parse AND/OR requirements or determine mandatory status. It deliberately emits no ATS score, page estimate, qualification percentage, seniority judgment, or employment decision.
