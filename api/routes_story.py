
from fastapi import APIRouter
from story_engine.story_engine import StoryEngine

router = APIRouter(prefix="/story")

@router.post("/start")
def start_story():
    engine = StoryEngine()
    story = engine.run_story()
    return {"story":story}
