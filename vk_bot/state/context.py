from typing import Optional, Dict, Any, TYPE_CHECKING
from .manager import StateManager

if TYPE_CHECKING:
    from .. import VKBot

class StateContext:
    
    def __init__(self, bot: 'VKBot', user_id: int):
        self.bot = bot
        self.user_id = user_id
        self._manager = bot.state_manager
    
    @property
    def current(self) -> Optional[str]:
        return self._manager.get_state(self.user_id)
    
    def set(self, state: str):
        self._manager.set_state(self.user_id, state)
    
    def get(self) -> Optional[str]:
        return self.current
    
    def finish(self):
        self._manager.reset(self.user_id)
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._manager.get_data(self.user_id)
    
    def update(self, **kwargs):
        self._manager.update_data(self.user_id, **kwargs)
    
    def clear_data(self):
        self._manager.set_data(self.user_id, {})
    
    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)
    
    def __setitem__(self, key: str, value: Any):
        self.update(**{key: value})
    
    def __contains__(self, key: str) -> bool:
        return key in self.data