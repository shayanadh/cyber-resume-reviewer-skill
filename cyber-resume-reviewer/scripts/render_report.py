#!/usr/bin/env python3
"""Render a resume-review Markdown file as a styled, paginated PDF.

Usage:
    python3 scripts/render_report.py /path/to/review.md /path/to/resume-review.pdf

The Markdown remains the source of truth. See references/report-rendering.md for
the supported conventions and the required visual checks.
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    BeautifulSoup = None


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSS = SKILL_ROOT / "assets" / "report.css"

SUBMISSION_STATUSES = {
    "Ready for candidate review",
    "Targeted edits needed",
    "More evidence needed",
    "Submission blocked",
    "Not assessed",
}
STATUS_SLUGS = {
    "Ready for candidate review": "s-ready",
    "Submission blocked": "s-blocked",
    "Not assessed": "s-notassessed",
}
EVIDENCE_STATUSES = {
    "demonstrated": "st-demonstrated",
    "claimed only": "st-claimed",
    "adjacent": "st-adjacent",
    "not shown": "st-notshown",
    "confirmed unmet": "st-unmet",
    "unknown": "st-unknown",
}

ICONS = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "alert": '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13.4"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4"/>',
    "scan": '<path d="M3 8V5a2 2 0 0 1 2-2h3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M21 16v3a2 2 0 0 1-2 2h-3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><line x1="3.5" y1="12" x2="20.5" y2="12"/>',
    "steps": '<line x1="9" y1="6" x2="21" y2="6"/><line x1="9" y1="12" x2="21" y2="12"/><line x1="9" y1="18" x2="21" y2="18"/><circle cx="4" cy="6" r="1.4"/><circle cx="4" cy="12" r="1.4"/><circle cx="4" cy="18" r="1.4"/>',
    "lock": '<rect x="4" y="10.5" width="16" height="10.5" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>',
    "ask": '<circle cx="12" cy="12" r="9.2"/><path d="M9.2 9.2a2.9 2.9 0 0 1 5.6 1c0 1.9-2.8 2.4-2.8 2.4"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "book": '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22.5z"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/>',
}
SECTION_ICONS = (
    (r"assess|verdict|summary", "shield"),
    (r"finding|edit|issue", "alert"),
    (r"target|fit|role", "target"),
    (r"impression|format|parse|layout", "scan"),
    (r"next action|action|step|plan", "steps"),
    (r"preserve|strength|keep", "lock"),
    (r"question|appendix|ask", "ask"),
    (r"check|verif", "check"),
)


class RenderError(Exception):
    """A user-correctable rendering error."""


def require_parser_dependencies() -> None:
    missing = []
    if yaml is None:
        missing.append("PyYAML")
    if BeautifulSoup is None:
        missing.append("beautifulsoup4")
    if missing:
        joined = ", ".join(missing)
        raise RenderError(
            f"missing Python package(s): {joined}. Install scripts/report-requirements.txt "
            "or use the host's PDF-generation capability"
        )


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    normalized = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    match = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", normalized, re.DOTALL)
    if not match:
        return {}, normalized
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except Exception as exc:
        raise RenderError(f"invalid YAML front matter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise RenderError("YAML front matter must be a mapping")
    validate_metadata(metadata)
    return metadata, normalized[match.end() :].lstrip("\n")


def validate_metadata(metadata: dict[str, Any]) -> None:
    for key in (
        "candidate",
        "header_name",
        "subtitle",
        "reviewed",
        "source_file",
        "source_note",
        "status",
        "status_note",
        "footer_note",
    ):
        if key in metadata and metadata[key] is not None and not isinstance(metadata[key], str):
            raise RenderError(f"front-matter field '{key}' must be text")

    status = metadata.get("status")
    if status and status not in SUBMISSION_STATUSES:
        allowed = ", ".join(sorted(SUBMISSION_STATUSES))
        raise RenderError(f"unknown submission status '{status}'. Use one of: {allowed}")

    for key, fields in (
        ("targets", ("label", "value")),
        ("chips", ("title", "body")),
        ("impacts", ("label", "body")),
    ):
        value = metadata.get(key, [])
        if value is None:
            continue
        if not isinstance(value, list):
            raise RenderError(f"front-matter field '{key}' must be a list")
        for index, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                raise RenderError(f"{key} item {index} must be a mapping")
            for field in fields:
                if field in item and item[field] is not None and not isinstance(item[field], str):
                    raise RenderError(f"{key} item {index} field '{field}' must be text")


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown as markdown_module
    except ModuleNotFoundError:
        markdown_module = None

    if markdown_module is not None:
        return markdown_module.markdown(
            markdown_text,
            extensions=["tables", "attr_list", "fenced_code", "sane_lists", "md_in_html"],
            output_format="html5",
        )

    pandoc = shutil.which("pandoc")
    if pandoc:
        process = subprocess.run(
            [pandoc, "--from", "gfm", "--to", "html5"],
            input=markdown_text,
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode == 0:
            return process.stdout
        raise RenderError(f"pandoc could not convert the Markdown: {process.stderr.strip()}")

    raise RenderError(
        "no Markdown engine found. Install the Python 'Markdown' package or install pandoc"
    )


def svg(key: str, colour: str = "#1D3557", size: int = 16, css_class: str = "ic") -> str:
    return (
        f'<svg class="{css_class}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{colour}" stroke-width="1.9" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{ICONS[key]}</svg>'
    )


def pick_icon(title: str) -> str:
    lowered = title.lower()
    for pattern, name in SECTION_ICONS:
        if re.search(pattern, lowered):
            return name
    return "book"


def sanitize_html(soup: Any) -> None:
    blocked_tags = (
        "audio",
        "base",
        "button",
        "embed",
        "form",
        "frame",
        "frameset",
        "iframe",
        "image",
        "input",
        "link",
        "meta",
        "object",
        "picture",
        "script",
        "source",
        "style",
        "svg",
        "track",
        "video",
    )
    for tag in soup.find_all(blocked_tags):
        tag.decompose()
    for tag in soup.find_all(True):
        for attribute in list(tag.attrs):
            if attribute.lower().startswith("on") or attribute.lower() in {
                "background",
                "ping",
                "poster",
                "srcset",
                "style",
            }:
                del tag.attrs[attribute]
        if tag.name == "img":
            source = str(tag.get("src", ""))
            if not source.startswith("data:image/"):
                replacement = soup.new_tag("span")
                replacement.string = tag.get("alt") or "[image omitted from PDF]"
                tag.replace_with(replacement)


def add_verify_tokens(soup: Any) -> None:
    token = re.compile(r"\[VERIFY:[^\]]*\]")
    for node in list(soup.find_all(string=token)):
        text = str(node)
        cursor = 0
        replacements = []
        for match in token.finditer(text):
            if match.start() > cursor:
                replacements.append(text[cursor : match.start()])
            span = soup.new_tag("span")
            span["class"] = "vf"
            span.string = match.group(0)
            replacements.append(span)
            cursor = match.end()
        if cursor < len(text):
            replacements.append(text[cursor:])
        node.replace_with(*replacements)


def upgrade_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    sanitize_html(soup)

    for number, heading in enumerate(list(soup.find_all("h2")), start=1):
        title = heading.get_text(" ", strip=True)
        wrapper = soup.new_tag("div")
        wrapper["class"] = "sec-head keep"
        badge = soup.new_tag("span")
        badge["class"] = "sec-num"
        badge.string = str(number)
        icon = BeautifulSoup(
            f'<span class="sec-ic">{svg(pick_icon(title), size=17)}</span>', "html.parser"
        )
        new_heading = soup.new_tag("h2")
        new_heading.string = title
        wrapper.append(badge)
        wrapper.append(icon)
        wrapper.append(new_heading)
        heading.replace_with(wrapper)

    for heading in soup.find_all("h3"):
        heading["class"] = list(heading.get("class", [])) + ["sub"]

    finding_pattern = re.compile(r"^([HMO])(\d+)\s*[\u2014\u2013-]\s*(.+)$", re.DOTALL)
    for paragraph in list(soup.find_all("p")):
        first = paragraph.find(("strong", "b"), recursive=False)
        if first is None or first is not paragraph.contents[0]:
            continue
        if paragraph.get_text(" ", strip=True) != first.get_text(" ", strip=True):
            continue
        match = finding_pattern.match(first.get_text(" ", strip=True))
        if not match:
            continue
        letter, number, title = match.groups()
        priority = {"H": "high", "M": "med", "O": "opt"}[letter]
        finding = BeautifulSoup(
            f'<div class="fnd p-{priority}"><div class="fnd-head keep">'
            f'<span class="fid">{letter}{number}</span>'
            f'<span class="ftitle">{html_lib.escape(title.strip())}</span>'
            "</div></div>",
            "html.parser",
        )
        paragraph.replace_with(finding)

    for paragraph in list(soup.find_all("p")):
        text = paragraph.get_text(" ", strip=True).lower()
        if text not in {"high priority", "medium priority", "optional", "low priority"}:
            continue
        css_class = "t-high" if "high" in text else "t-med" if "medium" in text else "t-opt"
        tier = soup.new_tag("div")
        tier["class"] = f"tier {css_class}"
        tier.string = paragraph.get_text(" ", strip=True)
        paragraph.replace_with(tier)

    for quote in list(soup.find_all("blockquote")):
        lead = quote.find(("em", "strong", "i", "b"))
        if lead is None:
            continue
        label = lead.get_text(" ", strip=True).rstrip(":").strip()
        lowered = label.lower()
        if re.search(r"^original(?: text)?$|^current(?: text| wording)?$", lowered):
            kind = "orig"
        elif re.search(r"supported replacement|ready-to-use replacement|^replacement$|^use this$", lowered):
            kind = "repl"
        elif re.search(r"draft|verify|incomplete|fill.?in", lowered):
            kind = "draft"
        elif re.search(r"note|callout|recommendation", lowered):
            lead.decompose()
            inner = re.sub(r"^\s*(<p>)?\s*:?\s*", r"\1", quote.decode_contents(), count=1)
            callout = BeautifulSoup(
                f'<div class="callout navy"><span class="co-h">{svg("book", size=14)} '
                f"{html_lib.escape(label)}</span>{inner}</div>",
                "html.parser",
            )
            quote.replace_with(callout)
            continue
        else:
            continue

        lead.decompose()
        inner = re.sub(r"^\s*(<p>)?\s*:?\s*", r"\1", quote.decode_contents(), count=1)
        evidence = BeautifulSoup(
            f'<div class="qb {kind}"><div class="qlbl">{html_lib.escape(label.upper())}</div>'
            f'<div class="qtx">{inner}</div></div>',
            "html.parser",
        )
        quote.replace_with(evidence)

    for paragraph in list(soup.find_all("p")):
        first = paragraph.find(("strong", "b"), recursive=False)
        if first is None or first is not paragraph.contents[0]:
            continue
        label = first.get_text(" ", strip=True).rstrip(":").strip()
        if not re.fullmatch(r"ask(?: the candidate)?", label, re.IGNORECASE):
            continue
        first.decompose()
        body = re.sub(r"^\s*:?\s*", "", paragraph.decode_contents())
        callout = BeautifulSoup(
            f'<div class="ask keep"><span class="askic">{svg("ask", size=14)}</span>'
            f'<span class="asklbl">{html_lib.escape(label)}</span> {body}</div>',
            "html.parser",
        )
        paragraph.replace_with(callout)

    for table in soup.find_all("table"):
        headers = [cell.get_text(" ", strip=True).lower() for cell in table.find_all("th")]
        status_columns = [index for index, value in enumerate(headers) if "status" in value]
        if not status_columns:
            continue
        column = status_columns[0]
        table["class"] = list(table.get("class", [])) + ["fit"]
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) <= column:
                continue
            cell = cells[column]
            raw = cell.get_text("\n", strip=True)
            first_line, _, note = raw.partition("\n")
            css_class = EVIDENCE_STATUSES.get(first_line.strip().lower())
            if not css_class:
                continue
            cell.clear()
            status = soup.new_tag("span")
            status["class"] = f"st {css_class}"
            status.string = first_line.strip()
            cell.append(status)
            if note.strip():
                detail = soup.new_tag("span")
                detail["class"] = "st-sub"
                detail.string = note.strip()
                cell.append(detail)

    rendered = str(soup).replace("<!-- pagebreak -->", '<div class="pagebreak"></div>')
    final_soup = BeautifulSoup(rendered, "html.parser")
    add_verify_tokens(final_soup)
    if final_soup.select(".qb.repl .vf"):
        raise RenderError(
            "a supported-replacement block contains [VERIFY]. Mark it as an incomplete draft"
        )
    return str(final_soup)


def escaped(value: Any) -> str:
    return html_lib.escape(str(value), quote=True)


def masthead(metadata: dict[str, Any]) -> str:
    if not metadata:
        return ""

    candidate = metadata.get("candidate") or "Resume Review"
    parts = [
        '<div class="mast">',
        '<div class="eyebrow">IT &amp; Cybersecurity Resume Review &nbsp;·&nbsp; Confidential</div>',
        f"<h1>{escaped(candidate)}</h1>",
    ]
    if metadata.get("subtitle"):
        parts.append(f'<p class="sub">{escaped(metadata["subtitle"])}</p>')
    parts.append("</div>")

    cells: list[tuple[str, str, str | None]] = []
    if metadata.get("reviewed"):
        cells.append(("Reviewed", metadata["reviewed"], None))
    if metadata.get("source_file"):
        cells.append(("Source file", metadata["source_file"], metadata.get("source_note")))
    for target in metadata.get("targets") or []:
        cells.append((target.get("label") or "Target", target.get("value") or "", None))
    if cells:
        width = round(100 / len(cells), 4)
        rendered_cells = []
        for label, value, note in cells:
            note_html = f'<br><span class="mnote">{escaped(note)}</span>' if note else ""
            rendered_cells.append(
                f'<td style="width:{width}%"><span class="mlbl">{escaped(label)}</span>'
                f'<span class="mval">{escaped(value)}{note_html}</span></td>'
            )
        parts.append(f'<table class="meta"><tr>{"".join(rendered_cells)}</tr></table>')

    chips = metadata.get("chips") or []
    impacts = metadata.get("impacts") or []
    if metadata.get("status") or chips or impacts:
        panel = ['<div class="glance">']
        if metadata.get("status"):
            status = metadata["status"]
            slug = STATUS_SLUGS.get(status, "")
            note = (
                f'<span class="status-note">{escaped(metadata["status_note"])}</span>'
                if metadata.get("status_note")
                else ""
            )
            panel.append(
                f'<div class="glance-top"><span class="status {slug}">{escaped(status)}</span>'
                f"{note}</div>"
            )
        if chips:
            width = round(100 / len(chips), 4)
            rendered_chips = "".join(
                f'<td style="width:{width}%"><div class="chip-h">'
                f'{svg("alert", "#A81F14", 13)} {escaped(item.get("title", ""))}</div>'
                f'<div class="chip-b">{escaped(item.get("body", ""))}</div></td>'
                for item in chips
            )
            panel.append(f'<table class="chips"><tr>{rendered_chips}</tr></table>')
        if impacts:
            width = round(100 / len(impacts), 4)
            rendered_impacts = "".join(
                f'<td style="width:{width}%"><span class="imp-l">'
                f'{escaped(item.get("label", ""))}</span><span class="imp-t">'
                f'{escaped(item.get("body", ""))}</span></td>'
                for item in impacts
            )
            panel.append(f'<table class="impact"><tr>{rendered_impacts}</tr></table>')
        panel.append("</div>")
        parts.append("".join(panel))
    return "".join(parts)


def css_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def weasyprint_page_css(metadata: dict[str, Any]) -> str:
    candidate = metadata.get("header_name") or metadata.get("candidate") or ""
    footer = metadata.get("footer_note") or "Confidential"
    return f"""
    @page {{
      size: Letter;
      margin: 16mm 17mm 18mm;
      @top-left {{
        content: "IT & CYBERSECURITY RESUME REVIEW";
        font-family: "DejaVu Sans Mono"; font-size: 6.4pt; color: #7a8492;
      }}
      @top-right {{
        content: "{css_string(str(candidate))}";
        font-family: "DejaVu Sans Mono"; font-size: 6.4pt; color: #7a8492;
      }}
      @bottom-left {{
        content: "Resume Review · {css_string(str(candidate))}";
        font-family: Poppins, "DejaVu Sans"; font-size: 7.2pt; color: #66717f;
      }}
      @bottom-center {{
        content: "{css_string(str(footer))}";
        font-family: Poppins, "DejaVu Sans"; font-size: 7pt; color: #9aa4b0;
      }}
      @bottom-right {{
        content: "Page " counter(page) " of " counter(pages);
        font-family: Poppins, "DejaVu Sans"; font-size: 7.2pt; color: #66717f;
      }}
    }}
    @page:first {{
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
    }}
    """


def make_document(body: str, metadata: dict[str, Any], css: str, extra_css: str = "") -> str:
    title = metadata.get("candidate") or "Resume Review"
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:">'
        f"<title>{escaped(title)}</title><style>{css}\n{extra_css}</style>"
        f"</head><body>{masthead(metadata)}{body}</body></html>"
    )


def render_with_weasyprint(document: str, output: Path) -> None:
    try:
        from weasyprint import HTML, default_url_fetcher
    except (ImportError, OSError) as exc:
        raise RenderError(f"WeasyPrint is unavailable: {exc}") from exc

    def embedded_image_fetcher(url: str, *args: Any, **kwargs: Any) -> Any:
        if url.startswith("data:image/"):
            return default_url_fetcher(url, *args, **kwargs)
        raise ValueError("external and local resources are disabled")

    try:
        HTML(string=document, url_fetcher=embedded_image_fetcher).write_pdf(str(output))
    except Exception as exc:
        raise RenderError(f"WeasyPrint could not create the PDF: {exc}") from exc


def render_with_wkhtmltopdf(document: str, output: Path, metadata: dict[str, Any]) -> None:
    executable = shutil.which("wkhtmltopdf")
    if not executable:
        raise RenderError("wkhtmltopdf is not installed")
    candidate = metadata.get("header_name") or metadata.get("candidate") or ""
    footer = metadata.get("footer_note") or "Confidential"
    with tempfile.TemporaryDirectory(prefix="resume-review-") as temporary:
        html_path = Path(temporary) / "review.html"
        html_path.write_text(document, encoding="utf-8")
        command = [
            executable,
            "--disable-javascript",
            "--disable-local-file-access",
            "--page-size",
            "Letter",
            "--encoding",
            "utf-8",
            "--dpi",
            "300",
            "--image-quality",
            "100",
            "--margin-top",
            "16mm",
            "--margin-bottom",
            "18mm",
            "--margin-left",
            "17mm",
            "--margin-right",
            "17mm",
            "--header-left",
            "IT & CYBERSECURITY RESUME REVIEW",
            "--header-right",
            str(candidate),
            "--header-font-size",
            "7",
            "--header-spacing",
            "4",
            "--footer-left",
            f"Resume Review · {candidate}",
            "--footer-center",
            str(footer),
            "--footer-right",
            "Page [page] of [topage]",
            "--footer-font-size",
            "7",
            "--footer-spacing",
            "4",
            str(html_path),
            str(output),
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0 or not output.exists():
        detail = (process.stderr or process.stdout or "no output was produced").strip()
        raise RenderError(f"wkhtmltopdf could not create the PDF: {detail}")
    if "not support using unpatched qt" in process.stderr.lower():
        sys.stderr.write(
            "note: this wkhtmltopdf build omitted running headers and footers; body styling is intact\n"
        )


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError):
        return False
    return True


def select_engine(requested: str) -> str:
    if requested == "weasyprint":
        if not weasyprint_available():
            raise RenderError("the requested WeasyPrint engine is unavailable")
        return requested
    if requested == "wkhtmltopdf":
        if not shutil.which("wkhtmltopdf"):
            raise RenderError("the requested wkhtmltopdf engine is unavailable")
        return requested
    if weasyprint_available():
        return "weasyprint"
    if shutil.which("wkhtmltopdf"):
        return "wkhtmltopdf"
    raise RenderError("no PDF engine found. Install WeasyPrint or wkhtmltopdf")


def page_count(pdf: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    process = subprocess.run([executable, str(pdf)], capture_output=True, text=True, check=False)
    match = re.search(r"^Pages:\s+(\d+)\s*$", process.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def render_qa_images(pdf: Path) -> Path | None:
    executable = shutil.which("pdftoppm")
    if not executable:
        return None
    qa_directory = pdf.parent / f"{pdf.stem}-qa"
    qa_directory.mkdir(parents=True, exist_ok=True)
    for old_image in qa_directory.glob("page-*.jpg"):
        old_image.unlink()
    process = subprocess.run(
        [executable, "-jpeg", "-r", "110", str(pdf), str(qa_directory / "page")],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RenderError(f"PDF created, but QA images failed: {process.stderr.strip()}")
    return qa_directory


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", help="source Markdown report")
    parser.add_argument("output", help="destination PDF")
    parser.add_argument("--css", default=str(DEFAULT_CSS), help="stylesheet path")
    parser.add_argument(
        "--engine",
        choices=("auto", "weasyprint", "wkhtmltopdf"),
        default="auto",
        help="PDF engine (default: auto)",
    )
    parser.add_argument("--keep-html", action="store_true", help="save the intermediate HTML")
    parser.add_argument("--no-qa", action="store_true", help="skip page-image generation")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_parser_dependencies()
    source = Path(args.markdown)
    output = Path(args.output)
    stylesheet = Path(args.css)
    if not source.is_file():
        raise RenderError(f"Markdown source not found: {source}")
    if not stylesheet.is_file():
        raise RenderError(f"stylesheet not found: {stylesheet}")
    if output.suffix.lower() != ".pdf":
        raise RenderError("output filename must end in .pdf")

    metadata, markdown_body = split_front_matter(source.read_text(encoding="utf-8-sig"))
    if metadata.get("candidate"):
        markdown_body = re.sub(r"\A\s*#\s+.*?(?:\n|\Z)", "", markdown_body, count=1)
    converted = markdown_to_html(markdown_body)
    upgraded = upgrade_html(converted)
    css = stylesheet.read_text(encoding="utf-8")
    engine = select_engine(args.engine)
    extra_css = weasyprint_page_css(metadata) if engine == "weasyprint" else ""
    document = make_document(upgraded, metadata, css, extra_css)

    output.parent.mkdir(parents=True, exist_ok=True)
    if engine == "weasyprint":
        render_with_weasyprint(document, output)
    else:
        render_with_wkhtmltopdf(document, output, metadata)

    if args.keep_html:
        output.with_suffix(".html").write_text(document, encoding="utf-8")
    qa_directory = None if args.no_qa else render_qa_images(output)
    pages = page_count(output)
    page_text = f", {pages} page{'s' if pages != 1 else ''}" if pages is not None else ""
    print(f"Created {output} with {engine}{page_text}.")
    if qa_directory:
        print(f"QA images: {qa_directory}/page-*.jpg. Inspect every page before delivery.")
    elif not args.no_qa:
        print("QA images were not created because pdftoppm is unavailable.")
    return 0


def main() -> int:
    try:
        return run()
    except (RenderError, OSError, UnicodeError) as exc:
        sys.stderr.write(f"render_report: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
