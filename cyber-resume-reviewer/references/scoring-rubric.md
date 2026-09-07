# Optional diagnostic scoring

Scores describe evidence in a resume for a stated target. They are editorial judgments, not a validated psychometric assessment, an ATS score, or an interview forecast. Omit scoring for quick reviews or rewrites unless asked. Use no letter grades or automatic caps.

## Categories and exact weight profiles

Each column totals 100. Select a profile and retain it across revisions of the same target. “Early career” changes evidence expectations; it does not mean certs are mandatory.

| ID | Category | Lens | General | Early career | Senior IC | Leadership | Advisory |
|---|---|---|---:|---:|---:|---:|---:|
| document | Original-file extractability | Machine-read | 10 | 10 | 10 | 10 | 10 |
| clarity | Content clarity and organization | Human-skim | 10 | 10 | 10 | 10 | 10 |
| positioning | Target positioning | Human-skim | 10 | 10 | 10 | 10 | 10 |
| fit | Core responsibility evidence | Human-believe | 20 | 20 | 20 | 20 | 20 |
| outcomes | Results and useful deliverables | Human-believe | 15 | 15 | 15 | 15 | 15 |
| depth | Technical or functional specificity | Human-believe | 15 | 15 | 20 | 10 | 10 |
| scope | Ownership and level calibration | Human-act | 10 | 5 | 10 | 20 | 15 |
| requirements | Stated qualification alignment | Human-act | 5 | 5 | 3 | 3 | 5 |
| development | Relevant learning / proof of work | Human-act | 5 | 10 | 2 | 2 | 5 |

Keep factual integrity as an unscored invariant. Do not penalize the same issue across multiple overlapping categories. In a hybrid role select the nearest profile, or disclose custom weights totaling 100. Do not award points for credentials irrelevant to the target.

## Anchors

| Rating | Observable evidence |
|---:|---|
| 0 | Applicable criterion has no evidence in the supplied document |
| 1 | Label or broad assertion only |
| 2 | Relevant task or partial evidence; significant specifics are unclear |
| 3 | Clear action, artifact, scope, or result adequate for the target |
| 4 | Strong examples showing depth, contribution, and meaningful results |
| 5 | Consistently specific evidence of relevant complexity, judgment, and results |

Use integer ratings. “Not assessed” is `null`, never zero. Mark document null for text-only sources; target-dependent categories null when there is no usable target. Mark development null when irrelevant. An ordinary responsibility with clear scope can earn credit without a percentage. Missing proof on the page does not prove inability.

## Calculation

For assessed rows: `points = weight * rating / 5`.

`assessed_weight = sum(weights of assessed rows)`

`overall_score = 100 * sum(points) / assessed_weight`

Round the final score to one decimal, not intermediate arithmetic. If no rows are assessed, score is null. Always disclose assessed weight and excluded categories. Mark the score **provisional** whenever coverage is below 100. Never compare scores with different targets, profiles, or assessed categories without explaining those differences.

Example: excluding a 10-point document category leaves 90 assessed points. If earned points are 63, report **70.0/100 on 90% assessed coverage**, not 63/100. The schema and validator enforce this arithmetic.

If stage subtotals are useful, compute them from the selected profile and assessed rows, rather than copying default denominators. Keep confirmed blockers in a separate status field; a strong content score does not resolve an unmet requirement.

## Submission status

Use `Ready for candidate review`, `Targeted edits needed`, `More evidence needed`, `Submission blocked`, or `Not assessed`. “Ready for candidate review” means the requested draft is internally complete from supplied facts, not that credentials were independently verified or an interview is likely.
