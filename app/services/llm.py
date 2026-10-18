import asyncio
from pydantic import ValidationError
from google.genai.errors import APIError
from google import genai
from google.genai import types
from app.config import settings
from app.schemas import LLMClassificationResponse

client = genai.Client(api_key=settings.GEMINI_API_KEY)
model_llm = settings.GEMINI_MODEL
gemini_semaphore = asyncio.Semaphore(value=1)


class RequestGemini:

    @staticmethod
    async def async_request(raw_text) -> LLMClassificationResponse:
        system_instruction = (
            "You are an AI System Analyst. "
            "Analyze the incoming request from internal team "
            "and extract structured data according "
            "to the provided Pydantic schema."
        )
        max_retries = 4
        async with gemini_semaphore:
            for attempt in range(max_retries):
                try:
                    response = await client.aio.models.generate_content(
                        model=model_llm,
                        contents=f"Request text: {raw_text}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=LLMClassificationResponse,
                            temperature=0.1,
                        ),
                    )
                    return response.parsed
                except asyncio.TimeoutError as e:
                    if attempt == max_retries - 1:
                        return LLMClassificationResponse(
                            short_summary=f"Error: Timeout after {max_retries} attempts.",
                            clarification_reason=str(e),
                        )
                    await asyncio.sleep((attempt + 1) * 2)
                except APIError as e:
                    if e.code in [429, 503]:
                        if attempt == max_retries - 1:
                            return LLMClassificationResponse(
                                short_summary="Error: API limit or unavailable.",
                                clarification_reason=str(e),
                            )
                        await asyncio.sleep((attempt + 1) * 2)
                    else:
                        return LLMClassificationResponse(
                            short_summary=f"Error: API error code: {e.code}",
                            clarification_reason=str(e),
                        )
                except ValidationError as e:
                    return LLMClassificationResponse(
                        short_summary="Pydantic validation error",
                        clarification_reason=str(e),
                    )
