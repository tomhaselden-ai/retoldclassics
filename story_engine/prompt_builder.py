
import json, pathlib
CONFIG = pathlib.Path(__file__).resolve().parent.parent / "universe_config"

def load(name):
    with open(CONFIG / name) as f:
        return json.load(f)

def build_prompt(scene):
    world = load("world.json")
    director = load("story_director.json")
    child = load("child_profile.json")
    scene_state = load("scene_state.json")

    return f"""
WORLD
{world}

DIRECTOR
{director}

CHILD
{child}

SCENE
{scene_state}

CURRENT_STAGE
{scene}
"""
