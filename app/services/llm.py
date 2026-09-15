import json
import asyncio
from google import genai
from google.genai import types
from app.config import settings
from app.schemas import LLMClassificationResponse

client = genai.Client(api_key=settings.GEMINI_API_KEY)
model_llm = settings.GEMINI_MODEL


async def request_gemini_async(text: str) -> LLMClassificationResponse:
    system_instruction = (
        "You are an AI System Analyst. "
        "Analyze the incoming request from internal team "
        "and extract structured data according "
        "to the provided Pydantic schema."
    )

    def _sync_call():
        return client.models.generate_content(
            model=model_llm,
            contents=f"Request text: {text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=LLMClassificationResponse,
                temperature=0.1,
            ),
        )

    response = await asyncio.to_thread(_sync_call)
    parsed_json = json.loads(response.text)
    return LLMClassificationResponse(**parsed_json)
