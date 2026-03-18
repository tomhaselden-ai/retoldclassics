
from story_engine.scene_planner import ScenePlanner
from story_engine.prompt_builder import build_prompt

class StoryGenerator:
    def generate(self,prompt:str)->str:
        return "Once upon a time in Silverwood Forest..."

class StoryEngine:
    def __init__(self):
        self.generator = StoryGenerator()
        self.planner = ScenePlanner()

    def run_story(self):
        scenes = self.planner.plan()
        story=[]
        for scene in scenes:
            prompt = build_prompt(scene)
            text = self.generator.generate(prompt)
            story.append(text)
        return story
