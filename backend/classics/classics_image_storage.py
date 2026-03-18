from pathlib import Path

from fastapi import HTTPException, status


BASE_CLASSICS_IMAGE_DIR = Path(__file__).resolve().parent.parent / "media" / "classics_images"
BASE_IMAGE_ROUTE = "/media/classics-images"


class ClassicsImageStorage:
    def __init__(self) -> None:
        BASE_CLASSICS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    def save_scene_illustration(self, story_id: int, illustration_key: int, image_bytes: bytes) -> str:
        image_path = BASE_CLASSICS_IMAGE_DIR / f"story_{story_id}_scene_{illustration_key}.png"
        try:
            image_path.write_bytes(image_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classics illustration could not be saved",
            ) from exc

        return f"{BASE_IMAGE_ROUTE}/story_{story_id}_scene_{illustration_key}.png"

    def image_exists(self, image_url: str | None) -> bool:
        if not image_url or not image_url.startswith(f"{BASE_IMAGE_ROUTE}/"):
            return False
        filename = image_url.removeprefix(f"{BASE_IMAGE_ROUTE}/")
        return (BASE_CLASSICS_IMAGE_DIR / filename).exists()
