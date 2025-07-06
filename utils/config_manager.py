### utils/config_manager.py ###
import os
from typing import Any, Dict
from asyncio import Lock as AsyncLock
from utils.helpers import load_yaml


class AsyncConfigManager:
    _instances: Dict[str, "AsyncConfigManager"] = {}
    _locks: Dict[str, AsyncLock] = {}

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("Use `await AsyncConfigManager.get_instance(path)` instead")

    @classmethod
    async def get_instance(cls, config_path: str):
        abs_path = os.path.abspath(config_path)

        # Buat lock khusus untuk setiap file config
        if abs_path not in cls._locks:
            cls._locks[abs_path] = AsyncLock()

        async with cls._locks[abs_path]:
            if abs_path not in cls._instances:
                self = super().__new__(cls)
                await self._init(abs_path)
                cls._instances[abs_path] = self
            return cls._instances[abs_path]

    async def _init(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        self._path = config_path
        self._config = await load_yaml(config_path)

    def get(self, *keys: str, default: Any = None) -> Any:
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_section(self, section: str) -> dict:
        return self._config.get(section, {})

    def as_dict(self) -> dict:
        return self._config

    def path(self) -> str:
        return self._path
