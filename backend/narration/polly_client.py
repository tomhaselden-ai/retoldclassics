from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from backend.config.settings import AWS_ACCESS_KEY, AWS_REGION, AWS_SECRET_KEY, POLLY_DEFAULT_STYLE_MODE
from backend.narration.pronunciation import load_lexicon_names, load_pronunciation_rules
from backend.narration.ssml_builder import build_storytelling_ssml
from backend.narration.text_preprocessor import build_narration_document
from backend.narration.voice_strategy import VoicePlan, list_voice_plan_candidates


DEFAULT_VOICE = "Joanna"


@dataclass(frozen=True)
class PollySynthesisResult:
    audio_bytes: bytes
    speech_marks_raw: str
    voice_plan: VoicePlan
    ssml: str


class PollyNarrationClient:
    def __init__(self) -> None:
        self._client = boto3.client(
            "polly",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )

    def _synthesize_audio_bytes(self, ssml: str, voice_plan: VoicePlan, lexicon_names: list[str]) -> bytes:
        try:
            request = {
                "Text": ssml,
                "TextType": voice_plan.text_type,
                "OutputFormat": voice_plan.output_format,
                "VoiceId": voice_plan.voice_id,
                "Engine": voice_plan.engine,
                "SampleRate": voice_plan.sample_rate,
            }
            if lexicon_names:
                request["LexiconNames"] = lexicon_names
            response = self._client.synthesize_speech(**request)
            return response["AudioStream"].read()
        except (BotoCoreError, ClientError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Amazon Polly audio generation failed",
            ) from exc

    def _synthesize_speech_marks(self, ssml: str, voice_plan: VoicePlan, lexicon_names: list[str]) -> str:
        try:
            request = {
                "Text": ssml,
                "TextType": voice_plan.text_type,
                "OutputFormat": "json",
                "VoiceId": voice_plan.voice_id,
                "Engine": voice_plan.engine,
                "SpeechMarkTypes": ["word", "sentence"],
            }
            if lexicon_names:
                request["LexiconNames"] = lexicon_names
            response = self._client.synthesize_speech(**request)
            return response["AudioStream"].read().decode("utf-8")
        except (BotoCoreError, ClientError, KeyError, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Amazon Polly speech mark generation failed",
            ) from exc

    def _synthesize_with_plan(self, ssml: str, voice_plan: VoicePlan, lexicon_names: list[str], requires_speech_marks: bool) -> tuple[bytes, str]:
        audio_bytes = self._synthesize_audio_bytes(ssml, voice_plan, lexicon_names)
        speech_marks_raw = (
            self._synthesize_speech_marks(ssml, voice_plan, lexicon_names)
            if requires_speech_marks
            else ""
        )
        return audio_bytes, speech_marks_raw

    def synthesize_storytelling_narration(
        self,
        text: str,
        style_mode: str = POLLY_DEFAULT_STYLE_MODE,
        pronunciation_overrides: dict | None = None,
        requires_speech_marks: bool = True,
        preferred_voice_id: str | None = None,
    ) -> PollySynthesisResult:
        pronunciation_rules = load_pronunciation_rules(overrides=pronunciation_overrides)
        candidate_plans = list_voice_plan_candidates(
            style_mode=style_mode,
            requires_speech_marks=requires_speech_marks,
            preferred_voice_id=preferred_voice_id,
        )
        narration_document = build_narration_document(text, style_mode=candidate_plans[0].style_mode)
        ssml = build_storytelling_ssml(narration_document, pronunciation_rules=pronunciation_rules)
        lexicon_names = load_lexicon_names()

        last_http_error: HTTPException | None = None
        for voice_plan in candidate_plans:
            try:
                audio_bytes, speech_marks_raw = self._synthesize_with_plan(
                    ssml,
                    voice_plan,
                    lexicon_names,
                    requires_speech_marks,
                )
                return PollySynthesisResult(
                    audio_bytes=audio_bytes,
                    speech_marks_raw=speech_marks_raw,
                    voice_plan=voice_plan,
                    ssml=ssml,
                )
            except HTTPException as exc:
                last_http_error = exc
                continue

        if last_http_error is not None:
            raise last_http_error
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Amazon Polly audio generation failed",
        )
