from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json

try:
    from redis import Redis
    redis_installed = True
except ImportError:
    redis_installed = False

class BaseStorage(ABC):
    @abstractmethod
    def get_state(self, user_id: int) -> Optional[str]:
        pass
    
    @abstractmethod
    def set_state(self, user_id: int, state: str):
        pass
    
    @abstractmethod
    def get_data(self, user_id: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def set_data(self, user_id: int, data: Dict[str, Any]):
        pass
    
    @abstractmethod
    def delete(self, user_id: int):
        pass

class MemoryStorage(BaseStorage):
    def __init__(self):
        self._states = {}
        self._data = {}
    
    def get_state(self, user_id: int) -> Optional[str]:
        return self._states.get(user_id)
    
    def set_state(self, user_id: int, state: str):
        self._states[user_id] = state
    
    def get_data(self, user_id: int) -> Dict[str, Any]:
        return self._data.get(user_id, {}).copy()
    
    def set_data(self, user_id: int, data: Dict[str, Any]):
        self._data[user_id] = data
    
    def delete(self, user_id: int):
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)

class RedisStorage(BaseStorage):
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        if not redis_installed:
            raise ImportError("Redis is not installed.")
        self.redis = Redis(
            host=host, 
            port=port, 
            db=db, 
            password=password,
            decode_responses=True
        )
    
    def _state_key(self, user_id: int) -> str:
        return f"vkbot:state:{user_id}"
    
    def _data_key(self, user_id: int) -> str:
        return f"vkbot:data:{user_id}"
    
    def get_state(self, user_id: int) -> Optional[str]:
        return self.redis.get(self._state_key(user_id))
    
    def set_state(self, user_id: int, state: str):
        self.redis.set(self._state_key(user_id), state)
    
    def get_data(self, user_id: int) -> Dict[str, Any]:
        data = self.redis.get(self._data_key(user_id))
        return json.loads(data) if data else {}
    
    def set_data(self, user_id: int, data: Dict[str, Any]):
        self.redis.set(self._data_key(user_id), json.dumps(data))
    
    def delete(self, user_id: int):
        self.redis.delete(self._state_key(user_id))
        self.redis.delete(self._data_key(user_id))