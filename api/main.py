
from fastapi import FastAPI
from api.routes_story import router as story_router

app = FastAPI(title="Persistent Story Universe API")

app.include_router(story_router)

@app.get("/")
def root():
    return {"status":"Story Universe API running"}
