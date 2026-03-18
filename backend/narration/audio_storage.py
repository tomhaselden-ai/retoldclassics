import os
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from backend.config.settings import AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class AudioStorageService:
    def __init__(self) -> None:
        if not S3_BUCKET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3_BUCKET is not configured",
            )

        self._bucket = S3_BUCKET
        bootstrap_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )
        self._bucket_region = self._resolve_bucket_region(bootstrap_client)
        self._client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=self._bucket_region,
            config=Config(signature_version="s3v4"),
        )

    def _resolve_bucket_region(self, client) -> str:
        try:
            response = client.get_bucket_location(Bucket=self._bucket)
        except (BotoCoreError, ClientError):
            return AWS_REGION

        location = response.get("LocationConstraint")
        if not location:
            return "us-east-1"
        return location

    def upload_scene_audio(self, story_id: int, scene_id: int, audio_bytes: bytes) -> str:
        object_key = f"stories/{story_id}/scene_{scene_id}.mp3"
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=audio_bytes,
                ContentType="audio/mpeg",
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="S3 upload failed",
            ) from exc

        return self.build_public_audio_url(object_key)

    def build_public_audio_url(self, object_key: str) -> str:
        return f"https://{self._bucket}.s3.{self._bucket_region}.amazonaws.com/{object_key}"

    def _extract_object_key(self, audio_url: str | None) -> str | None:
        if not audio_url:
            return None

        parsed = urlparse(audio_url)
        if parsed.scheme not in {"http", "https"}:
            return None

        host = parsed.netloc
        if not host.startswith(f"{self._bucket}.s3."):
            return None

        return parsed.path.lstrip("/") or None

    def normalize_audio_url(self, audio_url: str | None) -> str | None:
        if not audio_url:
            return None

        object_key = self._extract_object_key(audio_url)
        if not object_key:
            return audio_url

        return self.build_public_audio_url(object_key)

    def create_playback_url(self, audio_url: str | None, expires_in: int = 3600) -> str | None:
        normalized = self.normalize_audio_url(audio_url)
        object_key = self._extract_object_key(normalized)
        if not object_key:
            return normalized

        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except (BotoCoreError, ClientError):
            return normalized
