import logging
import os
import tomllib  # Python 3.11+
from pathlib import Path
from typing import Any, Dict, Union

# 配置日志
logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # 避免重复初始化
        if not hasattr(self, "initialized"):
            self.BASE_DIR = Path(__file__).resolve().parent.parent

            self._load_config()
            self.initialized = True

    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = self.BASE_DIR / "config" / "config.toml"

        try:
            if config_path.exists():
                with open(config_path, "rb") as f:
                    self._config_data = tomllib.load(f)
                logger.info(f"Configuration loaded from {config_path}")
            else:
                logger.warning(f"Config file not found: {config_path}")
                self._config_data = {}
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            self._config_data = {}

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持点号分隔的嵌套键

        Args:
            key: 配置键，支持嵌套如 'database.host'
            default: 默认值

        Returns:
            配置值或默认值
        """
        if "." in key:
            # 处理嵌套配置
            parts = key.split(".")
            value = self._config_data

            try:
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                return value
            except (TypeError, KeyError):
                return default
        else:
            return self._config_data.get(key, default)

    @property
    def data(self) -> Dict[str, Any]:
        """获取所有配置数据"""
        return self._config_data.copy()

    # 常用配置项的便捷访问属性
    @property
    def use_ssh_tunnel(self) -> bool:
        """是否使用SSH隧道"""
        return self.get("USE_SSH_TUNNEL", False)

    @property
    def debug(self) -> bool:
        """调试模式"""
        return self.get("DEBUG", False)


# 全局配置实例
_config_instance = Config()


def get_config() -> Dict[str, Any]:
    """获取所有配置数据（向后兼容）"""
    return _config_instance.data


def get_setting(key: str, default: Any = None) -> Any:
    """获取配置项（向后兼容）"""
    return _config_instance.get(key, default)


# 为了向后兼容，也可以创建一个模块级别的函数来获取配置实例
def get_config_instance() -> Config:
    """获取配置实例"""
    return _config_instance


# 初始化时自动加载配置
_config_instance.reload()

print(_config_instance.BASE_DIR)
