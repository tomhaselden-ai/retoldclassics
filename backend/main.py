from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.adaptive_routes import router as adaptive_router
from backend.api.analytics_routes import router as analytics_router
from backend.api.alexa_routes import router as alexa_router
from backend.api.character_canon_routes import router as character_canon_router
from backend.api.continuity_routes import router as continuity_router
from backend.api.classics_routes import router as classics_router
from backend.api.contact_routes import router as contact_router
from backend.api.content_routes import router as content_router
from backend.api.epub_routes import router as epub_router
from backend.api.auth_routes import router as auth_router
from backend.api.dashboard_routes import router as dashboard_router
from backend.api.game_routes import router as game_router
from backend.api.guest_routes import router as guest_router
from backend.api.goal_routes import router as goal_router
from backend.api.illustration_routes import router as illustration_router
from backend.api.library_routes import router as library_router
from backend.api.media_job_routes import router as media_job_router
from backend.api.memory_routes import router as memory_router
from backend.api.narration_routes import router as narration_router
from backend.api.parent_pin_routes import router as parent_pin_router
from backend.api.parent_routes import router as parent_router
from backend.api.reading_routes import router as reading_router
from backend.api.reader_home_routes import router as reader_home_router
from backend.api.reader_routes import router as reader_router
from backend.api.safety_routes import router as safety_router
from backend.api.scaling_routes import router as scaling_router
from backend.api.story_routes import router as story_router
from backend.api.vocabulary_routes import router as vocabulary_router
from backend.api.world_routes import router as world_router
from backend.api.blog_routes import router as blog_router
from backend.classics.classics_audio_storage import BASE_CLASSICS_AUDIO_DIR
from backend.classics.classics_image_storage import BASE_CLASSICS_IMAGE_DIR
from backend.config.runtime_validation import validate_runtime_settings
from backend.db.schema_migrations import (
    ensure_character_canon_schema,
    ensure_content_schema,
    ensure_game_foundation_schema,
    ensure_guest_session_schema,
    ensure_goal_schema,
    ensure_media_job_schema,
    ensure_parent_pin_schema,
    ensure_reader_world_custom_world_schema,
)
from backend.epub.assets_manager import BASE_EPUB_DIR
from backend.visuals.image_storage import BASE_IMAGE_DIR, BASE_IMAGE_ROUTE


app = FastAPI(title="StoryBloom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_CLASSICS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/classics-audio", StaticFiles(directory=str(BASE_CLASSICS_AUDIO_DIR)), name="classics-audio")
BASE_CLASSICS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/classics-images", StaticFiles(directory=str(BASE_CLASSICS_IMAGE_DIR)), name="classics-images")
BASE_EPUB_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/generated-epubs", StaticFiles(directory=str(BASE_EPUB_DIR)), name="generated-epubs")
BASE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount(BASE_IMAGE_ROUTE, StaticFiles(directory=str(BASE_IMAGE_DIR)), name="generated-illustrations")

app.include_router(adaptive_router)
app.include_router(analytics_router)
app.include_router(alexa_router)
app.include_router(blog_router)
app.include_router(classics_router)
app.include_router(character_canon_router)
app.include_router(continuity_router)
app.include_router(contact_router)
app.include_router(content_router)
app.include_router(epub_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(game_router)
app.include_router(guest_router)
app.include_router(goal_router)
app.include_router(illustration_router)
app.include_router(library_router)
app.include_router(media_job_router)
app.include_router(memory_router)
app.include_router(narration_router)
app.include_router(parent_pin_router)
app.include_router(parent_router)
app.include_router(reading_router)
app.include_router(reader_home_router)
app.include_router(reader_router)
app.include_router(safety_router)
app.include_router(scaling_router)
app.include_router(story_router)
app.include_router(vocabulary_router)
app.include_router(world_router)


@app.on_event("startup")
def apply_startup_schema_updates() -> None:
    validate_runtime_settings()
    ensure_reader_world_custom_world_schema()
    ensure_media_job_schema()
    ensure_guest_session_schema()
    ensure_parent_pin_schema()
    ensure_goal_schema()
    ensure_game_foundation_schema()
    ensure_character_canon_schema()
    ensure_content_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
