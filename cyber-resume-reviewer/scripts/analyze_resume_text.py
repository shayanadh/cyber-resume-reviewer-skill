#!/usr/bin/env python3
"""Local UTF-8 text signals for IT/cyber resumes. Not a fit or ATS score."""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "4.0.0"
MAX_BYTES = 2 * 1024 * 1024
DATA = Path(__file__).resolve().parents[1] / "references" / "term-aliases.json"
HEADING_GROUPS = {
    "summary": ["summary", "professional summary", "profile", "professional profile", "objective", "career objective", "executive summary"],
    "skills": ["skills", "technical skills", "core competencies", "technical competencies", "technologies", "technical expertise", "areas of expertise"],
    "experience": ["experience", "professional experience", "work experience", "employment", "employment history", "career history", "military experience", "relevant experience"],
    "education": ["education", "education and training", "academic background"],
    "certifications": ["certifications", "certificates", "licenses and certifications", "certifications and training", "professional certifications", "certifications and education"],
    "projects": ["projects", "personal projects", "selected projects", "technical projects", "labs", "portfolio"],
    "community": ["volunteer", "volunteer experience", "community", "community involvement", "publications", "speaking", "presentations", "awards"],
    "other": ["clearance", "languages", "interests", "additional information", "training", "professional development"],
}
HEADINGS = {name: group for group, names in HEADING_GROUPS.items() for name in names}
BULLET = re.compile(r"^\s*(?:[-*+•◦▪●]|\d+[.)])\s+(.+)$")
VERBS = set("administer administers administered analyze analyzes analyzed automate automates automated build builds built configure configures configured contain contains contained coordinate coordinates coordinated create creates created deploy deploys deployed design designs designed develop develops developed document documents documented escalate escalates escalated implement implements implemented investigate investigates investigated lead leads led maintain maintains maintained manage manages managed monitor monitors monitored operate operates operated support supports supported test tests tested troubleshoot troubleshoots troubleshot validate validates validated write writes wrote run runs ran reduce reduces reduced restore restores restored advise advises advised mentor mentors mentored patch patches patched harden hardens hardened".split())
PHRASES = ["responsible for", "worked on", "worked with", "helped with", "proven track record", "results-driven", "passionate", "various", "etc."]
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
DATE_TOKEN = rf"(?:{MONTH}\s+(?:19|20)\d{{2}}|(?:0?[1-9]|1[0-2])[/.-](?:19|20)\d{{2}}|(?:19|20)\d{{2}})"
DATE_RANGE = re.compile(rf"(?<![\w/])(?P<start>{DATE_TOKEN})\s*(?:to|[-–—])\s*(?P<end>{DATE_TOKEN}|Present|Current|Now)(?![\w/])", re.I)
MONTHS = {name: index for index, name in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
# Strip identifiers/versions before looking for measurable quantities.
NON_METRIC = re.compile(r"\b(?:SOC\s*2(?:\s*Type\s*(?:I{1,2}|[12]))?|ISO(?:/IEC)?\s*270\d{2}(?::\d{4})?|NIST(?:\s+SP)?\s*800[- ]\d+(?:\s+Rev\.?\s*\d+)?|CVE[- ]\d{4}[- ]\d+|T\d{4}(?:\.\d{3})?|Windows\s+(?:Server\s+)?\d+(?:\s*R2)?|Python\s+\d+(?:\.\d+)*|PCI\s+DSS\s+\d+(?:\.\d+)*|TLS\s+\d+(?:\.\d+)*|(?:IPv|v)\d+(?:\.\d+)*)\b", re.I)
QUANTITY = re.compile(r"(?:[$€£]\s*\d[\d,.]*(?:\s*[kmb])?\b|\b\d[\d,.]*\s*(?:%|percent\b)|\b\d[\d,.]*\s*(?:(?:unsupported|managed|critical|eligible|production|virtual|physical|cloud|active|privileged|high-risk|overdue)\s+){0,2}(?:milliseconds?|seconds?|minutes?|hours?|days?|weeks?|months?|years?|endpoints?|assets?|servers?|users?|identities|accounts?|subscriptions?|applications?|apps?|systems?|devices?|sites?|teams?|people|engineers?|reports?|tickets?|alerts?|incidents?|rules?|findings?|vulnerabilities|controls?|vendors?|clients?|countries|business units|FTEs?)\b)", re.I)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.translate(str.maketrans({"–": "-", "—": "-", "‑": "-", "−": "-"}))
    return re.sub(r"\s+", " ", value).strip()


def phrase_pattern(value: str) -> re.Pattern:
    # Do not match C in C++, SSO in an unrelated token, or .NET in ASP.NET.
    return re.compile(r"(?<![\w+#.])" + re.escape(normalize(value)).replace(r"\ ", r"\s+") + r"(?![\w+#])")


def heading(line: str):
    value = re.sub(r"^\s*#{1,6}\s+", "", line.strip())
    value = value.strip("*_ ").rstrip(":").strip().strip("*_ ").casefold().replace(" & ", " and ")
    return HEADINGS.get(value)


def lines_with_sections(text: str):
    section = "unclassified"
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        group = heading(line)
        if group:
            section = group
        result.append({"line": number, "text": line, "section": section, "heading": bool(group)})
    return result


def extract_bullets(lines):
    result = []
    active = None
    for item in lines:
        line = item["text"]
        match = BULLET.match(line)
        if item["heading"] or not line.strip():
            active = None
        elif match:
            active = {"line_start": item["line"], "line_end": item["line"], "section": item["section"], "text": match.group(1).strip()}
            result.append(active)
        elif active and line[:1].isspace():
            active["text"] += " " + line.strip()
            active["line_end"] = item["line"]
        else:
            active = None
    return result


def bullet_signals(lines, include_excerpts=False):
    records = []
    for bullet in extract_bullets(lines):
        body = bullet["text"]
        stripped = NON_METRIC.sub(" ", body)
        first = re.sub(r"^[*_]+", "", body).split(maxsplit=1)[0].casefold().strip("*:,")
        normalized = normalize(body)
        record = {k: v for k, v in bullet.items() if k != "text"}
        record.update({"word_count": len(body.split()), "has_digit": bool(re.search(r"\d", body)),
                       "quantity_candidate_count": len(list(QUANTITY.finditer(stripped))),
                       "starts_with_action_verb": first in VERBS,
                       "phrases_to_review": [p for p in PHRASES if phrase_pattern(p).search(normalized)]})
        if include_excerpts:
            record["text"] = body
        records.append(record)
    count = len(records)
    return {"bullet_count": count,
            "with_digits": sum(r["has_digit"] for r in records),
            "with_quantity_candidates": sum(r["quantity_candidate_count"] > 0 for r in records),
            "with_action_verbs": sum(r["starts_with_action_verb"] for r in records),
            "over_45_words": sum(r["word_count"] > 45 for r in records),
            "average_word_count": round(sum(r["word_count"] for r in records) / count, 1) if count else 0,
            "items": records}


def date_interval(value):
    value = value.casefold().strip()
    if value in {"present", "current", "now"}:
        return None, None, "ongoing"
    year = int(re.search(r"(?:19|20)\d{2}", value).group())
    if re.fullmatch(r"\d{4}", value):
        return year * 12 + 1, year * 12 + 12, "year"
    month = int(re.match(r"\d{1,2}", value).group()) if value[0].isdigit() else MONTHS[value[:3]]
    return year * 12 + month, year * 12 + month, "month"


def date_signals(text, include_excerpts=False):
    items = []
    for match in DATE_RANGE.finditer(text):
        start_min, _, start_precision = date_interval(match["start"])
        _, end_max, end_precision = date_interval(match["end"])
        item = {"line": text.count("\n", 0, match.start()) + 1,
                "start_precision": start_precision, "end_precision": end_precision,
                "ongoing": end_precision == "ongoing",
                "reversed_range_candidate": end_max is not None and end_max < start_min}
        if include_excerpts:
            item["text"] = match.group()
        items.append(item)
    return {"range_count": len(items), "reversed_range_candidates": sum(x["reversed_range_candidate"] for x in items), "items": items}


def contact_signals(text):
    # Presence only. Exclude a ten-digit span manufactured from date ranges.
    phone_candidates = re.findall(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\(?\d{2,4}\)?[ .-]){1,4}\d{3,4}(?!\w)", text)
    phones = [p for p in phone_candidates if 7 <= len(re.sub(r"\D", "", p)) <= 15 and not DATE_RANGE.search(p)]
    return {"email": bool(re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)),
            "phone_candidate": bool(phones),
            "linkedin": bool(re.search(r"\blinkedin\.com/", text, re.I)),
            "github": bool(re.search(r"\bgithub\.com/", text, re.I)),
            "web_link": bool(re.search(r"https?://\S+", text, re.I))}


def load_terms():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return data["terms"]


def term_mentions(lines, terms):
    results = []
    for term, aliases in sorted(terms.items()):
        patterns = [(alias, phrase_pattern(alias)) for alias in aliases]
        for line in lines:
            if line["heading"]:
                continue
            value = normalize(line["text"])
            matches = [(alias, m) for alias, pattern in patterns for m in pattern.finditer(value)]
            if term == "Active Directory":
                # The renamed cloud directory is not on-premises Active Directory.
                matches = [(alias, m) for alias, m in matches
                           if not re.search(r"\bazure\s+$", value[:m.start()])]
            if not matches:
                continue
            # One canonical occurrence per line; lexical presence is never mastery.
            cues = []
            if re.search(r"\b(?:no|not|never|without|lack|lacks|lacking)\b", value):
                cues.append("possible_negation")
            if re.search(r"\b(?:learn|learning|studying|study|course|coursework|planned|pursuing|lab|labs|personal project)\b", value):
                cues.append("possible_learning_or_lab_context")
            results.append({"term": term, "matched_aliases": sorted({a for a, _ in matches}),
                            "line": line["line"], "section": line["section"], "context_flags": cues})
    return results


def analyze(resume, jd="", target_title="", include_excerpts=False):
    lines = lines_with_sections(resume)
    jd_lines = lines_with_sections(jd)
    terms = load_terms()
    resume_mentions, jd_mentions = term_mentions(lines, terms), term_mentions(jd_lines, terms)
    resume_terms = {x["term"] for x in resume_mentions}
    jd_terms = {x["term"] for x in jd_mentions}
    skills_terms = {x["term"] for x in resume_mentions if x["section"] == "skills"}
    body_terms = {x["term"] for x in resume_mentions if x["section"] not in {"skills", "unclassified", "summary"}}
    ambiguous = []
    for item in lines:
        for token in ["SOC", "VM", "IR", "CISA", "AD", "SLA"]:
            if re.search(r"(?<!\w)" + token + r"(?!\w)", item["text"], re.I):
                ambiguous.append({"token": token, "line": item["line"], "note": "Resolve meaning and relevance from context; no automatic expansion."})
    return {
        "analysis_version": VERSION,
        "target_title": target_title,
        "input": {"resume_characters": len(resume), "resume_words": len(resume.split()), "resume_lines": len(lines), "jd_supplied": bool(jd.strip()), "input_kind": "text", "original_file_layout": "not_assessed", "page_count": None},
        "contact_presence": contact_signals(resume),
        "sections": [{"line": x["line"], "category": x["section"]} for x in lines if x["heading"]],
        "section_presence": {group: any(x["heading"] and x["section"] == group for x in lines) for group in HEADING_GROUPS},
        "dates": date_signals(resume, include_excerpts),
        "bullets": bullet_signals(lines, include_excerpts),
        "terms": {"resume_mentions": resume_mentions, "jd_mentions": jd_mentions,
                  "jd_terms_with_resume_mentions": sorted(jd_terms & resume_terms),
                  "jd_terms_without_resume_mentions": sorted(jd_terms - resume_terms),
                  "skills_only_terms": sorted(skills_terms - body_terms),
                  "skills_terms_mentioned_elsewhere": sorted(skills_terms & body_terms),
                  "ambiguous_acronym_mentions": ambiguous},
        "text_format_hints": {"lines_with_interior_spacing": sum(bool(re.search(r"\S(?: {4,}|\t+)\S", x["text"])) for x in lines),
                              "lines_with_graphical_ratings": sum(bool(re.search(r"[▁▂▃▄▅▆▇█]{2,}", x["text"])) for x in lines),
                              "unicode_replacement_characters": resume.count("\ufffd")},
        "limitations": ["Local text signals only; no ATS acceptance, fit score, hiring prediction, or original-file page/layout assessment.",
                        "Term vocabulary is bounded; lexical mentions and quantity candidates require manual context review.",
                        "Date ranges are not job records. Custom headings and unindented wrapped bullets may be missed.",
                        "Context flags are line-level hints, not reliable negation or experience classification."]
    }


def read_text(path):
    source = Path(path)
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("input exceeds the 2 MiB text limit")
    raw = source.read_bytes()
    if raw.startswith((b"%PDF", b"PK\x03\x04", b"\x89PNG")) or b"\x00" in raw:
        raise ValueError("input must be extracted UTF-8 text, not a document or binary file")
    return raw.decode("utf-8-sig")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", required=True, help="UTF-8 resume text path")
    parser.add_argument("--jd", help="Optional UTF-8 job description path")
    parser.add_argument("--target-title", default="")
    parser.add_argument("--include-excerpts", action="store_true", help="Include private bullet/date excerpts in JSON")
    args = parser.parse_args(argv)
    try:
        resume = read_text(args.resume)
        jd = read_text(args.jd) if args.jd else ""
        if not resume.strip():
            raise ValueError("resume text is empty")
        result = analyze(resume, jd, args.target_title, args.include_excerpts)
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
