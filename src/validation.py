
import json
from pathlib import Path
from src.statistical_analysis import analyze_dataset
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "companies.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "quality_report.json"

VALID_COUNTRIES = {"US", "IN", "GB"}
MIN_CREDIT_SCORE = 0
MAX_CREDIT_SCORE = 100


def validate_companies(file_path=DATA_PATH):
    df = pd.read_csv(file_path)
    issues = []

    def add_issue(row, rule, severity, message):
        issues.append({
            "company_id": str(row.get("company_id", "")),
            "company_name": str(row.get("company_name", "")),
            "rule": rule,
            "severity": severity,
            "message": message,
        })

    # 1. Missing required values
    required_columns = [
        "company_id", "company_name", "industry",
        "country", "revenue", "employee_count",
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Required column missing: {column}")

        for _, row in df[df[column].isna()].iterrows():
            add_issue(row, "missing_value", "HIGH",
                      f"Required field '{column}' is missing.")

    # 2. Duplicate company IDs
    for _, row in df[df["company_id"].duplicated(keep=False)].iterrows():
        add_issue(row, "duplicate_company_id", "HIGH",
                  "Company ID is duplicated.")

    # 3. Potential duplicate companies based on normalized names
    normalized_names = df["company_name"].fillna("").str.strip().str.casefold()
    duplicate_name_mask = normalized_names.duplicated(keep=False) & normalized_names.ne("")

    for _, row in df[duplicate_name_mask].iterrows():
        add_issue(row, "potential_duplicate_company", "MEDIUM",
                  "Company name matches another record after trimming spaces and ignoring case.")

    # 4. Invalid country codes
    for _, row in df[~df["country"].isin(VALID_COUNTRIES)].iterrows():
        add_issue(row, "invalid_country", "HIGH",
                  f"Country code '{row['country']}' is not in the approved list.")

    # 5. Invalid numeric values
    for _, row in df[df["revenue"].notna() & (df["revenue"] < 0)].iterrows():
        add_issue(row, "negative_revenue", "HIGH",
                  "Revenue cannot be negative under this validation rule.")

    for _, row in df[df["employee_count"].notna() & (df["employee_count"] < 0)].iterrows():
        add_issue(row, "negative_employee_count", "HIGH",
                  "Employee count cannot be negative.")

    for _, row in df[df["employee_count"].notna() & (df["employee_count"] == 0)].iterrows():
        add_issue(row, "zero_employee_count", "MEDIUM",
                  "Company reports zero employees; review whether this is expected.")

    invalid_credit = (
        df["credit_score"].notna()
        & ~df["credit_score"].between(MIN_CREDIT_SCORE, MAX_CREDIT_SCORE)
    )
    for _, row in df[invalid_credit].iterrows():
        add_issue(row, "invalid_credit_score", "HIGH",
                  "Credit score must be between 0 and 100.")

    # 6. Suspicious growth values: flag for review, not automatic rejection
    for _, row in df[df["annual_growth"].notna() & (df["annual_growth"] > 100)].iterrows():
        add_issue(row, "unusual_annual_growth", "MEDIUM",
                  "Annual growth exceeds 100%; verify against the source.")

    # 7. Website format check
    website = df["website"].fillna("").astype(str).str.strip()
    valid_website = website.str.match(r"^https?://[^\s]+\.[^\s]+$", case=False)

    for idx in df.index[~valid_website]:
        row = df.loc[idx]
        add_issue(row, "invalid_website", "MEDIUM",
                  "Website does not match the expected HTTP/HTTPS URL format.")

    # Summary
    issue_df = pd.DataFrame(issues)
    summary = {
        "total_records": int(len(df)),
        "total_issues": int(len(issues)),
        "affected_records": int(issue_df["company_id"].nunique()) if not issue_df.empty else 0,
        "issues_by_severity": (
            issue_df["severity"].value_counts().to_dict()
            if not issue_df.empty else {}
        ),
        "issues_by_rule": (
            issue_df["rule"].value_counts().to_dict()
            if not issue_df.empty else {}
        ),
        "issues": issues,
        "statistical_analysis": analyze_dataset(df),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    return summary


if __name__ == "__main__":
    report = validate_companies()
    print(json.dumps({k: v for k, v in report.items() if k != "issues"}, indent=2))
    print(f"\nFull report saved to: {REPORT_PATH}")
