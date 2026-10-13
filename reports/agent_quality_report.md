# AI-Powered Business Data Quality Report

## Verified Validation Summary

These statistics were calculated by Python using the configured validation rules.

```json
{
  "total_records": 15,
  "total_issues": 14,
  "affected_records": 13,
  "issues_by_severity": {
    "MEDIUM": 9,
    "HIGH": 5
  },
  "issues_by_rule": {
    "potential_duplicate_company": 6,
    "missing_value": 1,
    "invalid_country": 1,
    "negative_revenue": 1,
    "negative_employee_count": 1,
    "zero_employee_count": 1,
    "invalid_credit_score": 1,
    "unusual_annual_growth": 1,
    "invalid_website": 1
  }
}
```

## Rule-Level Evidence

The following evidence was grouped by Python from the validation findings.

```json
{
  "verified_totals": {
    "total_records": 15,
    "total_issues": 14,
    "affected_records": 13
  },
  "verified_severity_breakdown": {
    "MEDIUM": 9,
    "HIGH": 5
  },
  "verified_rule_breakdown": {
    "potential_duplicate_company": 6,
    "missing_value": 1,
    "invalid_country": 1,
    "negative_revenue": 1,
    "negative_employee_count": 1,
    "zero_employee_count": 1,
    "invalid_credit_score": 1,
    "unusual_annual_growth": 1,
    "invalid_website": 1
  },
  "rule_evidence": [
    {
      "rule": "invalid_country",
      "finding_count": 1,
      "severity_breakdown": {
        "HIGH": 1
      },
      "evidence": [
        {
          "company_id": "C007",
          "severity": "HIGH",
          "message": "Country code 'XX' is not in the approved list."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "invalid_credit_score",
      "finding_count": 1,
      "severity_breakdown": {
        "HIGH": 1
      },
      "evidence": [
        {
          "company_id": "C011",
          "severity": "HIGH",
          "message": "Credit score must be between 0 and 100."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "invalid_website",
      "finding_count": 1,
      "severity_breakdown": {
        "MEDIUM": 1
      },
      "evidence": [
        {
          "company_id": "C008",
          "severity": "MEDIUM",
          "message": "Website does not match the expected HTTP/HTTPS URL format."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "missing_value",
      "finding_count": 1,
      "severity_breakdown": {
        "HIGH": 1
      },
      "evidence": [
        {
          "company_id": "C005",
          "severity": "HIGH",
          "message": "Required field 'revenue' is missing."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "negative_employee_count",
      "finding_count": 1,
      "severity_breakdown": {
        "HIGH": 1
      },
      "evidence": [
        {
          "company_id": "C006",
          "severity": "HIGH",
          "message": "Employee count cannot be negative."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "negative_revenue",
      "finding_count": 1,
      "severity_breakdown": {
        "HIGH": 1
      },
      "evidence": [
        {
          "company_id": "C014",
          "severity": "HIGH",
          "message": "Revenue cannot be negative under this validation rule."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "potential_duplicate_company",
      "finding_count": 6,
      "severity_breakdown": {
        "MEDIUM": 6
      },
      "evidence": [
        {
          "company_id": "C001",
          "severity": "MEDIUM",
          "message": "Company name matches another record after trimming spaces and ignoring case."
        },
        {
          "company_id": "C002",
          "severity": "MEDIUM",
          "message": "Company name matches another record after trimming spaces and ignoring case."
        },
        {
          "company_id": "C004",
          "severity": "MEDIUM",
          "message": "Company name matches another record after trimming spaces and ignoring case."
        },
        {
          "company_id": "C005",
          "severity": "MEDIUM",
          "message": "Company name matches another record after trimming spaces and ignoring case."
        },
        {
          "company_id": "C009",
          "severity": "MEDIUM",
          "message": "Company name matches another record after trimming spaces and ignoring case."
        }
      ],
      "additional_findings_omitted": 1
    },
    {
      "rule": "unusual_annual_growth",
      "finding_count": 1,
      "severity_breakdown": {
        "MEDIUM": 1
      },
      "evidence": [
        {
          "company_id": "C010",
          "severity": "MEDIUM",
          "message": "Annual growth exceeds 100%; verify against the source."
        }
      ],
      "additional_findings_omitted": 0
    },
    {
      "rule": "zero_employee_count",
      "finding_count": 1,
      "severity_breakdown": {
        "MEDIUM": 1
      },
      "evidence": [
        {
          "company_id": "C012",
          "severity": "MEDIUM",
          "message": "Company reports zero employees; review whether this is expected."
        }
      ],
      "additional_findings_omitted": 0
    }
  ]
}
```

## Business Insights

Report source: **Deterministic fallback; local AI unavailable**

### Main data quality risks
The validation engine identified the following rule-based findings:
- `invalid_country`: 1 finding(s).
- `invalid_credit_score`: 1 finding(s).
- `invalid_website`: 1 finding(s).
- `missing_value`: 1 finding(s).
- `negative_employee_count`: 1 finding(s).
- `negative_revenue`: 1 finding(s).
- `potential_duplicate_company`: 6 finding(s).
- `unusual_annual_growth`: 1 finding(s).
- `zero_employee_count`: 1 finding(s).

### Potential business impact
Investigate findings before using the affected records for company profiling, reporting, or analytical decisions. The actual impact depends on the underlying records and their intended use.

### Recommended investigation and corrective actions
- Review the affected records and the evidence recorded for each rule.
- Confirm suspected issues against authoritative source data.
- Correct records only after verification and retain an audit trail.
- Rerun validation after approved corrections.

### Limitations and items requiring human review
These are automated validation flags, not confirmed errors. The local LLM was unavailable, so this report uses a deterministic fallback rather than AI-generated analysis.

---

**Important:** Findings are rule-based flags, not necessarily confirmed errors. The validation engine calculates the statistics; the language model, when available, explains the supplied evidence. Review findings before changing source data.
