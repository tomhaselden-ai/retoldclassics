from pathlib import Path

from fastapi import HTTPException, status


BASE_CLASSICS_AUDIO_DIR = Path(__file__).resolve().parent.parent / "media" / "classics_audio"
BASE_AUDIO_ROUTE = "/media/classics-audio"


class ClassicsAudioStorage:
    def __init__(self) -> None:
        BASE_CLASSICS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def save_story_audio(self, story_id: int, audio_bytes: bytes) -> str:
        audio_path = BASE_CLASSICS_AUDIO_DIR / f"story_{story_id}.mp3"
        try:
            audio_path.write_bytes(audio_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classics audio could not be saved",
            ) from exc

        return f"{BASE_AUDIO_ROUTE}/story_{story_id}.mp3"

    def audio_exists(self, audio_url: str | None) -> bool:
        if not audio_url or not audio_url.startswith(f"{BASE_AUDIO_ROUTE}/"):
            return False
        filename = audio_url.removeprefix(f"{BASE_AUDIO_ROUTE}/")
        return (BASE_CLASSICS_AUDIO_DIR / filename).exists()
