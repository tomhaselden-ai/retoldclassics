from pathlib import Path

from fastapi import HTTPException, status


BASE_IMAGE_DIR = Path(__file__).resolve().parent.parent / "images" / "stories"
BASE_IMAGE_ROUTE = "/media/generated-illustrations"


class IllustrationImageStorage:
    def save_story_cover(self, story_id: int, image_bytes: bytes) -> str:
        story_dir = BASE_IMAGE_DIR / str(story_id)
        image_path = story_dir / "story_cover.png"

        try:
            story_dir.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(image_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Illustration image could not be saved",
            ) from exc

        return str(image_path)

    def save_scene_illustration(self, story_id: int, scene_id: int, image_bytes: bytes) -> str:
        story_dir = BASE_IMAGE_DIR / str(story_id)
        image_path = story_dir / f"scene_{scene_id}.png"

        try:
            story_dir.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(image_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Illustration image could not be saved",
            ) from exc

        return str(image_path)

    def get_scene_public_url(self, story_id: int, scene_id: int) -> str:
        return f"{BASE_IMAGE_ROUTE}/{story_id}/scene_{scene_id}.png"

    def get_story_cover_public_url(self, story_id: int) -> str:
        return f"{BASE_IMAGE_ROUTE}/{story_id}/story_cover.png"

    def resolve_local_asset(self, asset_path: str | None) -> Path | None:
        if not asset_path:
            return None

        path = Path(asset_path)
        if path.is_file():
            return path

        if asset_path.startswith(f"{BASE_IMAGE_ROUTE}/"):
            relative_path = asset_path.removeprefix(f"{BASE_IMAGE_ROUTE}/")
            candidate = BASE_IMAGE_DIR / relative_path
            if candidate.is_file():
                return candidate

        return None

    def normalize_public_url(self, asset_path: str | None) -> str | None:
        if not asset_path:
            return None

        if asset_path.startswith(BASE_IMAGE_ROUTE):
            return asset_path

        local_path = self.resolve_local_asset(asset_path)
        if local_path is None:
            return asset_path

        try:
            relative_path = local_path.relative_to(BASE_IMAGE_DIR).as_posix()
            return f"{BASE_IMAGE_ROUTE}/{relative_path}"
        except ValueError:
            return asset_path
