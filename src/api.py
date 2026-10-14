
import io
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from src.agent import agent


# ---------- Configuration ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "agent_quality_report.md"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

REQUIRED_COLUMNS = {
    "company_id",
    "company_name",
    "industry",
    "country",
    "revenue",
    "employee_count",
    "credit_score",
    "annual_growth",
    "registration_date",
    "website",
}


# ---------- FastAPI application ----------

app = FastAPI(
    title="Business Data Quality Agent",
    description=(
        "Validate company data and generate AI-assisted "
        "business insights using Python, LangGraph, and Ollama."
    ),
    version="0.3.0",
)


# ---------- Response builder ----------

def build_response(result: dict) -> dict:
    """
    Build a consistent API response from the LangGraph result.

    Statistical analysis is included inside summary because
    the Streamlit dashboard reads it from that location.
    """

    validation = result["validation_report"]

    statistical_analysis = validation.get(
        "statistical_analysis", {}
    )

    return {
        "status": "success",
        "message": "Validation workflow completed.",
        "ai_status": result.get("ai_status", "unknown"),
        "summary": {
            "total_records": validation.get("total_records", 0),
            "total_issues": validation.get("total_issues", 0),
            "affected_records": validation.get("affected_records", 0),
            "issues_by_severity": validation.get(
                "issues_by_severity", {}
            ),
            "issues_by_rule": validation.get(
                "issues_by_rule", {}
            ),
            "statistical_analysis": statistical_analysis,
        },
        "issues": validation.get("issues", []),
        "evidence": result.get("evidence_summary", {}),
        "report": result.get("final_report", ""),
    }


# ---------- Health check ----------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Business Data Quality Agent",
    }


# ---------- Run validation on default dataset ----------

@app.post("/run-validation")
def run_validation():
    """Run validation on the default project dataset."""

    try:
        result = agent.invoke({})
        return build_response(result)

    except Exception as exc:
        print(
            f"Validation workflow failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Validation workflow failed. "
                "Check the server logs."
            ),
        ) from exc


# ---------- Upload and analyze CSV ----------

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Validate an uploaded CSV and return structured findings."""

    if (
        not file.filename
        or Path(file.filename).suffix.lower() != ".csv"
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload a file with a .csv extension.",
        )

    temp_path = None

    try:
        # Read one byte beyond the limit to detect oversized files.
        contents = await file.read(MAX_FILE_SIZE + 1)

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the 10 MB upload limit.",
            )

        # Confirm that the file can be parsed as a CSV.
        try:
            headers = pd.read_csv(
                io.BytesIO(contents),
                nrows=0,
            ).columns

        except (
            ValueError,
            UnicodeDecodeError,
            pd.errors.ParserError,
        ) as exc:
            raise HTTPException(
                status_code=400,
                detail="The file is not a readable CSV.",
            ) from exc

        # Retain the existing company dataset requirements.
        missing_columns = sorted(
            REQUIRED_COLUMNS - set(headers)
        )

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "CSV is missing required columns.",
                    "missing_columns": missing_columns,
                },
            )

        # Save the uploaded file temporarily for the agent.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".csv",
            delete=False,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        # Run the LangGraph workflow.
        result = agent.invoke(
            {"input_path": temp_path}
        )

        # Return validation and statistical analysis together.
        response_data = build_response(result)

        return response_data

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"CSV processing failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "CSV processing or report generation failed. "
                "Check the server logs."
            ),
        ) from exc

    finally:
        await file.close()

        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


# ---------- Retrieve the generated report ----------

@app.get("/report", response_class=PlainTextResponse)
def get_report():
    """Return the latest generated Markdown report."""

    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No report exists yet. Run validation first.",
        )

    return REPORT_PATH.read_text(encoding="utf-8")
