
import unittest
from unittest.mock import patch

from src.agent import agent, build_evidence_summary, generate_insights


MOCK_VALIDATION_REPORT = {
    "total_records": 2,
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


class TestAgentWorkflow(unittest.TestCase):

    def test_evidence_summary_uses_verified_python_counts(self):
        evidence = build_evidence_summary(MOCK_VALIDATION_REPORT)

        self.assertEqual(
            evidence["verified_totals"]["total_records"], 2
        )
        self.assertEqual(
            evidence["verified_totals"]["total_issues"], 1
        )
        self.assertEqual(
            evidence["verified_totals"]["affected_records"], 1
        )
        self.assertEqual(
            evidence["rule_evidence"][0]["rule"], "missing_value"
        )

    @patch("src.agent.chat")
    def test_ai_failure_uses_fallback(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Ollama unavailable")

        result = generate_insights(
            {"validation_report": MOCK_VALIDATION_REPORT}
        )

        self.assertEqual(result["ai_status"], "fallback")
        self.assertIn(
            "missing_value", result["ai_insights"]
        )
        self.assertIn(
            "human review", result["ai_insights"].lower()
        )
        self.assertIn("evidence_summary", result)

    @patch("src.agent.chat")
    def test_ai_success_returns_model_insights(self, mock_chat):
        mock_chat.return_value = {
            "message": {
                "content": (
                    "### Main data quality risks\n"
                    "The missing revenue value needs investigation."
                )
            }
        }

        result = generate_insights(
            {"validation_report": MOCK_VALIDATION_REPORT}
        )

        self.assertEqual(result["ai_status"], "success")
        self.assertIn(
            "needs investigation", result["ai_insights"]
        )

    @patch("src.agent.chat")
    def test_full_workflow_completes_when_ai_fails(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Ollama unavailable")

        result = agent.invoke({})

        self.assertEqual(result["ai_status"], "fallback")
        self.assertIn("validation_report", result)
        self.assertIn("evidence_summary", result)
        self.assertIn("final_report", result)
        self.assertIn(
            "Deterministic fallback",
            result["final_report"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
