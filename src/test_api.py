
import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


VALID_CSV = b"""company_id,company_name,industry,country,revenue,employee_count,credit_score,annual_growth,registration_date,website
T001,Test Company,IT Services,US,1000000,25,80,10.0,2020-01-01,https://test.example
"""

INVALID_SCHEMA_CSV = b"""company_id,company_name
T001,Test Company
"""


MOCK_VALIDATION_REPORT = {
    "total_records": 1,
    "total_issues": 1,
    "affected_records": 1,
    "issues_by_severity": {"HIGH": 1},
    "issues_by_rule": {"missing_value": 1},
    "issues": [
        {
            "company_id": "T001",
            "rule": "missing_value",
            "severity": "HIGH",
            "message": "Required field 'revenue' is missing.",
        }
    ],
}


MOCK_EVIDENCE = {
    "verified_totals": {
        "total_records": 1,
        "total_issues": 1,
        "affected_records": 1,
    },
    "verified_severity_breakdown": {"HIGH": 1},
    "verified_rule_breakdown": {"missing_value": 1},
    "rule_evidence": [
        {
            "rule": "missing_value",
            "finding_count": 1,
            "severity_breakdown": {"HIGH": 1},
            "evidence": [
                {
                    "company_id": "T001",
                    "severity": "HIGH",
                    "message": "Required field 'revenue' is missing.",
                }
            ],
            "additional_findings_omitted": 0,
        }
    ],
}


def make_mock_result(ai_status):
    return {
        "final_report": "# Test quality report",
        "ai_status": ai_status,
        "evidence_summary": MOCK_EVIDENCE,
        "validation_report": MOCK_VALIDATION_REPORT,
    }


class TestDataQualityAPI(unittest.TestCase):

    def test_health_endpoint(self):
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)

    @patch("src.api.agent.invoke")
    def test_upload_csv_success(self, mock_invoke):
        mock_invoke.return_value = make_mock_result("success")

        response = client.post(
            "/upload-csv",
            files={
                "file": (
                    "test.csv",
                    io.BytesIO(VALID_CSV),
                    "text/csv",
                )
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["ai_status"], "success")
        self.assertEqual(data["summary"]["total_records"], 1)
        self.assertEqual(data["summary"]["total_issues"], 1)
        self.assertEqual(data["summary"]["affected_records"], 1)
        self.assertEqual(len(data["issues"]), 1)
        self.assertIn("missing_value", data["evidence"]["verified_rule_breakdown"])
        self.assertEqual(data["report"], "# Test quality report")

        mock_invoke.assert_called_once()

    @patch("src.api.agent.invoke")
    def test_upload_reports_ai_fallback(self, mock_invoke):
        mock_invoke.return_value = make_mock_result("fallback")

        response = client.post(
            "/upload-csv",
            files={
                "file": (
                    "test.csv",
                    io.BytesIO(VALID_CSV),
                    "text/csv",
                )
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["ai_status"], "fallback")
        self.assertEqual(data["summary"]["total_issues"], 1)
        self.assertEqual(len(data["issues"]), 1)
        self.assertTrue(data["evidence"]["rule_evidence"])

    @patch("src.api.agent.invoke")
    def test_upload_reports_ai_success(self, mock_invoke):
        mock_invoke.return_value = make_mock_result("success")

        response = client.post(
            "/upload-csv",
            files={
                "file": (
                    "test.csv",
                    io.BytesIO(VALID_CSV),
                    "text/csv",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ai_status"], "success")

    def test_upload_rejects_non_csv(self):
        response = client.post(
            "/upload-csv",
            files={
                "file": (
                    "test.txt",
                    io.BytesIO(b"not a csv"),
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_missing_columns(self):
        response = client.post(
            "/upload-csv",
            files={
                "file": (
                    "invalid.csv",
                    io.BytesIO(INVALID_SCHEMA_CSV),
                    "text/csv",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "missing_columns",
            str(response.json()["detail"]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
