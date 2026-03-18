from typing import Any


def build_ssml(speech_text: str) -> str:
    escaped = (
        speech_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"<speak>{escaped}</speak>"


def build_alexa_response(
    speech_text: str,
    *,
    audio_url: str | None = None,
    story_id: int | None = None,
    scene_id: int | None = None,
    scene_order: int | None = None,
    end_session: bool = False,
    session_attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "response": {
            "speech_text": speech_text,
            "ssml": build_ssml(speech_text),
            "audio_url": audio_url,
            "story_id": story_id,
            "scene_id": scene_id,
            "scene_order": scene_order,
            "end_session": end_session,
        },
        "session_attributes": session_attributes or {},
    }
