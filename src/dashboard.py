
import json

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = "https://ai-data-quality-validator-api.onrender.com"
REQUEST_TIMEOUT = 300


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Business Data Quality Intelligence",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.08);
            border: 1px solid rgba(128, 128, 128, 0.2);
            padding: 16px;
            border-radius: 12px;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_statistical_analysis(result, summary):
    """
    Support both API response formats:
    1. result["summary"]["statistical_analysis"]
    2. result["statistical_analysis"]
    """
    statistical = summary.get("statistical_analysis")

    if not statistical:
        statistical = result.get("statistical_analysis")

    if not isinstance(statistical, dict):
        return {}

    return statistical


def safe_number(value, default=0):
    """Return a display-safe numeric value."""
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
        return value
    except (TypeError, ValueError):
        return default


def display_dataframe(data, empty_message):
    """Display a list of dictionaries as a dataframe."""
    if isinstance(data, list) and data:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(empty_message)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.title("Data Quality")
    st.caption("AI-assisted company data intelligence")

    api_url = st.text_input(
        "Backend API URL",
        value=DEFAULT_API_URL,
    ).strip().rstrip("/")

    st.divider()

    st.markdown("**Workflow**")
    st.markdown(
        "1. Upload a CSV\n"
        "2. Run validation rules\n"
        "3. Review findings and evidence\n"
        "4. Explore statistical analysis\n"
        "5. Read AI-assisted insights"
    )

    if st.button("Clear current results"):
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_filename", None)
        st.rerun()


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("Business Data Quality Intelligence")

st.caption(
    "Identify data quality risks, explore validation findings, "
    "analyze dataset statistics, and generate AI-assisted business insights."
)


# --------------------------------------------------
# Backend status
# --------------------------------------------------

status_col, info_col = st.columns([1, 3])

api_healthy = False

try:
    health_response = requests.get(
        f"{api_url}/health",
        timeout=10,
    )
    api_healthy = health_response.ok
except requests.RequestException:
    api_healthy = False

with status_col:
    if api_healthy:
        st.success("Backend connected")
    else:
        st.error("Backend unavailable")

with info_col:
    st.caption(
        "FastAPI runs the validation workflow. The backend should return "
        "statistical profiles, validation findings, evidence, and AI insights."
    )

st.divider()


# --------------------------------------------------
# CSV upload
# --------------------------------------------------

st.subheader("Analyze your dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type=["csv"],
    help="Maximum file size: 10 MB.",
)

if uploaded_file is not None:
    st.caption(f"Selected file: **{uploaded_file.name}**")

    if st.button(
        "Analyze dataset",
        type="primary",
        disabled=not api_healthy,
    ):
        try:
            with st.spinner(
                "Validating records, calculating statistics, "
                "and generating business insights..."
            ):
                response = requests.post(
                    f"{api_url}/upload-csv",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "text/csv",
                        )
                    },
                    timeout=REQUEST_TIMEOUT,
                )

            if response.ok:
                response_data = response.json()

                st.session_state["analysis_result"] = response_data
                st.session_state["analysis_filename"] = uploaded_file.name

                st.success("Analysis completed successfully.")

            else:
                try:
                    detail = response.json().get(
                        "detail",
                        response.text,
                    )
                except ValueError:
                    detail = response.text

                st.error(
                    f"Request failed ({response.status_code}): {detail}"
                )

        except requests.Timeout:
            st.error(
                "The analysis took too long. Check the backend logs "
                "and try again."
            )

        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")

        except ValueError as exc:
            st.error(f"The backend returned an invalid response: {exc}")


# --------------------------------------------------
# Results
# --------------------------------------------------

result = st.session_state.get("analysis_result")

if result:
    summary = result.get("summary") or {}
    issues = result.get("issues") or []
    report = result.get("report") or ""
    evidence = result.get("evidence") or {}
    ai_status = result.get("ai_status", "unknown")

    # Important compatibility fix:
    # Statistics can be nested inside summary or at the response root.
    statistical = get_statistical_analysis(result, summary)

    st.divider()
    st.subheader("Dataset overview")

    filename = st.session_state.get(
        "analysis_filename",
        "Uploaded dataset",
    )
    st.caption(f"Analyzed file: **{filename}**")

    # --------------------------------------------------
    # AI status
    # --------------------------------------------------

    st.markdown("### AI insight generation")

    if ai_status == "success":
        st.success(
            "AI-generated insights: the AI service successfully returned a report."
        )
    elif ai_status == "fallback":
        st.warning(
            "Fallback report: deterministic insights were generated "
            "because AI insight generation was unavailable."
        )
    else:
        st.info(
            "AI status is unknown. The API response did not identify "
            "whether AI or the fallback generated the report."
        )

    # --------------------------------------------------
    # KPI cards
    # --------------------------------------------------

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            "Records analyzed",
            safe_number(summary.get("total_records")),
        )

    with k2:
        st.metric(
            "Validation findings",
            safe_number(summary.get("total_issues")),
        )

    with k3:
        st.metric(
            "Affected records",
            safe_number(summary.get("affected_records")),
        )

    severity_counts = summary.get("issues_by_severity") or {}
    rule_counts = summary.get("issues_by_rule") or {}

    with k4:
        st.metric(
            "High-severity findings",
            safe_number(severity_counts.get("HIGH")),
        )

    # --------------------------------------------------
    # Statistical analysis
    # --------------------------------------------------

    st.divider()
    st.subheader("Statistical analysis")

    if statistical:
        overview = statistical.get("dataset_overview") or {}

        st.markdown("**Dataset statistics**")

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric(
                "Rows",
                safe_number(overview.get("row_count")),
            )

        with stat_col2:
            st.metric(
                "Columns",
                safe_number(overview.get("column_count")),
            )

        with stat_col3:
            st.metric(
                "Missing cells",
                safe_number(overview.get("total_missing_cells")),
            )

        with stat_col4:
            st.metric(
                "Duplicate rows",
                safe_number(overview.get("duplicate_row_count")),
            )

        total_cells = safe_number(overview.get("total_cells"))
        memory_bytes = safe_number(overview.get("memory_usage_bytes"))

        st.caption(
            f"Total cells: {total_cells:,} | "
            f"Memory usage: {memory_bytes:,} bytes"
        )

        # ----------------------------------------------
        # Column profiles
        # ----------------------------------------------

        column_profiles = statistical.get("columns") or []

        if column_profiles:
            st.markdown("**Column profiles and descriptive statistics**")

            profile_rows = []

            for column in column_profiles:
                stats = column.get("statistics") or {}
                date_stats = column.get("date_statistics") or {}

                profile_rows.append(
                    {
                        "Column": column.get("column"),
                        "Data type": column.get("data_type"),
                        "Profile type": column.get("profile_type"),
                        "Non-missing": column.get("non_missing_count"),
                        "Missing": column.get("missing_count"),
                        "Missing (%)": column.get("missing_percent"),
                        "Unique values": column.get("unique_count"),
                        "Unique (%)": column.get("unique_percent"),
                        "Mean": stats.get("mean"),
                        "Median": stats.get("median"),
                        "Std. deviation": stats.get("standard_deviation"),
                        "Minimum": stats.get("minimum"),
                        "Maximum": stats.get("maximum"),
                        "IQR outliers": stats.get("outlier_count_iqr"),
                        "Earliest date": date_stats.get("earliest"),
                        "Latest date": date_stats.get("latest"),
                    }
                )

            st.dataframe(
                pd.DataFrame(profile_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("The backend did not return column profiles.")

        # ----------------------------------------------
        # Categorical field details
        # ----------------------------------------------

        categorical_columns = [
            column
            for column in column_profiles
            if column.get("profile_type") == "categorical"
        ]

        if categorical_columns:
            st.markdown("**Categorical field distributions**")

            for column in categorical_columns:
                name = column.get("column", "Unknown column")
                top_values = column.get("top_values") or []

                with st.expander(f"Values in {name}"):
                    st.write(
                        f"Distinct categories: "
                        f"{column.get('category_count', 0)}"
                    )

                    st.write(
                        f"High cardinality: "
                        f"{column.get('high_cardinality', False)}"
                    )

                    display_dataframe(
                        top_values,
                        "No non-missing category values found.",
                    )

        # ----------------------------------------------
        # Numeric correlations
        # ----------------------------------------------

        correlations = statistical.get("numeric_correlations") or {}

        st.markdown("**Numeric correlation analysis**")

        if correlations:
            st.caption(
                "Correlation values range from -1 to +1. Positive values "
                "indicate a positive association, while negative values "
                "indicate a negative association. Correlation does not "
                "establish causation."
            )

            correlation_df = pd.DataFrame(correlations)

            st.dataframe(
                correlation_df,
                use_container_width=True,
            )
        else:
            st.info(
                "Correlation analysis requires eligible numeric columns "
                "with sufficient overlapping observations."
            )

        # ----------------------------------------------
        # Statistical notes
        # ----------------------------------------------

        notes = statistical.get("notes") or []

        if notes:
            with st.expander("How to interpret these statistics"):
                for note in notes:
                    st.write(f"- {note}")

    else:
        st.warning(
            "Statistical analysis was not found in the API response. "
            "The dashboard checked both summary.statistical_analysis "
            "and the top-level statistical_analysis field."
        )

        with st.expander("Debug API response"):
            st.write("Top-level response keys:")
            st.write(list(result.keys()))

            st.write("Summary keys:")
            st.write(list(summary.keys()))

            st.write("AI status:")
            st.write(ai_status)

            st.caption(
                "If statistical_analysis is missing from both sets of "
                "keys, the backend must be checked and redeployed."
            )

    # --------------------------------------------------
    # Validation analytics
    # --------------------------------------------------

    st.divider()
    st.subheader("Validation analytics")

    st.caption(
        f"Validation rules with findings: {len(rule_counts)}. "
        "Findings are rule-generated flags, not necessarily confirmed "
        "errors. Finding counts may differ from affected-record counts."
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Findings by severity**")

        if severity_counts:
            severity_df = pd.DataFrame(
                {"Findings": severity_counts}
            )
            st.bar_chart(severity_df)
        else:
            st.info("No findings by severity to display.")

    with chart_col2:
        st.markdown("**Findings by validation rule**")

        if rule_counts:
            rule_df = pd.DataFrame(
                {"Findings": rule_counts}
            ).sort_values("Findings", ascending=True)

            st.bar_chart(rule_df)
        else:
            st.info("No validation-rule findings to display.")

    # --------------------------------------------------
    # Rule-level evidence
    # --------------------------------------------------

    st.divider()
    st.subheader("Rule-level evidence")

    rule_evidence = evidence.get("rule_evidence") or []

    if rule_evidence:
        st.caption(
            "Evidence grouped by validation rule using Python. "
            "Examples may be limited to five findings per rule."
        )

        for rule_item in rule_evidence:
            rule_name = rule_item.get("rule", "Unknown rule")
            finding_count = rule_item.get("finding_count", 0)
            severity_breakdown = rule_item.get("severity_breakdown") or {}
            examples = rule_item.get("evidence") or []
            omitted = rule_item.get("additional_findings_omitted", 0)

            with st.expander(
                f"{rule_name} — {finding_count} finding(s)"
            ):
                st.write("**Severity breakdown**")
                st.json(severity_breakdown)

                if examples:
                    st.write("**Example findings**")
                    st.dataframe(
                        pd.DataFrame(examples),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No example findings were supplied.")

                if omitted:
                    st.caption(
                        f"{omitted} additional finding(s) omitted "
                        "from this evidence preview."
                    )

    elif evidence:
        st.info(
            "Evidence was returned, but no rule-level examples were supplied."
        )
    else:
        st.info(
            "Rule-level evidence is not available in this API response."
        )

    # --------------------------------------------------
    # Findings table
    # --------------------------------------------------

    st.divider()
    st.subheader("Explore findings")

    if issues:
        findings_df = pd.DataFrame(issues)

        filter_col1, filter_col2 = st.columns([1, 2])

        if "severity" in findings_df.columns:
            available_severities = sorted(
                findings_df["severity"].dropna().unique().tolist()
            )
        else:
            available_severities = []

        if "rule" in findings_df.columns:
            available_rules = sorted(
                findings_df["rule"].dropna().unique().tolist()
            )
        else:
            available_rules = []

        with filter_col1:
            selected_severities = st.multiselect(
                "Filter by severity",
                options=available_severities,
                default=available_severities,
            )

        with filter_col2:
            selected_rules = st.multiselect(
                "Filter by validation rule",
                options=available_rules,
                default=available_rules,
            )

        search_text = st.text_input(
            "Search findings",
            placeholder="Enter a record ID, name, or keyword...",
        )

        filtered_df = findings_df.copy()

        if "severity" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["severity"].isin(selected_severities)
            ]

        if "rule" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["rule"].isin(selected_rules)
            ]

        if search_text.strip():
            searchable = (
                filtered_df.fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
            )

            filtered_df = filtered_df[
                searchable.str.contains(
                    search_text.strip(),
                    case=False,
                    regex=False,
                )
            ]

        preferred_columns = [
            "company_id",
            "company_name",
            "rule",
            "severity",
            "message",
        ]

        display_columns = [
            column
            for column in preferred_columns
            if column in filtered_df.columns
        ]

        if not display_columns:
            display_columns = filtered_df.columns.tolist()

        st.caption(
            f"Showing {len(filtered_df)} of {len(findings_df)} findings"
        )

        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        findings_csv = filtered_df[display_columns].to_csv(index=False)

        st.download_button(
            "Download filtered findings (CSV)",
            data=findings_csv,
            file_name="filtered_data_quality_findings.csv",
            mime="text/csv",
        )

    else:
        st.success("No validation findings were reported.")

    # --------------------------------------------------
    # Business quality report
    # --------------------------------------------------

    st.divider()
    st.subheader("Business quality report")

    st.caption(
        "Verified Python summaries and validation findings provide the "
        "source of truth for numerical values. AI-generated explanations "
        "are recommendations for human review."
    )

    if report:
        with st.expander("View full report", expanded=True):
            st.markdown(report)

        st.download_button(
            "Download full report (Markdown)",
            data=report,
            file_name="data_quality_report.md",
            mime="text/markdown",
        )
    else:
        st.info("No business quality report was returned.")

    # --------------------------------------------------
    # Structured JSON download
    # --------------------------------------------------

    st.divider()
    st.subheader("Export results")

    structured_result = {
        "status": result.get("status", "unknown"),
        "ai_status": ai_status,
        "summary": summary,
        "statistical_analysis": statistical,
        "issues": issues,
        "evidence": evidence,
        "report": report,
    }

    st.download_button(
        "Download structured results (JSON)",
        data=json.dumps(
            structured_result,
            indent=2,
            default=str,
        ),
        file_name="data_quality_results.json",
        mime="application/json",
    )

else:
    st.info(
        "Upload a CSV and select **Analyze dataset** "
        "to see the analytics dashboard."
    )
