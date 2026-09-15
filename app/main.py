import csv

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import io
import pandas as pd
from app.services.processor import process_csv
from app.services.reporter import generate_reports

app = FastAPI(title="classification data FastAPI")
templates = Jinja2Templates(directory="templates")

RESULTS_CSV_FILE: List[Dict[str, Any]] = []


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
            status_code=400,
            detail="File must end with .csv",
        )
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        records = df.to_dict(orient="records")
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail=f"File failed to load. Error: {err}",
        )

    results = await process_csv(records)
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
            status_code=400,
            detail="No results CSV file.",
        )
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "id",
            "channel",
            "short_summary",
            "category",
            "target_department",
            "priority",
            "needs_clarification",
            "clarification_reason",
        ]
    )
    for item in RESULTS_CSV_FILE:
        writer.writerow(
            [
                item.get("id", "-"),
                item.get("channel", "-"),
                item.get("short_summary", "-"),
                item.get("category", "-"),
                item.get("target_department", "-"),
                item.get("priority", "-"),
                item.get("needs_clarification", "-"),
                item.get("clarification_reason", "-"),
            ]
        )
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=classification_report.csv"
        },
    )
