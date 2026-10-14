
import json

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Business Data Quality Intelligence",
    page_icon="📊",
    layout="wide",
)


# ---------- Styling ----------

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


# ---------- Sidebar ----------

with st.sidebar:
    st.title("Data Quality")
    st.caption("AI-assisted company data intelligence")

    api_url = st.text_input(
        "Backend API URL",
        value=DEFAULT_API_URL,
    ).rstrip("/")

    st.divider()
    st.markdown("**Workflow**")
    st.markdown(
        "1. Upload a CSV\n"
        "2. Run validation rules\n"
        "3. Review findings and evidence\n"
        "4. Read AI-assisted insights"
    )

    if st.button("Clear current results"):
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_filename", None)
        st.rerun()


# ---------- Header ----------

st.title("Business Data Quality Intelligence")
st.caption(
    "Identify data quality risks, explore validation findings, "
    "and generate AI-assisted business insights."
)


# ---------- API status ----------

status_col, info_col = st.columns([1, 3])

try:
    health_response = requests.get(
        f"{api_url}/health",
        timeout=5,
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
        "FastAPI runs the Python validation engine and LangGraph workflow. "
        "Ollama provides local AI insights when available."
    )

st.divider()


# ---------- CSV upload ----------

st.subheader("Analyze company data")

uploaded_file = st.file_uploader(
    "Upload a company CSV file",
    type=["csv"],
    help="Maximum file size: 10 MB. Required company-data columns must be present.",
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
                "Validating records and generating business insights..."
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
                    timeout=300,
                )

            if response.ok:
                st.session_state["analysis_result"] = response.json()
                st.session_state["analysis_filename"] = uploaded_file.name
                st.success("Analysis completed.")
            else:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text

                st.error(
                    f"Request failed ({response.status_code}): {detail}"
                )

        except requests.Timeout:
            st.error(
                "The analysis took too long. Check whether the backend "
                "and Ollama are running, then try again."
            )
        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")


# ---------- Results ----------

result = st.session_state.get("analysis_result")

if result:
    summary = result.get("summary", {})
    issues = result.get("issues", [])
    report = result.get("report", "")
    evidence = result.get("evidence", {})
    ai_status = result.get("ai_status", "unknown")

    st.divider()
    st.subheader("Dataset overview")

    filename = st.session_state.get(
        "analysis_filename",
        "Uploaded dataset",
    )
    st.caption(f"Analyzed file: **{filename}**")

    # ---------- AI status ----------

    st.markdown("### AI insight generation")

    if ai_status == "success":
        st.success(
            "AI-generated insights: Ollama successfully returned a report."
        )
    elif ai_status == "fallback":
        st.warning(
            "Fallback report: the workflow generated a deterministic report "
            "because AI insight generation was unavailable."
        )
    else:
        st.info(
            "AI status is unknown. The API response did not identify "
            "whether Ollama or the fallback generated the report."
        )

    # ---------- KPI cards ----------

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            "Records analyzed",
            summary.get("total_records", 0),
        )

    with k2:
        st.metric(
            "Validation findings",
            summary.get("total_issues", 0),
        )

    with k3:
        st.metric(
            "Affected records",
            summary.get("affected_records", 0),
        )

    severity_counts = summary.get("issues_by_severity", {})
    high_count = severity_counts.get("HIGH", 0)

    with k4:
        st.metric(
            "High-severity findings",
            high_count,
        )

        # ---------- Statistical analysis ----------

    st.divider()
    st.subheader("Statistical analysis")

    statistical = summary.get("statistical_analysis", {})

    if statistical:
        overview = statistical.get("overview", {})

        st.markdown("**Dataset statistics**")

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric("Rows", overview.get("rows", 0))

        with stat_col2:
            st.metric("Columns", overview.get("columns", 0))

        with stat_col3:
            st.metric("Missing cells", overview.get("missing_cells", 0))

        with stat_col4:
            st.metric("Duplicate rows", overview.get("duplicate_rows", 0))

        numeric_stats = statistical.get("numeric_summary", [])

        if numeric_stats:
            st.markdown("**Numeric field statistics**")
            st.dataframe(
                pd.DataFrame(numeric_stats),
                use_container_width=True,
                hide_index=True,
            )

        column_stats = statistical.get("column_profiles", [])

        if column_stats:
            st.markdown("**Column profiles**")
            st.dataframe(
                pd.DataFrame(column_stats),
                use_container_width=True,
                hide_index=True,
            )

        correlations = statistical.get("correlations", {})

        if correlations:
            st.markdown("**Correlation analysis**")
            st.dataframe(
                pd.DataFrame(correlations),
                use_container_width=True,
            )

    else:
        st.info(
            "Statistical analysis is not available. "
            "Confirm that the backend returns statistical_analysis."
        )


    rule_counts = summary.get("issues_by_rule", {})

    st.caption(
        f"Validation rules with findings: {len(rule_counts)}. "
        "Findings are rule-generated flags, not necessarily confirmed errors. "
        "The number of findings may differ from the number of affected records."
    )

    # ---------- Charts ----------

    st.divider()
    st.subheader("Validation analytics")

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

    # ---------- Rule-level evidence ----------

    st.divider()
    st.subheader("Rule-level evidence")

    if evidence and evidence.get("rule_evidence"):
        st.caption(
            "Evidence grouped by validation rule using Python. "
            "Examples may be limited to five findings per rule."
        )

        for rule_item in evidence["rule_evidence"]:
            rule_name = rule_item.get("rule", "Unknown rule")
            finding_count = rule_item.get("finding_count", 0)
            severity_breakdown = rule_item.get("severity_breakdown", {})

            with st.expander(
                f"{rule_name} — {finding_count} finding(s)"
            ):
                st.write("**Severity breakdown**")
                st.json(severity_breakdown)

                examples = rule_item.get("evidence", [])

                if examples:
                    st.write("**Example findings**")
                    st.dataframe(
                        pd.DataFrame(examples),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No example findings were supplied.")

                omitted = rule_item.get(
                    "additional_findings_omitted", 0
                )

                if omitted:
                    st.caption(
                        f"{omitted} additional finding(s) omitted from "
                        "this evidence preview."
                    )

    elif evidence:
        st.info(
            "Evidence was returned, but no rule-level examples were supplied."
        )
    else:
        st.info(
            "Rule-level evidence is not available in this API response. "
            "Confirm that the backend returns the agent's evidence_summary."
        )

    # ---------- Findings table ----------

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
            "Search by company ID, name, or finding message",
            placeholder="Enter a company or keyword...",
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

        display_columns = [
            column
            for column in [
                "company_id",
                "company_name",
                "rule",
                "severity",
                "message",
            ]
            if column in filtered_df.columns
        ]

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

    # ---------- AI report ----------

    st.divider()
    st.subheader("Business quality report")

    st.caption(
        "Use the verified Python summary and validation findings as the "
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

    # ---------- Structured downloads ----------

    structured_result = {
        "status": result.get("status", "unknown"),
        "ai_status": ai_status,
        "summary": summary,
        "issues": issues,
        "evidence": evidence,
        "report": report,
    }

    st.download_button(
        "Download structured results (JSON)",
        data=json.dumps(structured_result, indent=2),
        file_name="data_quality_results.json",
        mime="application/json",
    )

else:
    st.info(
        "Upload a company CSV and select **Analyze dataset** "
        "to see the analytics dashboard."
    )
