import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_report as renderer


PARSER_READY = importlib.util.find_spec("yaml") and importlib.util.find_spec("bs4")
MARKDOWN_READY = importlib.util.find_spec("markdown") or shutil.which("pandoc")
PDF_READY = renderer.weasyprint_available() or shutil.which("wkhtmltopdf")


@unittest.skipUnless(PARSER_READY, "PDF parser dependencies are not installed")
class RendererUnitTests(unittest.TestCase):
    def test_front_matter_accepts_crlf(self):
        metadata, body = renderer.split_front_matter(
            "---\r\ncandidate: Candidate Name\r\nstatus: Not assessed\r\n---\r\n## Assessment\r\n"
        )
        self.assertEqual(metadata["candidate"], "Candidate Name")
        self.assertEqual(body, "## Assessment\n")

    def test_unknown_submission_status_rejected(self):
        with self.assertRaises(renderer.RenderError):
            renderer.split_front_matter("---\nstatus: Strong match\n---\nText\n")

    def test_metadata_is_html_escaped(self):
        output = renderer.masthead({"candidate": "Candidate <Name>"})
        self.assertIn("Candidate &lt;Name&gt;", output)
        self.assertNotIn("Candidate <Name>", output)

    def test_verify_token_cannot_be_supported_replacement(self):
        source = (
            "<blockquote><p><em>Supported replacement:</em> "
            "Led [VERIFY: team size] analysts.</p></blockquote>"
        )
        with self.assertRaises(renderer.RenderError):
            renderer.upgrade_html(source)

    def test_unlabeled_quote_stays_neutral(self):
        output = renderer.upgrade_html("<blockquote><p>Employer requirement.</p></blockquote>")
        self.assertIn("<blockquote>", output)
        self.assertNotIn('class="qb', output)

    def test_finding_with_trailing_text_is_not_truncated(self):
        source = "<p><strong>H1 - Finding</strong> Keep this sentence.</p>"
        output = renderer.upgrade_html(source)
        self.assertIn("Keep this sentence.", output)
        self.assertNotIn('class="fid"', output)

    def test_standalone_finding_header_is_upgraded(self):
        output = renderer.upgrade_html("<p><strong>H1 - Clarify scope</strong></p>")
        self.assertIn('class="fnd p-high"', output)
        self.assertIn('class="fid"', output)
        self.assertIn("Clarify scope", output)

    def test_supported_replacement_is_upgraded(self):
        source = (
            "<blockquote><p><em>Supported replacement:</em> "
            "Supported endpoint tools.</p></blockquote>"
        )
        output = renderer.upgrade_html(source)
        self.assertIn('class="qb repl"', output)
        self.assertIn("Supported endpoint tools.", output)

    def test_external_resources_and_inline_styles_are_removed(self):
        source = (
            '<style>@import url("https://invalid.example/style.css");</style>'
            '<link rel="stylesheet" href="https://invalid.example/other.css">'
            '<img src="https://invalid.example/image.png" alt="Image omitted">'
            '<p style="background:url(https://invalid.example/pixel)">Safe text.</p>'
        )
        output = renderer.upgrade_html(source)
        self.assertNotIn("invalid.example", output)
        self.assertNotIn("style=", output)
        self.assertIn("Image omitted", output)
        self.assertIn("Safe text.", output)


@unittest.skipUnless(
    PARSER_READY and MARKDOWN_READY and PDF_READY,
    "PDF rendering dependencies are not installed",
)
class RendererIntegrationTests(unittest.TestCase):
    def test_generic_report_renders_to_pdf(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "review.md"
            output = Path(temporary) / "review.pdf"
            source.write_text(
                (ROOT / "tests" / "fixtures" / "render-report.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            process = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "render_report.py"),
                    str(source),
                    str(output),
                    "--no-qa",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(output.read_bytes().startswith(b"%PDF"))
            if shutil.which("pdftotext"):
                extracted = subprocess.run(
                    ["pdftotext", str(output), "-"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                self.assertIn("Example Candidate", extracted)
                self.assertIn("Clarify operational scope", extracted)
                self.assertIn("The Markdown remains the source of truth", extracted)


if __name__ == "__main__":
    unittest.main()
