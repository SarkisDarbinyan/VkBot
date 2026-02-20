from typing import Optional, Dict, Any, TYPE_CHECKING
from .manager import StateManager
from .machine import FiniteStateMachine, FSMRegistry

if TYPE_CHECKING:
    from .. import VKBot

class StateContext:
    def __init__(self, bot: 'VKBot', user_id: int, fsm_name: str = "default"):
        self.bot = bot
        self.user_id = user_id
        self._manager = bot.state_manager
        self._fsm = FSMRegistry.get_or_create(fsm_name)
    
    @property
    def current(self) -> Optional[str]:
        return self._manager.get_state(self.user_id)
    
    @property
    def fsm(self) -> FiniteStateMachine:
        return self._fsm
    
    def set(self, state: str) -> bool:
        current = self.current
        
        if not self._fsm.can_transition(current, state, self):
            raise ValueError(
                f"Transition from '{current}' to '{state}' not allowed"
            )
        
        self._fsm.transition(current, state, self)
        self._manager.set_state(self.user_id, state)
        return True
    
    def get(self) -> Optional[str]:
        return self.current
    
    def finish(self):
        self._manager.reset(self.user_id)
        if self._fsm.current_state:
            self._fsm.transition(self._fsm.current_state, None, self)
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._manager.get_data(self.user_id)
    
    def update(self, **kwargs):
        self._manager.update_data(self.user_id, **kwargs)
    
    def clear_data(self):
        self._manager.set_data(self.user_id, {})
    
    def is_state(self, state: str) -> bool:
        return self.current == state
    
    def is_in_group(self, group: str) -> bool:
        if not self.current:
            return False
        return False
    
    def get_next_states(self) -> list:
        return self._fsm.get_next_states(self.current, self)
    
    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)
    
    def __setitem__(self, key: str, value: Any):
        self.update(**{key: value})
    
    def __contains__(self, key: str) -> bool:
        return key in self.data