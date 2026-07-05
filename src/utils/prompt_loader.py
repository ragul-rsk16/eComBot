from pathlib import Path

def load_prompt(relative_path: str) -> str:
    #Load a markdown prompt file and return it as a string.
    return Path(relative_path).read_text(encoding="utf-8")