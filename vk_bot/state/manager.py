from typing import Any

from vk_bot.state.storage import BaseStorage, MemoryStorage


class StateManager:
    def __init__(self, storage: BaseStorage | None = None):
        self.storage = storage or MemoryStorage()

    def get_state(self, user_id: int) -> str | None:
        return self.storage.get_state(user_id)

    def set_state(self, user_id: int, state: str):
        self.storage.set_state(user_id, state)

    def get_data(self, user_id: int) -> dict[str, Any]:
        return self.storage.get_data(user_id)

    def set_data(self, user_id: int, data: dict[str, Any]):
        self.storage.set_data(user_id, data)

    def update_data(self, user_id: int, **kwargs):
        data = self.get_data(user_id)
        data.update(kwargs)
        self.set_data(user_id, data)

    def reset(self, user_id: int):
        self.storage.delete(user_id)


class State:
    def __init__(self, name: str | None = None):
        self._name = name

    def __set_name__(self, owner, name):
        if not self._name:
            self._name = f"{owner.__name__}:{name}"

    def __get__(self, obj, objtype=None):
        return self._name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"State({self._name})"
