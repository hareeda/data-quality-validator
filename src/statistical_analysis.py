
from __future__ import annotations

import numpy as np
import pandas as pd


def analyze_dataset(df: pd.DataFrame) -> dict:
    """
    Generate general-purpose statistical profiles for any tabular dataset.

    The function does not modify the input DataFrame. Numeric statistics
    use values that can be parsed as numbers; date statistics are generated
    for columns identified as dates by their names or values.
    """
    row_count, column_count = df.shape

    result = {
        "dataset_overview": {
            "row_count": int(row_count),
            "column_count": int(column_count),
            "duplicate_row_count": int(df.duplicated().sum()),
            "total_missing_cells": int(df.isna().sum().sum()),
            "total_cells": int(df.size),
            "memory_usage_bytes": int(
                df.memory_usage(index=True, deep=True).sum()
            ),
        },
        "columns": [],
        "numeric_correlations": {},
        "notes": [
            "Statistics describe the uploaded dataset, not the quality "
            "or correctness of the underlying business facts.",
            "Outliers and correlations indicate patterns, not proof of errors "
            "or causal relationships.",
        ],
    }

    numeric_columns = []

    for column in df.columns:
        series = df[column]
        non_missing = series.dropna()
        name = str(column)
        lower_name = name.lower()

        column_result = {
            "column": name,
            "data_type": str(series.dtype),
            "non_missing_count": int(series.notna().sum()),
            "missing_count": int(series.isna().sum()),
            "missing_percent": round(
                100 * series.isna().mean(), 2
            ) if row_count else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
            "unique_percent": round(
                100 * series.nunique(dropna=True) / row_count, 2
            ) if row_count else 0.0,
        }

        # Try numeric profiling for numeric dtypes or columns with
        # number-like values. Identifier-like columns are excluded from
        # correlations but still receive descriptive statistics.
        numeric = pd.to_numeric(series, errors="coerce")
        numeric_ratio = (
            numeric.notna().sum() / max(series.notna().sum(), 1)
        )
        is_numeric = (
            pd.api.types.is_numeric_dtype(series)
            or (
                numeric_ratio >= 0.9
                and len(non_missing) > 0
                and not any(
                    token in lower_name
                    for token in ("phone", "postal", "zip", "code")
                )
            )
        )

        if is_numeric:
            values = numeric.dropna()
            column_result["profile_type"] = "numeric"

            if len(values):
                q1 = float(values.quantile(0.25))
                median = float(values.median())
                q3 = float(values.quantile(0.75))
                iqr = q3 - q1

                lower_fence = q1 - 1.5 * iqr
                upper_fence = q3 + 1.5 * iqr
                outlier_count = int(
                    ((values < lower_fence) | (values > upper_fence)).sum()
                )

                column_result["statistics"] = {
                    "count": int(values.count()),
                    "mean": _safe_float(values.mean()),
                    "median": _safe_float(median),
                    "standard_deviation": _safe_float(values.std()),
                    "variance": _safe_float(values.var()),
                    "minimum": _safe_float(values.min()),
                    "maximum": _safe_float(values.max()),
                    "range": _safe_float(values.max() - values.min()),
                    "q1": _safe_float(q1),
                    "q3": _safe_float(q3),
                    "interquartile_range": _safe_float(iqr),
                    "skewness": _safe_float(values.skew()),
                    "outlier_count_iqr": outlier_count,
                }

                if (
                    len(values) >= 2
                    and not any(
                        token in lower_name
                        for token in (
                            "id", "phone", "postal", "zip", "code"
                        )
                    )
                ):
                    numeric_columns.append(name)
            else:
                column_result["statistics"] = None

        else:
            # Detect likely date columns by name or parseable values.
            parsed_dates = None
            date_name = any(
                token in lower_name
                for token in ("date", "time", "_at", "_on", "timestamp")
            )

            if date_name and len(non_missing):
                parsed_dates = pd.to_datetime(
                    non_missing, errors="coerce", format="mixed", utc=True
                )
            elif (
                len(non_missing)
                and not any(
                    token in lower_name
                    for token in ("id", "code", "phone", "zip", "postal")
                )
            ):
                sample = non_missing.astype(str).head(100)
                candidate_dates = pd.to_datetime(
                    sample, errors="coerce", format="mixed", utc=True
                )
                if candidate_dates.notna().mean() >= 0.9:
                    parsed_dates = pd.to_datetime(
                        non_missing, errors="coerce",
                        format="mixed", utc=True
                    )

            if parsed_dates is not None:
                valid_dates = parsed_dates.dropna()
                column_result["profile_type"] = "date"
                column_result["invalid_date_count"] = int(
                    parsed_dates.isna().sum()
                )
                if len(valid_dates):
                    column_result["date_statistics"] = {
                        "earliest": valid_dates.min().isoformat(),
                        "latest": valid_dates.max().isoformat(),
                        "span_days": int(
                            (valid_dates.max() - valid_dates.min()).days
                        ),
                    }
                else:
                    column_result["date_statistics"] = None
            else:
                column_result["profile_type"] = "categorical"
                counts = non_missing.astype(str).value_counts()
                column_result["top_values"] = [
                    {"value": str(value), "count": int(count)}
                    for value, count in counts.head(5).items()
                ]
                column_result["category_count"] = int(len(counts))
                column_result["high_cardinality"] = bool(
                    row_count > 0
                    and series.nunique(dropna=True) / row_count > 0.8
                )

        result["columns"].append(column_result)

    # Pairwise correlations are computed only when there are at least
    # two eligible numeric columns and enough complete observations.
    if len(numeric_columns) >= 2:
        numeric_frame = pd.DataFrame({
            column: pd.to_numeric(df[column], errors="coerce")
            for column in numeric_columns
        })
        correlation = numeric_frame.corr(min_periods=3)

        result["numeric_correlations"] = {
            column: {
                other: _safe_float(value)
                for other, value in correlation[column].items()
            }
            for column in correlation.columns
        }

    return result


def _safe_float(value):
    """Convert NumPy/Pandas numeric values to JSON-safe Python values."""
    if value is None or pd.isna(value):
        return None
    value = float(value)
    if not np.isfinite(value):
        return None
    return value
