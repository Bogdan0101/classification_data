import asyncio
from app.services.llm import request_gemini_async
from typing import List, Dict, Any


async def process_csv(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    semaphore = asyncio.Semaphore(value=1)

    async def worker(record: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            raw_text = str(record.get("raw_text", ""))
            max_retries = 4
            llm_data = {
                "category": "out_of_scope",
                "priority": "low",
                "target_department": "unassigned",
                "short_summary": "None",
                "needs_clarification": True,
                "clarification_reason": "None",
            }
            for attempt in range(max_retries):
                try:
                    llm_response = await request_gemini_async(raw_text)
                    data_dict = llm_response.model_dump()
                    for key in ["category", "priority", "target_department"]:
                        if hasattr(data_dict.get(key), "value"):
                            data_dict[key] = data_dict[key].value
                    llm_data = data_dict
                    break
                except Exception as e:
                    err_message = str(e)
                    if any(
                            code in err_message
                            for code in [
                                "429",
                                "503",
                                "RESOURCE_EXHAUSTED",
                                "UNAVAILABLE"
                            ]
                    ):
                        wait_time = (attempt + 1) * 2
                        await asyncio.sleep(wait_time)
                    else:
                        llm_data["short_summary"] = f"Error: {err_message}"
                        llm_data["clarification_reason"] = err_message
                        break
            await asyncio.sleep(2)
            return {**record, **llm_data}

    tasks = [worker(record) for record in records]
    results = await asyncio.gather(*tasks)
    return list(results)
