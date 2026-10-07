import asyncio
from app.services.llm import request_gemini_async
from typing import List
from app.schemas import RowSchema, LLMResponseSchema, ResultSchema


async def process_csv(records: List[RowSchema]) -> List[ResultSchema]:
    semaphore = asyncio.Semaphore(value=1)

    async def worker(record: RowSchema) -> ResultSchema:
        async with semaphore:
            raw_text = record.raw_text
            max_retries = 4
            llm_data = LLMResponseSchema().model_dump()
            for attempt in range(max_retries):
                try:
                    llm_response = await request_gemini_async(raw_text)
                    llm_data = llm_response.model_dump(mode="json")
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

            row_dict = {**record.model_dump(mode="json"), **llm_data}
            return ResultSchema.model_validate(row_dict)

    tasks = [worker(record) for record in records]
    results = await asyncio.gather(*tasks)
    return list(results)
