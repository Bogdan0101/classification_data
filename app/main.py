import csv
import io
import pandas as pd

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import List

from pandas.errors import EmptyDataError, ParserError
from pydantic import ValidationError

from app.services.processor import process_csv
from app.services.reporter import generate_reports
from app.schemas import RowSchema, ResultSchema

app = FastAPI(title="classification data FastAPI")
templates = Jinja2Templates(directory="templates")

RESULTS_CSV_FILE: List[ResultSchema] = []


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "results": None,
            "stats": None,
            "markdown_report": None,
        },
    )


@app.post("/classify-csv", response_class=HTMLResponse)
async def classify_csv(request: Request, file: UploadFile = File(...)):
    global RESULTS_CSV_FILE

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail="File must end with .csv",
        )

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        records = df.to_dict(orient="records")
    except (EmptyDataError, ParserError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid CSV structure or empty file: {e}",
        )
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"File encoding error (use UTF-8): {e}",
        )
    except (IOError, OSError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server failed to read uploaded file due to an I/O error: {e}",
        )

    try:
        validated_records = [RowSchema.model_validate(row) for row in records]
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Pydantic validation error {str(e)}",
        )

    results = await process_csv(validated_records)
    reports = generate_reports(results)
    RESULTS_CSV_FILE = results
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "results": results,
            "stats": reports["summary_stats"],
            "markdown_report": reports["markdown_report"],
        },
    )


@app.get("/download/report-csv")
async def download_report_csv():
    if not RESULTS_CSV_FILE:
        raise HTTPException(
            status_code=404,
            detail="No results CSV file.",
        )
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(ResultSchema.get_fields_name())
    for item in RESULTS_CSV_FILE:
        writer.writerow(item.get_fields_value())
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=classification_report.csv"
        },
    )
