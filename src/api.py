
import io
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from src.agent import agent


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

app = FastAPI(
    title="Business Data Quality Agent",
    description=(
        "Validate company data and generate AI-assisted "
        "business insights using Python, LangGraph, and Ollama."
    ),
    version="0.3.0",
)



def build_response(result: dict) -> dict:
    validation = result["validation_report"]

    return {
        "status": "success",
        "message": "Validation workflow completed.",
        "ai_status": result.get("ai_status", "unknown"),
        "summary": {
            "total_records": validation["total_records"],
            "total_issues": validation["total_issues"],
            "affected_records": validation["affected_records"],
            "issues_by_severity": validation["issues_by_severity"],
            "issues_by_rule": validation["issues_by_rule"],
        },
        "issues": validation["issues"],
        "evidence": result.get("evidence_summary", {}),
        "report": result["final_report"],
    }



@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Business Data Quality Agent",
    }


@app.post("/run-validation")
def run_validation():
    """Run validation on the default project dataset."""
    try:
        result = agent.invoke({})
        return build_response(result)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Validation workflow failed. Check the server logs.",
        )


@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Validate an uploaded CSV and return structured findings."""
    if not file.filename or Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Please upload a file with a .csv extension.",
        )

    temp_path = None

    try:
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

        try:
            headers = pd.read_csv(
                io.BytesIO(contents),
                nrows=0,
            ).columns
        except (
            ValueError,
            UnicodeDecodeError,
            pd.errors.ParserError,
        ):
            raise HTTPException(
                status_code=400,
                detail="The file is not a readable CSV.",
            )

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

        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".csv",
            delete=False,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        result = agent.invoke({"input_path": temp_path})
        return build_response(result)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "CSV processing or report generation failed. "
                "Check the server logs."
            ),
        )
    finally:
        await file.close()

        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@app.get("/report", response_class=PlainTextResponse)
def get_report():
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No report exists yet. Run validation first.",
        )

    return REPORT_PATH.read_text(encoding="utf-8")
