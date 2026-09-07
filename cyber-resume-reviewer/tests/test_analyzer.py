import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_resume_text as analyzer


class AnalyzerTests(unittest.TestCase):
    def test_month_dates_not_double_counted(self):
        r = analyzer.date_signals('Jan 2020 - Present\n09/2018 - Dec 2019\n2015–2017')
        self.assertEqual(r['range_count'], 3)
        self.assertEqual(r['items'][0]['start_precision'], 'month')

    def test_reversed_ranges_but_not_concurrent_roles(self):
        r = analyzer.date_signals('2024-2021\n2020-Present\n2022-Present')
        self.assertEqual(r['reversed_range_candidates'], 1)

    def test_year_precision_remains_year(self):
        r = analyzer.date_signals('2018 - 2021')['items'][0]
        self.assertEqual((r['start_precision'], r['end_precision']), ('year', 'year'))

    def test_markdown_heading_stops_skills(self):
        r = analyzer.analyze('## Technical Skills\nPython, Terraform\n**Experience**\n- Built Python automation.\n## Education\nDegree')
        self.assertEqual(r['terms']['skills_only_terms'], ['Terraform'])
        self.assertIn('Python', r['terms']['skills_terms_mentioned_elsewhere'])

    def test_duplicate_skill_is_not_body_evidence(self):
        r = analyzer.analyze('Skills\nTerraform, Terraform\nEducation\nDegree')
        self.assertEqual(r['terms']['skills_only_terms'], ['Terraform'])

    def test_multiword_and_slash_terms(self):
        r = analyzer.analyze('Skills\nCI/CD, TCP/IP, C++, C#, .NET')
        names = {x['term'] for x in r['terms']['resume_mentions']}
        self.assertTrue({'CI/CD','TCP/IP','C++','C#','.NET'}.issubset(names))
        self.assertNotIn('C', names)

    def test_not_substrings(self):
        r = analyzer.analyze('Skills\nspamming drawers powershellish')
        self.assertEqual(r['terms']['resume_mentions'], [])

    def test_same_product_alias_matches(self):
        r = analyzer.analyze('Skills\nAzure AD', 'Microsoft Entra ID required')
        self.assertIn('Microsoft Entra ID',r['terms']['jd_terms_with_resume_mentions'])

    def test_azure_ad_does_not_prove_onprem_ad(self):
        r = analyzer.analyze('Skills\nAzure Active Directory')
        self.assertNotIn('Active Directory', {x['term'] for x in r['terms']['resume_mentions']})

    def test_different_products_not_equated(self):
        r = analyzer.analyze('Skills\nMicrosoft Sentinel', 'Splunk required')
        self.assertIn('Splunk', r['terms']['jd_terms_without_resume_mentions'])

    def test_both_directory_products_can_be_present(self):
        r = analyzer.analyze('Skills\nAzure Active Directory and Active Directory')
        names = {x['term'] for x in r['terms']['resume_mentions']}
        self.assertTrue({'Microsoft Entra ID', 'Active Directory'}.issubset(names))

    def test_negation_and_learning_flagged(self):
        r = analyzer.analyze('Skills\nNo Terraform experience.\nStudying Splunk in a lab.')
        mentions = {x['term']:x for x in r['terms']['resume_mentions']}
        self.assertIn('possible_negation', mentions['Terraform']['context_flags'])
        self.assertIn('possible_learning_or_lab_context', mentions['Splunk']['context_flags'])

    def test_versions_not_quantified_impact(self):
        r = analyzer.analyze('Experience\n- Reviewed SOC 2 Type II and ISO 27001 controls.\n- Patched Windows 11 for CVE-2025-12345.\n- Mapped T1059.001 and NIST SP 800-53 Rev. 5.')
        self.assertEqual(r['bullets']['with_digits'], 3)
        self.assertEqual(r['bullets']['with_quantity_candidates'], 0)

    def test_scope_and_outcome_are_candidates(self):
        r = analyzer.analyze('Experience\n- Administered 5,000 users.\n- Reduced preparation from 4 hours to 45 minutes.\n- Reduced alerts by 20%.')
        self.assertEqual(r['bullets']['with_quantity_candidates'], 3)

    def test_wrapped_bullet(self):
        r = analyzer.analyze('Experience\n- Automated reporting with Python\n  across 2,400 endpoints.\n- Supported recovery.',include_excerpts=True)
        self.assertEqual(r['bullets']['bullet_count'],2)
        self.assertEqual(r['bullets']['items'][0]['line_end'],3)
        self.assertIn('2,400 endpoints',r['bullets']['items'][0]['text'])

    def test_empty_bullet_shape_is_stable(self):
        a = analyzer.analyze('Summary\nIT professional')['bullets']
        b = analyzer.analyze('Experience\n- Supported recovery.')['bullets']
        self.assertEqual(set(a),set(b))
        self.assertEqual(a['average_word_count'],0)

    def test_contact_international_and_date_not_phone(self):
        self.assertTrue(analyzer.contact_signals('+44 20 7946 0958')['phone_candidate'])
        self.assertFalse(analyzer.contact_signals('2018-2021')['phone_candidate'])

    def test_no_page_guess_or_numeric_overlap(self):
        r = analyzer.analyze('A\n' * 300, 'Terraform')
        self.assertIsNone(r['input']['page_count'])
        self.assertEqual(r['input']['original_file_layout'],'not_assessed')
        self.assertFalse(any('ratio' in k or 'score' in k for k in r['terms']))

    def test_empty_jd(self):
        r = analyzer.analyze('Skills\nPython','  \n')
        self.assertFalse(r['input']['jd_supplied'])
        self.assertEqual(r['terms']['jd_terms_without_resume_mentions'],[])

    def test_excerpts_opt_in(self):
        text = 'Experience\n- Supported recovery for 100 users.'
        self.assertNotIn('text',analyzer.analyze(text)['bullets']['items'][0])
        self.assertIn('text',analyzer.analyze(text,include_excerpts=True)['bullets']['items'][0])

    def test_utf8_bom(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'resume.txt';p.write_bytes(b'\xef\xbb\xbfSkills\nPython')
            self.assertEqual(analyzer.read_text(p),'Skills\nPython')

    def test_reject_document_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            for raw in [b'%PDF-1.7 fake', b'PK\x03\x04fake', b'abc\x00def']:
                p=Path(d)/'resume.txt';p.write_bytes(raw)
                with self.assertRaises(ValueError): analyzer.read_text(p)

    def test_invalid_encoding_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'resume.txt';p.write_bytes(b'\xffinvalid')
            with self.assertRaises(UnicodeError): analyzer.read_text(p)

    def test_cli_empty_input_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'empty.txt';p.write_text(' ')
            r=subprocess.run([sys.executable,str(ROOT/'scripts/analyze_resume_text.py'),'--resume',str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            self.assertIn('resume text is empty',r.stderr)
            self.assertNotIn('Traceback',r.stderr)

    def test_sample_cli_is_json_and_read_only(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/analyze_resume_text.py'),'--resume',str(ROOT/'examples/sample-resume-redacted.txt'),'--jd',str(ROOT/'examples/sample-job-description-cloud-security.txt')],capture_output=True,text=True,check=True)
        output=json.loads(r.stdout)
        self.assertEqual(output['analysis_version'],'4.0.0')
        self.assertEqual(output['bullets']['bullet_count'],7)
        self.assertEqual(output['dates']['range_count'],2)
        self.assertEqual(output['bullets']['with_quantity_candidates'],2)


if __name__ == '__main__': unittest.main()
