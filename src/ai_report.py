
import json
from pathlib import Path

from ollama import chat


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "reports" / "quality_report.json"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "ai_quality_report.md"


def generate_ai_report():
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        quality_report = json.load(file)

    # Keep the full list of findings out of the prompt for now.
    # The model receives the summary and rule-level counts.
    summary = {
        key: value
        for key, value in quality_report.items()
        if key != "issues"
    }

    prompt = f"""
Analyze this business data quality validation summary.

DATA:
{json.dumps(summary, indent=2)}

Write a concise business report with these sections:
1. Executive summary
2. Main data quality risks
3. Recommended corrective actions, ordered by priority
4. Limitations and items requiring human review

Rules:
- Use only the supplied counts and rule names as evidence.
- Do not invent company-specific facts.
- Distinguish validation findings from confirmed business errors.
- Explain that unusual growth and potential duplicate names require review.
- Do not claim that the data has been corrected.
- Use clear language for a business stakeholder.
"""

    response = chat(
        model="llama3.2:latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful business data quality analyst. "
                    "Never invent findings or claim actions were completed."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    report_text = response["message"]["content"]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"\nAI report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_ai_report()
