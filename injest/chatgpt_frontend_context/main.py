from fastapi import FastAPI

from backend.api.adaptive_routes import router as adaptive_router
from backend.api.analytics_routes import router as analytics_router
from backend.api.alexa_routes import router as alexa_router
from backend.api.continuity_routes import router as continuity_router
from backend.api.epub_routes import router as epub_router
from backend.api.auth_routes import router as auth_router
from backend.api.dashboard_routes import router as dashboard_router
from backend.api.game_routes import router as game_router
from backend.api.illustration_routes import router as illustration_router
from backend.api.library_routes import router as library_router
from backend.api.memory_routes import router as memory_router
from backend.api.narration_routes import router as narration_router
from backend.api.reading_routes import router as reading_router
from backend.api.reader_routes import router as reader_router
from backend.api.safety_routes import router as safety_router
from backend.api.scaling_routes import router as scaling_router
from backend.api.story_routes import router as story_router
from backend.api.vocabulary_routes import router as vocabulary_router
from backend.api.world_routes import router as world_router


app = FastAPI(title="Persistent Story Universe API")

app.include_router(adaptive_router)
app.include_router(analytics_router)
app.include_router(alexa_router)
app.include_router(continuity_router)
app.include_router(epub_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(game_router)
app.include_router(illustration_router)
app.include_router(library_router)
app.include_router(memory_router)
app.include_router(narration_router)
app.include_router(reading_router)
app.include_router(reader_router)
app.include_router(safety_router)
app.include_router(scaling_router)
app.include_router(story_router)
app.include_router(vocabulary_router)
app.include_router(world_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
