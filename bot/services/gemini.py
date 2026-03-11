from google import genai
from google.genai.types import GenerateContentConfig

from bot.settings import settings

_client = genai.Client(api_key=settings.gemini_api_key)


async def translate_text(text: str, target_language: str) -> str:
    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=text,
        config=GenerateContentConfig(
            system_instruction=(
                f"You are a professional translator. "
                f"Translate the following text to {target_language}. "
                f"Output ONLY the translation, nothing else. "
                f"Preserve the original formatting and tone."
            ),
        ),
    )
    return response.text.strip()


async def transcribe_and_translate(audio_bytes: bytes, target_language: str) -> str:
    from google.genai.types import Content, Part

    audio_part = Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=Content(parts=[audio_part]),
        config=GenerateContentConfig(
            system_instruction=(
                f"You are a professional translator and transcriber. "
                f"First, transcribe the audio message. "
                f"Then translate the transcription to {target_language}. "
                f"Output the result in this format:\n"
                f"[Original]: <transcription in original language>\n"
                f"[Translation]: <translation to {target_language}>"
            ),
        ),
    )
    return response.text.strip()


async def translate_disclaimer(target_language: str) -> str:
    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=(
            "Translate this phrase to "
            f"{target_language}: "
            "'Translated using AI. Errors or misunderstandings are possible.'"
        ),
        config=GenerateContentConfig(
            system_instruction=(
                "You are a translator. Output ONLY the translated phrase. "
                "Nothing else. No quotes."
            ),
        ),
    )
    return response.text.strip()
