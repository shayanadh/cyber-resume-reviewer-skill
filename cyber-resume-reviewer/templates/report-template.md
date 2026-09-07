# Standard review structure

Use these sections selectively; a default review should not repeat the same findings in several tables. Replace template prompts with actual evidence or omit them.

For a file deliverable, add only the useful YAML metadata described in [report rendering](../references/report-rendering.md). Do not leave template placeholders in the final report.

## Assessment

Give the target, the main conclusion about the document, its strongest relevant evidence, and the highest-impact edit. State confirmed blockers separately from material risks and unknowns. Include content/target/format limitations as needed.

## Prioritized findings and exact edits

Use one block per material finding. Number high-priority findings `H1`, `H2`; medium findings `M1`, `M2`; and optional findings `O1`, `O2`.

**H1 - Short, specific finding title**

State the source location, observation, impact, and action. Keep them concise.

> *Original:* Exact current wording.

> *Supported replacement:* Ready-to-use wording built from known facts only.

**Ask:** Include one evidence question only when its answer could improve the edit.

For an incomplete draft, use this label and include a specific token:

> *Fill-in draft - INCOMPLETE, DO NOT SEND AS-IS:* Text with [VERIFY: missing fact].

Use Critical only for a confirmed submission blocker or a known factual error that must be corrected. Quote accurately; label paraphrases and combined excerpts.

## Target fit (when a target exists)

| JD requirement or labeled inference | Importance and timing | Candidate evidence/location | Evidence status | Next step |
|---|---|---|---|---|
| Preserve required/preferred and alternatives | Mandatory / Core responsibility / Preferred / Inferred / Unclear | Source quote | Demonstrated / Claimed only / Adjacent / Not shown / Confirmed unmet / Unknown | Specific action |

Add keyword placement only where it leads to a truthful, useful change. Do not duplicate the entire JD.

## First impression and format

Describe what is visible or what the supplied opening text establishes. Identify one useful ordering change. State original-file extraction and rendered-layout checks performed; mark unavailable checks unassessed.

## Diagnostic score (optional)

| Category ID and name | Weight | Rating 0–5 or Not assessed | Points | Evidence/reason |
|---|---:|---:|---:|---|
| Use the selected rubric profile | From profile | Integer or null | weight × rating / 5 | Source-specific rationale |

Report profile, total earned points, assessed weight, normalized score, and exclusions. Mark incomplete coverage provisional. Do not add letter grades or interview probabilities.

## Next actions

Give a short ordered list, preserving strong content as appropriate. Ask essential missing-fact questions first; distinguish optional stronger evidence. Add learning recommendations only for confirmed gaps, with current sources where relevant. A complete rewrite belongs here only when the user's request calls for it, and should take priority over report length.
