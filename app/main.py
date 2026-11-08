import csv
import io
import uuid
import pandas as pd

from fastapi import FastAPI, UploadFile, File, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional, Union

from pandas.errors import EmptyDataError, ParserError
from pydantic import ValidationError

from app.services.processor import ProcessorCSV
from app.services.reporter import Reporter
from app.schemas import RowSchema, ResultSchema

app = FastAPI(title="classification data FastAPI")
templates = Jinja2Templates(directory="templates")

RESULTS_CSV_FILE: Dict[str, Union[None, str, List[ResultSchema]]] = {}
processor = ProcessorCSV()
reporter = Reporter()


async def process_csv_in_background(task_id: str, validated_records: List[RowSchema]):
    """Фонова задача, яка працює, поки користувач дивиться на лоадер"""
    try:
        results = await processor.run_process_csv(validated_records)
        RESULTS_CSV_FILE[task_id] = results
    except Exception as e:
        RESULTS_CSV_FILE[task_id] = "error"
        print(f"Error processing task {task_id}: {e}")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, task_id: Optional[str] = None):
    results = None
    stats = None
    markdown_report = None

    if task_id and task_id in RESULTS_CSV_FILE:
        data = RESULTS_CSV_FILE[task_id]
        if isinstance(data, list):
            results = data
            reports = reporter.generate_reports(results)
            stats = reports["summary_stats"]
            markdown_report = reports["markdown_report"]


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "results": results,
            "stats": stats,
            "markdown_report": markdown_report,
            "task_id": task_id,
        },
    )


@app.post("/classify-csv", response_class=HTMLResponse)
async def classify_csv(
        request: Request,
        background_task: BackgroundTasks,
        file: UploadFile = File(...)
):
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
    task_id = str(uuid.uuid4())

    RESULTS_CSV_FILE[task_id] = None

    background_task.add_task(process_csv_in_background, task_id, validated_records)

    return templates.TemplateResponse(
        request=request,
        name="payloader.html",
        context={"task_id": task_id}
    )


@app.get("/payloader", response_class=HTMLResponse)
async def payloader(request: Request, task_id: str):
    return templates.TemplateResponse(
        request=request,
        name="payloader.html",
        context={"task_id": task_id}
    )

@app.get("/check-status")
def check_status(task_id: str):
    """Сервер перевіряє за task_id, чи є результати"""
    results = RESULTS_CSV_FILE.get(task_id)

    if isinstance(results, list):
        return RedirectResponse(url=f"/?task_id={task_id}", status_code=303)
    else:
        return RedirectResponse(url=f"/payloader?task_id={task_id}", status_code=303)


@app.get("/download/report-csv")
async def download_report_csv(task_id: Optional[str] = None):
    results = RESULTS_CSV_FILE.get(task_id) if task_id else None

    if not task_id or not isinstance(results, list):
        raise HTTPException(
            status_code=404,
            detail="No results CSV file available for this task.",
        )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(ResultSchema.get_fields_name())
    for item in results:
        writer.writerow(item.get_fields_value())
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename=classification_report_{task_id[:8]}.csv"
        },
    )
