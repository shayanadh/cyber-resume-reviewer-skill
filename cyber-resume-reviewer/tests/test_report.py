import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import validate_report as validator


@unittest.skipUnless(importlib.util.find_spec('jsonschema'), 'Optional jsonschema dependency is not installed')
class ReportTests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((ROOT/'examples/example-report.json').read_text())

    def test_example_valid(self):
        self.assertEqual(validator.validate(self.report),[])

    def test_profiles_sum_to_100(self):
        for weights in validator.WEIGHTS.values(): self.assertEqual(sum(weights),100)

    def test_wrong_total_rejected(self):
        self.report['scorecard']['overall_score']=80
        self.assertTrue(validator.validate(self.report))

    def test_wrong_weights_rejected(self):
        self.report['scorecard']['rows'][1]['weight']=12
        self.assertTrue(validator.validate(self.report))

    def test_unassessed_not_zero(self):
        self.report['scorecard']['rows'][0]['points']=0
        self.assertTrue(validator.validate(self.report))

    def test_rating_bounds(self):
        self.report['scorecard']['rows'][1]['rating']=6
        self.assertTrue(validator.validate(self.report))

    def test_extra_properties_rejected(self):
        self.report['ats_pass_probability']=99
        self.assertTrue(validator.validate(self.report))

    def test_duplicate_categories_rejected(self):
        self.report['scorecard']['rows'][1]['category']='document'
        self.assertTrue(validator.validate(self.report))

    def test_clean_rewrite_cannot_have_unresolved_fact(self):
        self.report['rewritten_resume']={'text':'Managed [VERIFY: team size] people.','status':'clean','placeholders':[]}
        self.assertTrue(validator.validate(self.report))

    def test_placeholder_repetition_needs_each_occurrence(self):
        self.report['rewritten_resume']={'text':'[VERIFY: size]\n[VERIFY: size]','status':'incomplete','placeholders':[{'token':'[VERIFY: size]','location':'line 1','question_id':'Q1'}]}
        self.assertTrue(validator.validate(self.report))
        self.report['rewritten_resume']['placeholders'].append({'token':'[VERIFY: size]','location':'line 2','question_id':'Q1'})
        self.assertEqual(validator.validate(self.report),[])

    def test_supported_edit_needs_source(self):
        self.report['edits'][0]['source_refs']=[]
        self.assertTrue(validator.validate(self.report))

    def test_supported_edit_no_assumption_placeholders(self):
        self.report['edits'][0]['replacement_text']='Led [Assumed: enterprise response].'
        self.assertTrue(validator.validate(self.report))

    def test_unknown_question_reference_rejected(self):
        edit=self.report['edits'][0]
        edit['status']='needs_verification';edit['verification_question_ids']=['Q99']
        self.assertTrue(validator.validate(self.report))

    def test_all_unassessed(self):
        card=self.report['scorecard']
        for row in card['rows']: row['rating']=None;row['points']=None
        card.update(assessed_weight=0,overall_score=None,provisional=True)
        self.assertEqual(validator.validate(self.report),[])

    def test_scoring_optional(self):
        self.report['scorecard']=None
        self.assertEqual(validator.validate(self.report),[])


if __name__ == '__main__': unittest.main()
