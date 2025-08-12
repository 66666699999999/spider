import os
import tomllib
from pathlib import Path
from typing import Dict, Any

FILE = Path(__file__).resolve()
project_root = FILE.parents[2]


class Config:
    def __init__(self) -> None:
        self.ROOT_PATH = project_root
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件并缓存配置数据"""
        config_path = self.ROOT_PATH / "app" / "config" / "config.toml"
        try:
            with open(config_path, "rb") as f:
                self._config_data = tomllib.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            self._config_data = {}

    def load_file(self) -> Dict[str, Any]:
        """获取配置数据"""
        return self._config_data
