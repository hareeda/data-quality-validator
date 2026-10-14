
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from ollama import Client, chat as local_chat

from src.validation import validate_companies


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "agent_quality_report.md"

CLOUD_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
LOCAL_MODEL = os.getenv("OLLAMA_LOCAL_MODEL", "llama3.2:latest")


class AgentState(TypedDict, total=False):
    input_path: str
    validation_report: dict
    evidence_summary: dict
    ai_insights: str
    ai_status: str
    report_source: str
    final_report: str


def chat(*, model: str, messages: list, options: dict | None = None):
    """Use Ollama Cloud when configured; otherwise use local Ollama."""
    api_key = os.getenv("OLLAMA_API_KEY")

    if api_key:
        client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        return client.chat(
            model=model,
            messages=messages,
            options=options or {"temperature": 0.1},
        )

    return local_chat(
        model=LOCAL_MODEL,
        messages=messages,
        options=options or {"temperature": 0.1},
    )


def response_text(response) -> str:
    """Support both Ollama response objects and test/mock dictionaries."""
    if isinstance(response, dict):
        return response["message"]["content"].strip()

    return response.message.content.strip()


def validate_data(state: AgentState) -> dict:
    """Run deterministic validation on the supplied or default CSV."""
    input_path = state.get("input_path")
    report = validate_companies(input_path) if input_path else validate_companies()
    return {"validation_report": report}


def build_evidence_summary(report: dict) -> dict:
    """Build verified rule-level evidence using Python."""
    grouped_findings = defaultdict(list)

    for issue in report.get("issues", []):
        rule = issue.get("rule", "unknown_rule")
        grouped_findings[rule].append({
            "company_id": issue.get("company_id"),
            "severity": issue.get("severity", "UNKNOWN"),
            "message": issue.get("message", ""),
        })

    rules = []
    for rule, findings in sorted(grouped_findings.items()):
        severity_counts = defaultdict(int)

        for finding in findings:
            severity_counts[finding["severity"]] += 1

        rules.append({
            "rule": rule,
            "finding_count": len(findings),
            "severity_breakdown": dict(sorted(severity_counts.items())),
            "evidence": findings[:5],
            "additional_findings_omitted": max(0, len(findings) - 5),
        })

    return {
        "verified_totals": {
            "total_records": report["total_records"],
            "total_issues": report["total_issues"],
            "affected_records": report["affected_records"],
        },
        "verified_severity_breakdown": report["issues_by_severity"],
        "verified_rule_breakdown": report["issues_by_rule"],
        "rule_evidence": rules,
    }


RULE_ACTIONS = {
    "potential_duplicate_company": (
        "Compare company identifiers and other attributes; merge only "
        "after confirming that the records represent the same entity."
    ),
    "missing_value": (
        "Retrieve the missing field from an authoritative source and "
        "record the provenance of the correction."
    ),
    "invalid_country": (
        "Check the source country value and map it to an approved country code."
    ),
    "negative_revenue": (
        "Verify the value, sign, currency, and accounting context against "
        "the source record before changing it."
    ),
    "negative_employee_count": (
        "Verify the employee count and its reporting period against the source."
    ),
    "zero_employee_count": (
        "Confirm whether zero employees is legitimate for this entity."
    ),
    "invalid_credit_score": (
        "Check the score, allowed range, and source-system definition."
    ),
    "unusual_annual_growth": (
        "Verify the growth calculation, reporting periods, and source values."
    ),
    "invalid_website": (
        "Confirm the official website and normalize it to a valid HTTP/HTTPS URL."
    ),
}


def build_fallback_insights(evidence: dict) -> str:
    """Create a useful business report without an available language model."""
    totals = evidence["verified_totals"]
    rules = evidence["rule_evidence"]
    severity = evidence["verified_severity_breakdown"]

    if not rules:
        return (
            "### Executive summary\n\n"
            "No validation findings were returned by the configured rules.\n\n"
            "### Main data quality risks\n\n"
            "No issues were flagged in this run. This does not guarantee "
            "that every field is correct or complete.\n\n"
            "### Recommended actions\n\n"
            "- Review whether the configured rules cover the intended use.\n"
            "- Confirm important records against authoritative sources.\n\n"
            "### Limitations and human review\n\n"
            "The report uses deterministic fallback logic because AI "
            "insight generation was unavailable."
        )

    high_rules = [
        item for item in rules
        if item["severity_breakdown"].get("HIGH", 0) > 0
    ]
    duplicate_count = evidence["verified_rule_breakdown"].get(
        "potential_duplicate_company", 0
    )

    lines = [
        "### Executive summary",
        "",
        f"The validation process examined {totals['total_records']} records "
        f"and flagged {totals['affected_records']} records for review. "
        f"It recorded {totals['total_issues']} findings. These are rule-based "
        "flags, not confirmed errors. Resolve material issues before relying "
        "on the affected data for business decisions.",
        "",
        "### Main data quality risks",
        "",
    ]

    if duplicate_count:
        lines.append(
            "Potential duplicate company names may affect entity matching, "
            "record counts, and downstream analysis. Duplicate flags do not "
            "prove that records represent the same business."
        )

    if high_rules:
        lines.append(
            "High-severity findings need prompt verification, particularly "
            "missing or invalid values that could affect company profiling "
            "and analytical results."
        )

    for item in rules:
        lines.append(
            f"- **{item['rule']}**: {item['finding_count']} finding(s)."
        )

    lines.extend([
        "",
        "### Recommended investigation and corrective actions",
        "",
    ])

    for item in sorted(
        rules,
        key=lambda rule: (
            -rule["severity_breakdown"].get("HIGH", 0),
            -rule["finding_count"],
            rule["rule"],
        ),
    ):
        action = RULE_ACTIONS.get(
            item["rule"],
            "Review the evidence against an authoritative source before "
            "approving any correction.",
        )
        lines.append(f"- **{item['rule']}** — {action}")

    lines.extend([
        "",
        "### Limitations and human review",
        "",
        "Business impact cannot be quantified from these validation flags "
        "alone. Verify suspected issues with source owners, retain an audit "
        "trail, and rerun validation after approved corrections. This report "
        "uses deterministic fallback logic because AI insight generation "
        "was unavailable.",
        "",
        f"Severity breakdown: {json.dumps(severity, sort_keys=True)}.",
    ])

    return "\n".join(lines)


def generate_insights(state: AgentState) -> dict:
    """Generate evidence-grounded business insights with a safe fallback."""
    evidence = build_evidence_summary(state["validation_report"])
    cloud_enabled = bool(os.getenv("OLLAMA_API_KEY"))
    model = CLOUD_MODEL if cloud_enabled else LOCAL_MODEL
    source = f"Ollama Cloud ({model})" if cloud_enabled else f"Local Ollama ({model})"

    prompt = f"""
You are a business data quality analyst writing for business stakeholders.

Use only the Python-verified evidence below:
{json.dumps(evidence, indent=2)}

Write a concise report with these exact Markdown headings:
### Executive summary
### Main data quality risks
### Potential business impact
### Recommended investigation and corrective actions
### Limitations and items requiring human review

Requirements:
- Explain what the findings could mean for company profiling, reporting,
  entity matching, and analytical decisions, where relevant.
- Prioritize high-severity findings and provide actions tied to each rule.
- Explain that potential duplicate names require verification before merging.
- Do not claim that flagged records are definitely wrong.
- Do not invent financial losses, causes, company facts, or outcomes.
- Do not invent counts, percentages, or statistics; refer to rule names
  instead of restating numerical summaries.
- State when business impact cannot be determined from the evidence.
- Recommend source verification and an audit trail before corrections.
- Use clear business language, preferably under 250 words.
"""

    try:
        response = chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain verified data quality evidence "
                        "conservatively. Never invent findings, company "
                        "facts, numerical claims, causes, or outcomes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1},
        )
        insights = response_text(response)

        if not insights:
            raise ValueError("The model returned an empty response.")

        return {
            "evidence_summary": evidence,
            "ai_insights": insights,
            "ai_status": "success",
            "report_source": source,
        }

    except Exception as exc:
        print(f"AI insight generation failed: {type(exc).__name__}: {exc}")
        return {
            "evidence_summary": evidence,
            "ai_insights": build_fallback_insights(evidence),
            "ai_status": "fallback",
            "report_source": "Deterministic fallback; AI unavailable",
        }


def save_report(state: AgentState) -> dict:
    """Save verified statistics separately from generated explanations."""
    report = state["validation_report"]
    verified_summary = {
        "total_records": report["total_records"],
        "total_issues": report["total_issues"],
        "affected_records": report["affected_records"],
        "issues_by_severity": report["issues_by_severity"],
        "issues_by_rule": report["issues_by_rule"],
    }

    summary_json = json.dumps(verified_summary, indent=2)
    evidence_json = json.dumps(state["evidence_summary"], indent=2)
    ai_status = state.get("ai_status", "unknown")
    report_source = state.get("report_source", "Unknown")

    final_report = (
        "# Business Data Quality Assessment\n\n"
        "## Verified Validation Summary\n\n"
        "Statistics calculated by Python using the configured validation rules.\n\n"
        f"```json\n{summary_json}\n```\n\n"
        "## Rule-Level Evidence\n\n"
        "Evidence grouped by Python from the validation findings.\n\n"
        f"```json\n{evidence_json}\n```\n\n"
        "## Business Assessment\n\n"
        f"**Report source:** {report_source}  \n"
        f"**AI status:** {ai_status}\n\n"
        f"{state['ai_insights']}\n\n"
        "---\n\n"
        "**Important:** Findings are rule-based flags, not necessarily "
        "confirmed errors. Python calculates the validation statistics; "
        "the language model explains the supplied evidence when available. "
        "Verify records before making changes.\n"
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(final_report, encoding="utf-8")
    print(f"Report saved to: {REPORT_PATH}")

    return {"final_report": final_report}


builder = StateGraph(AgentState)
builder.add_node("validate_data", validate_data)
builder.add_node("generate_insights", generate_insights)
builder.add_node("save_report", save_report)
builder.add_edge(START, "validate_data")
builder.add_edge("validate_data", "generate_insights")
builder.add_edge("generate_insights", "save_report")
builder.add_edge("save_report", END)

agent = builder.compile()


if __name__ == "__main__":
    result = agent.invoke({})
    print(result["final_report"])
    print(f"\nAI status: {result.get('ai_status', 'unknown')}")
    print("LangGraph workflow completed successfully.")
