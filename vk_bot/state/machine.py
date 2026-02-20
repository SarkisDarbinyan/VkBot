from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

class TransitionType(Enum):
    ANY = "any"
    STRICT = "strict"
    AUTO = "auto"

@dataclass
class StateInfo:
    name: str
    group: Optional[str] = None
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    timeout: Optional[int] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Transition:
    from_state: str
    to_state: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    priority: int = 0

class FiniteStateMachine:
    def __init__(self, name: str = "default"):
        self.name = name
        self.states: Dict[str, StateInfo] = {}
        self.transitions: List[Transition] = []
        self.initial_state: Optional[str] = None
        self.current_state: Optional[str] = None
        self.on_any_transition: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    def add_state(
        self,
        state: str,
        group: Optional[str] = None,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        timeout: Optional[int] = None,
        retries: int = 0,
        **metadata
    ) -> 'FiniteStateMachine':
        self.states[state] = StateInfo(
            name=state,
            group=group,
            on_enter=on_enter,
            on_exit=on_exit,
            timeout=timeout,
            retries=retries,
            metadata=metadata
        )
        return self
    
    def add_transition(
        self,
        from_state: str,
        to_state: str,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None,
        priority: int = 0
    ) -> 'FiniteStateMachine':
        self.transitions.append(Transition(
            from_state=from_state,
            to_state=to_state,
            condition=condition,
            action=action,
            priority=priority
        ))
        return self
    
    def set_initial(self, state: str) -> 'FiniteStateMachine':
        if state not in self.states:
            raise ValueError(f"State {state} not found")
        self.initial_state = state
        return self
    
    def can_transition(self, from_state: str, to_state: str, context: Any = None) -> bool:
        if from_state not in self.states:
            return False
        
        if not self.transitions:
            return True
        
        for trans in sorted(self.transitions, key=lambda x: -x.priority):
            if trans.from_state == from_state and trans.to_state == to_state:
                if trans.condition:
                    return trans.condition(context)
                return True
            if trans.from_state == '*' and trans.to_state == to_state:
                if trans.condition:
                    return trans.condition(context)
                return True
            if trans.from_state == from_state and trans.to_state == '*':
                if trans.condition:
                    return trans.condition(context)
                return True
        
        return False
    
    def get_next_states(self, from_state: str, context: Any = None) -> List[str]:
        if from_state not in self.states:
            return []
        
        possible = set()
        
        for trans in self.transitions:
            if trans.from_state == from_state or trans.from_state == '*':
                if trans.condition:
                    if trans.condition(context):
                        possible.add(trans.to_state)
                else:
                    possible.add(trans.to_state)
        
        return list(possible)
    
    def transition(
        self,
        from_state: Optional[str],
        to_state: str,
        context: Any = None
    ) -> bool:
        if from_state and from_state in self.states:
            state_info = self.states[from_state]
            if state_info.on_exit:
                state_info.on_exit(context)
        
        if to_state in self.states:
            state_info = self.states[to_state]
            if state_info.on_enter:
                state_info.on_enter(context)
        
        if self.on_any_transition:
            self.on_any_transition(from_state, to_state, context)
        
        self.current_state = to_state
        return True
    
    def reset(self) -> None:
        self.current_state = self.initial_state
    
    def is_state(self, state: str) -> bool:
        return self.current_state == state
    
    def is_in_group(self, group: str) -> bool:
        if not self.current_state:
            return False
        state_info = self.states.get(self.current_state)
        return state_info and state_info.group == group
    
    def __repr__(self) -> str:
        return f"<FSM '{self.name}': {self.current_state}>"

class FSMRegistry:
    _instances: Dict[str, FiniteStateMachine] = {}
    
    @classmethod
    def register(cls, name: str, fsm: FiniteStateMachine) -> None:
        cls._instances[name] = fsm
    
    @classmethod
    def get(cls, name: str) -> Optional[FiniteStateMachine]:
        return cls._instances.get(name)
    
    @classmethod
    def get_or_create(cls, name: str) -> FiniteStateMachine:
        if name not in cls._instances:
            cls._instances[name] = FiniteStateMachine(name)
        return cls._instances[name]