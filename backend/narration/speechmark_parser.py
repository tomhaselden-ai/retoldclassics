import json

from fastapi import HTTPException, status


def parse_speech_marks(raw_speech_marks: str) -> list[dict]:
    parsed_marks: list[dict] = []

    for line in raw_speech_marks.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid speech marks returned by Polly",
            ) from exc

        parsed_marks.append(
            {
                "time": payload.get("time"),
                "type": payload.get("type"),
                "start": payload.get("start"),
                "end": payload.get("end"),
                "value": payload.get("value"),
            }
        )

    return parsed_marks
