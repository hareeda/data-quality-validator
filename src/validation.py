
import json
from pathlib import Path

import pandas as pd

from src.statistical_analysis import analyze_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "companies.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "quality_report.json"


def _safe_value(value):
    """Convert pandas/numpy values into JSON-safe Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def _record_identifier(df, index):
    """Return a useful identifier without assuming a specific schema."""
    for column in df.columns:
        if str(column).strip().lower() in {
            "id",
            "record_id",
            "customer_id",
            "employee_id",
            "transaction_id",
            "company_id",
        }:
            value = df.iloc[index][column]

            if pd.notna(value):
                return str(value)

    return str(df.index[index])


def _add_issue(issues, df, row_index, rule, severity, message, column=None):
    """Create a consistent, schema-independent finding."""
    issue = {
        "record_id": _record_identifier(df, row_index),
        "row_index": int(row_index),
        "rule": rule,
        "severity": severity,
        "message": message,
    }

    if column is not None:
        issue["column"] = str(column)

    # Include available context without forcing particular column names.
    row = df.iloc[row_index]

    for field in list(df.columns)[:10]:
        issue[str(field)] = _safe_value(row[field])

    issues.append(issue)


def validate_dataset(file_path):
    """
    Validate a generic tabular dataset.

    Rules:
    - Missing values
    - Duplicate rows
    - Duplicate column names
    - Constant columns
    - Potential numeric outliers using the IQR method

    These rules flag potential quality concerns; they do not assume
    that unusual values are necessarily incorrect.
    """
    file_path = Path(file_path)

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The uploaded CSV is empty.") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            "The CSV encoding could not be read. Save the file as UTF-8 "
            "and upload it again."
        ) from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            f"The CSV could not be parsed: {exc}"
        ) from exc

    if df.empty and len(df.columns) == 0:
        raise ValueError("The uploaded CSV has no columns.")

    if len(df.columns) == 0:
        raise ValueError("The uploaded CSV has no columns.")

    issues = []

    # ----------------------------------------------
    # Duplicate column names
    # ----------------------------------------------

    column_names = pd.Index(df.columns.astype(str))
    duplicated_names = column_names[
        column_names.duplicated(keep=False)
    ].unique()

    for column in duplicated_names:
        issues.append(
            {
                "record_id": None,
                "row_index": None,
                "column": str(column),
                "rule": "duplicate_column_name",
                "severity": "HIGH",
                "message": (
                    f"The column name '{column}' appears more than once."
                ),
            }
        )

    # ----------------------------------------------
    # Missing values
    # ----------------------------------------------

    for column in df.columns:
        missing_mask = df[column].isna()
        missing_count = int(missing_mask.sum())

        if missing_count == 0:
            continue

        missing_percent = missing_count / max(len(df), 1) * 100

        severity = "HIGH" if missing_percent >= 50 else "MEDIUM"

        for position in range(len(df)):
            if missing_mask.iloc[position]:
                _add_issue(
                    issues=issues,
                    df=df,
                    row_index=position,
                    rule="missing_value",
                    severity=severity,
                    message=(
                        f"Column '{column}' contains a missing value. "
                        f"{missing_percent:.1f}% of this column is missing."
                    ),
                    column=column,
                )

    # ----------------------------------------------
    # Duplicate rows
    # ----------------------------------------------

    duplicate_mask = df.duplicated(keep=False)

    for position in range(len(df)):
        if duplicate_mask.iloc[position]:
            _add_issue(
                issues=issues,
                df=df,
                row_index=position,
                rule="duplicate_row",
                severity="MEDIUM",
                message=(
                    "This row matches another row across all columns. "
                    "Verify whether the duplicate is intentional."
                ),
            )

    # ----------------------------------------------
    # Constant columns
    # ----------------------------------------------

    for column in df.columns:
        non_missing = df[column].dropna()

        if len(non_missing) > 1 and non_missing.nunique() == 1:
            issues.append(
                {
                    "record_id": None,
                    "row_index": None,
                    "column": str(column),
                    "rule": "constant_column",
                    "severity": "LOW",
                    "message": (
                        f"Column '{column}' has only one distinct "
                        "non-missing value. Check whether this field "
                        "provides useful information."
                    ),
                }
            )

    # ----------------------------------------------
    # Numeric outliers using IQR
    # ----------------------------------------------

    for column in df.select_dtypes(include="number").columns:
        series = df[column].dropna()

        # Small samples do not support a useful outlier assessment.
        if len(series) < 4 or series.nunique() < 2:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if pd.isna(iqr) or iqr == 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_positions = (
            (df[column] < lower_bound)
            | (df[column] > upper_bound)
        ).fillna(False)

        for position in range(len(df)):
            if outlier_positions.iloc[position]:
                value = _safe_value(df.iloc[position][column])

                _add_issue(
                    issues=issues,
                    df=df,
                    row_index=position,
                    rule="potential_numeric_outlier",
                    severity="LOW",
                    message=(
                        f"Value {value} in column '{column}' falls outside "
                        f"the IQR thresholds [{lower_bound:.4g}, "
                        f"{upper_bound:.4g}]. Verify its context."
                    ),
                    column=column,
                )

    # ----------------------------------------------
    # Summaries
    # ----------------------------------------------

    issue_df = pd.DataFrame(issues)

    issues_by_severity = {}
    issues_by_rule = {}

    if not issue_df.empty:
        issues_by_severity = {
            str(key): int(value)
            for key, value in issue_df["severity"].value_counts().items()
        }

        issues_by_rule = {
            str(key): int(value)
            for key, value in issue_df["rule"].value_counts().items()
        }

    affected_rows = {
        issue["row_index"]
        for issue in issues
        if issue.get("row_index") is not None
    }

    # Include duplicate column/constant-column findings in total findings,
    # but only row-specific findings contribute to affected records.
    report = {
        "dataset_name": file_path.name,
        "total_records": int(len(df)),
        "total_columns": int(len(df.columns)),
        "total_issues": int(len(issues)),
        "affected_records": int(len(affected_rows)),
        "issues_by_severity": issues_by_severity,
        "issues_by_rule": issues_by_rule,
        "issues": issues,
        "statistical_analysis": analyze_dataset(df),
    }

    # Save a local JSON report for existing project workflows.
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2, default=str)

    return report


def validate_companies(file_path=DATA_PATH):
    """
    Backward-compatible wrapper.

    Existing agent code can continue calling validate_companies()
    while the application transitions to generic dataset validation.
    """
    return validate_dataset(file_path)
