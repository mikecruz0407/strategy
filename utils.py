import os
import json

FAVS_PATH = "favorites.json"

def load_favorites():
    if not os.path.exists(FAVS_PATH):
        return []
    try:
        with open(FAVS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_favorites(favs):
    try:
        with open(FAVS_PATH, "w") as f:
            json.dump(sorted(set(favs)), f, indent=2)
    except Exception:
        pass
