
import os
from pathlib import Path
from typing import TypedDict, Any

import pandas as pd
from langgraph.graph import StateGraph, END

from src.validation import validate_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "agent_quality_report.md"


class AgentState(TypedDict, total=False):
    input_path: str
    validation_report: dict[str, Any]
    evidence_summary: dict[str, Any]
    ai_insights: str
    ai_status: str
    report_source: str
    final_report: str


def validate_data(state: AgentState) -> dict:
    """Validate the supplied CSV or the default dataset."""

    input_path = state.get("input_path")

    if input_path:
        report = validate_dataset(input_path)
    else:
        default_path = PROJECT_ROOT / "data" / "companies.csv"
        report = validate_dataset(default_path)

    return {"validation_report": report}


def build_evidence_summary(report: dict) -> dict:
    """Create a dataset-independent summary of validation findings."""

    issues = report.get("issues", [])
    severity_counts = report.get("issues_by_severity", {})
    rule_counts = report.get("issues_by_rule", {})

    findings_by_rule = {}

    for issue in issues:
        rule = issue.get("rule", "unknown")
        findings_by_rule.setdefault(rule, [])

        if len(findings_by_rule[rule]) < 5:
            findings_by_rule[rule].append({
                "record_id": issue.get("record_id"),
                "row_index": issue.get("row_index"),
                "column": issue.get("column"),
                "severity": issue.get("severity"),
                "message": issue.get("message"),
            })

    statistical_analysis = report.get("statistical_analysis", {})
    overview = statistical_analysis.get("dataset_overview", {})

    return {
        "dataset_name": report.get("dataset_name", "dataset.csv"),
        "total_records": report.get("total_records", 0),
        "total_columns": report.get("total_columns", 0),
        "total_issues": report.get("total_issues", 0),
        "affected_records": report.get("affected_records", 0),
        "issues_by_severity": severity_counts,
        "issues_by_rule": rule_counts,
        "dataset_overview": overview,
        "sample_findings_by_rule": findings_by_rule,
    }


def create_fallback_insights(
    report: dict,
    evidence: dict,
) -> str:
    """Generate useful insights without requiring an AI service."""

    total_records = report.get("total_records", 0)
    total_columns = report.get("total_columns", 0)
    total_issues = report.get("total_issues", 0)
    affected_records = report.get("affected_records", 0)

    severity = report.get("issues_by_severity", {})
    rules = report.get("issues_by_rule", {})

    statistical_analysis = report.get("statistical_analysis", {})
    overview = statistical_analysis.get("dataset_overview", {})

    missing_cells = overview.get("total_missing_cells", 0)
    duplicate_rows = overview.get("duplicate_row_count", 0)

    if total_issues == 0:
        quality_assessment = (
            "No issues were detected by the current validation rules. "
            "This does not guarantee that every value is correct or that "
            "all business requirements have been satisfied."
        )
    else:
        quality_assessment = (
            f"The validator detected {total_issues} findings affecting "
            f"{affected_records} records. Review the findings before "
            "using the dataset for reporting or downstream analysis."
        )

    lines = [
        "# AI-Powered Data Quality Report",
        "",
        "## 1. Dataset Overview",
        "",
        f"- **Dataset:** {report.get('dataset_name', 'dataset.csv')}",
        f"- **Records:** {total_records}",
        f"- **Columns:** {total_columns}",
        f"- **Detected findings:** {total_issues}",
        f"- **Affected records:** {affected_records}",
        f"- **Missing cells:** {missing_cells}",
        f"- **Duplicate rows:** {duplicate_rows}",
        "",
        "## 2. Quality Assessment",
        "",
        quality_assessment,
        "",
        "## 3. Findings by Severity",
        "",
    ]

    if severity:
        for level, count in severity.items():
            lines.append(f"- **{level}:** {count}")
    else:
        lines.append("- No findings were recorded.")

    lines.extend([
        "",
        "## 4. Findings by Rule",
        "",
    ])

    if rules:
        for rule, count in rules.items():
            lines.append(f"- **{rule}:** {count}")
    else:
        lines.append("- No rule violations were detected.")

    lines.extend([
        "",
        "## 5. Recommended Actions",
        "",
        "1. Investigate columns with a high percentage of missing values.",
        "2. Review duplicate records and confirm whether they are legitimate.",
        "3. Check unusual numeric values against the context of the dataset.",
        "4. Review constant columns to determine whether they are useful.",
        "5. Confirm the detected issues against the dataset's business rules.",
        "6. Re-run validation after correcting the identified problems.",
        "",
        "## 6. Limitations",
        "",
        "These findings are based on general-purpose data quality rules. "
        "The validator does not automatically know the meaning of every "
        "column, the expected value ranges, or the business rules governing "
        "the dataset. Statistical outliers are indicators for review, not "
        "proof of incorrect data.",
    ])

    return "\n".join(lines)


def generate_insights(state: AgentState) -> dict:
    """Generate AI insights when available, otherwise use fallback insights."""

    report = state.get("validation_report", {})
    evidence = build_evidence_summary(report)

    fallback_report = create_fallback_insights(report, evidence)

    api_key = os.getenv("OLLAMA_API_KEY")
    model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

    if not api_key:
        return {
            "evidence_summary": evidence,
            "ai_insights": fallback_report,
            "ai_status": "fallback",
            "report_source": "deterministic_fallback",
        }

    try:
        from ollama import Client

        client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        prompt = f"""
You are a data quality analyst reviewing an arbitrary CSV dataset.

Use only the evidence provided below. Do not invent column meanings,
business rules, causes, or findings. Clearly distinguish detected issues
from potential risks and recommendations.

Dataset evidence:
{evidence}

Write a concise Markdown report containing:
1. Executive summary
2. Main data quality concerns
3. Findings by severity and rule
4. Columns or patterns that deserve further investigation
5. Prioritized recommendations
6. Limitations and assumptions

Explain that statistical outliers are not necessarily errors.
If there are no detected issues, explain what the current checks cover
and what they do not guarantee.
"""

        response = client.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful, evidence-based data quality "
                        "analyst. Analyze any dataset without assuming "
                        "it contains company data. Never fabricate facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        insights = response["message"]["content"].strip()

        if not insights:
            raise ValueError("The AI service returned an empty response.")

        return {
            "evidence_summary": evidence,
            "ai_insights": insights,
            "ai_status": "success",
            "report_source": "ollama_cloud",
        }

    except Exception as exc:
        print(f"AI insight generation failed: {exc}")

        return {
            "evidence_summary": evidence,
            "ai_insights": fallback_report,
            "ai_status": "fallback",
            "report_source": "deterministic_fallback",
        }


def save_report(state: AgentState) -> dict:
    """Save the generated report as a Markdown file."""

    insights = state.get("ai_insights", "")
    evidence = state.get("evidence_summary", {})

    report_content = (
        f"{insights}\n\n"
        "---\n\n"
        "## Validation Metadata\n\n"
        f"- AI status: {state.get('ai_status', 'unknown')}\n"
        f"- Report source: {state.get('report_source', 'unknown')}\n"
        f"- Dataset: {evidence.get('dataset_name', 'dataset.csv')}\n"
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_content, encoding="utf-8")

    return {"final_report": report_content}


workflow = StateGraph(AgentState)

workflow.add_node("validate_data", validate_data)
workflow.add_node("generate_insights", generate_insights)
workflow.add_node("save_report", save_report)

workflow.set_entry_point("validate_data")
workflow.add_edge("validate_data", "generate_insights")
workflow.add_edge("generate_insights", "save_report")
workflow.add_edge("save_report", END)

agent = workflow.compile()
