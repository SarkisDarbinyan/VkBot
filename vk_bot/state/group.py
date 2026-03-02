from vk_bot.state.manager import State


class StatesGroupMeta(type):
    def __new__(mcs, name, bases, namespace):
        states = {}
        for key, value in namespace.items():
            if isinstance(value, State):
                states[key] = value

        cls = super().__new__(mcs, name, bases, namespace)
        cls._states = states

        for state_name, state in states.items():
            if not state._name:
                state._name = f"{cls.__name__}:{state_name}"

        return cls

    def __contains__(cls, item: str) -> bool:
        return any(state._name == item for state in cls._states.values())

    def __iter__(cls):
        return iter(cls._states.values())

    def __repr__(cls) -> str:
        return f"<StatesGroup '{cls.__name__}'>"


class StatesGroup(metaclass=StatesGroupMeta):
    @classmethod
    def get_state(cls, name: str) -> str | None:
        state = cls._states.get(name)
        return state._name if state else None

    @classmethod
    def get_all_states(cls) -> list[str]:
        return [state._name for state in cls._states.values()]

    @classmethod
    def is_in_group(cls, state: str) -> bool:
        return any(state == s._name for s in cls._states.values())
