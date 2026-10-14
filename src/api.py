
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from src.agent import agent
from src.validation import validate_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "agent_quality_report.md"

MAX_FILE_SIZE = 10 * 1024 * 1024

app = FastAPI(
    title="AI Data Quality Validator API",
    description=(
        "Generic CSV data quality validation, statistical profiling, "
        "and AI-assisted insights."
    ),
    version="2.0.0",
)


def build_response(result: dict) -> dict:
    """Build a consistent response for the Streamlit dashboard."""
    validation = result.get("validation_report") or {}

    statistical_analysis = validation.get("statistical_analysis") or {}

    return {
        "status": "success",
        "message": "Dataset analysis completed.",
        "dataset_name": validation.get("dataset_name"),
        "ai_status": result.get("ai_status", "unknown"),
        "summary": {
            "total_records": validation.get("total_records", 0),
            "total_columns": validation.get("total_columns", 0),
            "total_issues": validation.get("total_issues", 0),
            "affected_records": validation.get("affected_records", 0),
            "issues_by_severity": validation.get(
                "issues_by_severity", {}
            ),
            "issues_by_rule": validation.get("issues_by_rule", {}),
            "statistical_analysis": statistical_analysis,
        },
        "issues": validation.get("issues", []),
        "evidence": result.get("evidence_summary", {}),
        "report": result.get("final_report", ""),
    }


@app.get("/")
def root():
    return {
        "status": "success",
        "service": "AI Data Quality Validator API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AI Data Quality Validator API",
    }


@app.post("/run-validation")
def run_validation():
    """Validate the default project dataset."""
    try:
        result = agent.invoke({})
        return build_response(result)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dataset validation failed: {str(exc)}",
        ) from exc


@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Validate an uploaded CSV with arbitrary column names.

    No company-specific schema is required.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    if Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .csv file.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The CSV exceeds the 10 MB upload limit.",
        )

    temp_path = None

    try:
        # Check that pandas can read the CSV and that it has columns.
        try:
            preview = pd.read_csv(
                pd.io.common.BytesIO(content),
                nrows=5,
            )
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="Could not read the CSV encoding. Please use UTF-8.",
            ) from exc
        except pd.errors.EmptyDataError as exc:
            raise HTTPException(
                status_code=400,
                detail="The CSV has no readable columns.",
            ) from exc
        except pd.errors.ParserError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CSV format: {str(exc)}",
            ) from exc

        if len(preview.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The CSV must contain a header row.",
            )

        # Store the uploaded data temporarily for the validation workflow.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".csv",
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        # The validator and agent both receive the uploaded dataset.
        result = agent.invoke({"input_path": str(temp_path)})

        response = build_response(result)

        # Return the original upload filename for dashboard display.
        response["dataset_name"] = Path(file.filename).name

        return response

    except HTTPException:
        raise

    except (ValueError, pd.errors.ParserError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze the uploaded dataset: {str(exc)}",
        ) from exc

    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

        await file.close()


@app.get("/report", response_class=PlainTextResponse)
def get_report():
    """Return the latest Markdown report if available."""
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No report is available yet. Run an analysis first.",
        )

    return REPORT_PATH.read_text(encoding="utf-8")
