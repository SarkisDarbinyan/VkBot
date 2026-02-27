import json
from abc import ABC, abstractmethod
from typing import Any

try:
    from redis import Redis

    redis_installed = True
except ImportError:
    redis_installed = False


class BaseStorage(ABC):
    """Abstract base class for state storage backends."""

    @abstractmethod
    def get_state(self, user_id: int) -> str | None:
        pass

    @abstractmethod
    def set_state(self, user_id: int, state: str):
        pass

    @abstractmethod
    def get_data(self, user_id: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def set_data(self, user_id: int, data: dict[str, Any]):
        pass

    @abstractmethod
    def delete(self, user_id: int):
        pass


class MemoryStorage(BaseStorage):
    """In-memory state storage.

    Data is lost on restart. Suitable for development.
    """

    def __init__(self):
        self._states = {}
        self._data = {}

    def get_state(self, user_id: int) -> str | None:
        return self._states.get(user_id)

    def set_state(self, user_id: int, state: str):
        self._states[user_id] = state

    def get_data(self, user_id: int) -> dict[str, Any]:
        return self._data.get(user_id, {}).copy()

    def set_data(self, user_id: int, data: dict[str, Any]):
        self._data[user_id] = data

    def delete(self, user_id: int):
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)


class RedisStorage(BaseStorage):
    """Redis-backed state storage.

    Persistent storage. Suitable for production.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        if not redis_installed:
            raise ImportError("Redis is not installed.")
        self.redis = Redis(
            host=host, port=port, db=db, password=password, decode_responses=True
        )

    def _state_key(self, user_id: int) -> str:
        return f"vkbot:state:{user_id}"

    def _data_key(self, user_id: int) -> str:
        return f"vkbot:data:{user_id}"

    def get_state(self, user_id: int) -> str | None:
        return self.redis.get(self._state_key(user_id))

    def set_state(self, user_id: int, state: str):
        self.redis.set(self._state_key(user_id), state)

    def get_data(self, user_id: int) -> dict[str, Any]:
        data = self.redis.get(self._data_key(user_id))
        return json.loads(data) if data else {}

    def set_data(self, user_id: int, data: dict[str, Any]):
        self.redis.set(self._data_key(user_id), json.dumps(data))

    def delete(self, user_id: int):
        self.redis.delete(self._state_key(user_id))
        self.redis.delete(self._data_key(user_id))
