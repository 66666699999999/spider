import tomllib
import os
from pathlib import Path

FILE = Path(__file__).resolve()
project_root = FILE.parents[2]
print(project_root)

class Config:
    def __init__(self):
        self.ROOT_PATH = project_root

    def load_file(self):
        path = self.ROOT_PATH / "app" / "config" / "config.toml"
        with open(path, "rb") as f:
            config = tomllib.load(f)
        return config
