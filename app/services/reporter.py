import json
from typing import List, Dict, Any
import pandas as pd
from app.schemas import ResultSchema


def generate_reports(results: List[ResultSchema]) -> Dict[str, Any]:
    clean_results = [result.model_dump(mode="json") for result in results]

    output_json_str = json.dumps(clean_results, ensure_ascii=False, indent=2)

    df = pd.DataFrame(clean_results)

    by_category = df["category"].value_counts().to_dict()
    by_priority = df["priority"].value_counts().to_dict()
    by_department = (
        df["target_department"].fillna("unassigned").value_counts().to_dict()
    )

    clarification_list = [
        {
            "id": result.id,
            "short_summary": result.short_summary,
            "clarification_reason": result.clarification_reason or "-",
        }
        for result in results
        if result.needs_clarification
    ]
    clarification_list_count = len(clarification_list)

    cat_md = (
        pd.Series(by_category).to_markdown() if by_category else "Немає даних"
    )
    prio_md = (
        pd.Series(by_priority).to_markdown() if by_priority else "Немає даних"
    )
    dep_md = (
        pd.Series(by_department).to_markdown()
        if by_department
        else "Немає даних"
    )

    markdown_lines = [
        "Звіт за результатами класифікації запитів:",
        "!!! По категоріях",
        cat_md,
        "!!! По пріоритету",
        prio_md,
        "!!! По відділах",
        dep_md,
        "----------------------------------------",
        f"Запити що потребують уточнення({clarification_list_count})"
    ]

    markdown_report = "\n".join(markdown_lines) + "\n"

    for item in clarification_list:
        markdown_report += (
            f'**{item["id"]}**: '
            f'{item["short_summary"]}\n '
            f'Причина: {item["clarification_reason"]}\n'
        )

    return {
        "json_data": output_json_str,
        "markdown_report": markdown_report,
        "summary_stats": {
            "by_category": by_category,
            "by_priority": by_priority,
            "by_department": by_department,
            "needs_clarification_count": clarification_list_count,
        },
    }
