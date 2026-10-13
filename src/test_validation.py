
import unittest

from validation import validate_companies


class TestCompanyValidation(unittest.TestCase):
    def test_validation_summary(self):
        report = validate_companies()

        self.assertEqual(report["total_records"], 15)
        self.assertEqual(report["total_issues"], 14)
        self.assertEqual(report["affected_records"], 13)

        self.assertIn("missing_value", report["issues_by_rule"])
        self.assertIn("invalid_country", report["issues_by_rule"])
        self.assertIn("negative_revenue", report["issues_by_rule"])
        self.assertIn("invalid_credit_score", report["issues_by_rule"])


if __name__ == "__main__":
    unittest.main()
