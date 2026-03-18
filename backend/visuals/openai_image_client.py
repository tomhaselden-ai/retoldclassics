import base64

from fastapi import HTTPException, status
from openai import OpenAI

from backend.config.settings import OPENAI_API_KEY


IMAGE_MODEL = "gpt-image-1"
IMAGE_SIZE = "1024x1024"


class OpenAIImageClient:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY is not configured",
            )
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_image(self, prompt: str) -> bytes:
        try:
            response = self._client.images.generate(
                model=IMAGE_MODEL,
                prompt=prompt,
                size=IMAGE_SIZE,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI image generation failed",
            ) from exc

        image_data = None
        if getattr(response, "data", None):
            image_data = response.data[0]

        base64_image = getattr(image_data, "b64_json", None)
        if not base64_image:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI image generation returned no image data",
            )

        try:
            return base64.b64decode(base64_image)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI image data could not be decoded",
            ) from exc
