import asyncio
from app.services.llm import RequestGemini
from typing import List
from app.schemas import RowSchema, ResultSchema


class ProcessorCSV:

    @staticmethod
    async def _worker(record: RowSchema) -> ResultSchema:
        gemini = RequestGemini()
        llm_response = await gemini.async_request(record.raw_text)

        result = ResultSchema(
            id=record.id,
            channel=record.channel,
            short_summary=llm_response.short_summary,
            category=llm_response.category,
            target_department=llm_response.target_department,
            priority=llm_response.priority,
            needs_clarification=llm_response.needs_clarification,
            clarification_reason=llm_response.clarification_reason,

        )
        return ResultSchema.model_validate(result)

    async def run_process_csv(self, records: List[RowSchema]) -> List[ResultSchema]:
        tasks = [self._worker(record) for record in records]
        results = await asyncio.gather(*tasks)
        return list(results)
