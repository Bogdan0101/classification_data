import asyncio
from app.services.llm import request_gemini_async
from typing import List
from pydantic import ValidationError
from google.genai.errors import APIError
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

                except asyncio.TimeoutError as e:
                    if attempt == max_retries - 1:
                        llm_data = {
                            "short_summary": f"Error: Timeout after {max_retries} attempts.",
                            "clarification_reason": str(e),
                        }
                        break
                    await asyncio.sleep((attempt + 1) * 2)
                except APIError as e:
                    if e.code in [429, 503]:
                        if attempt == max_retries - 1:
                            llm_data = {
                                "short_summary": "Error: API limit or unavailable.",
                                "clarification_reason": str(e),
                            }
                            break
                        await asyncio.sleep((attempt + 1) * 2)
                    else:
                        llm_data = {
                            "short_summary": f"Error: API error code: {e.code}",
                            "clarification_reason": str(e),
                        }
                        break
                except ValidationError as e:
                    llm_data = {
                        "short_summary": "Pydantic validation error",
                        "clarification_reason": str(e),
                    }
                    break

            await asyncio.sleep(2)

            row_dict = {**record.model_dump(mode="json"), **llm_data}
            return ResultSchema.model_validate(row_dict)

    tasks = [worker(record) for record in records]
    results = await asyncio.gather(*tasks)
    return list(results)
