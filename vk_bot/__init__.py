__version__ = '0.2.0'

from typing import List, Optional, Union, Callable, Dict, Any
import time
import re
import json
from . import apihelper
from . import types
from . import exception
from . import util
from .state.manager import StateManager
from .state.storage import BaseStorage,MemoryStorage, RedisStorage
from .state.context import StateContext
from .state.group import StatesGroup
from .state.machine import FiniteStateMachine, FSMRegistry
from .handlers import (
    MessageHandler, CallbackQueryHandler, MiddlewareHandler
)

class VKBot:
    def __init__(self, token: str, group_id: int = None, state_storage: BaseStorage = None):
        self.token = token
        self._group_id = group_id
        self._me = None
        self.message_handlers: List[MessageHandler] = []
        self.callback_query_handlers: List[CallbackQueryHandler] = []
        self.middleware_handlers: List[MiddlewareHandler] = []
        self.lp_server = None
        self._polling = False
        self.state_manager = StateManager(state_storage or MemoryStorage())

    @property
    def group_id(self) -> int:
        if self._group_id is None:
            self._group_id = apihelper.get_group_id(self.token)
        return self._group_id

    @property
    def me(self) -> types.User:
        if not self._me:
            data = apihelper.get_me(self.token)
            self._me = types.User.from_dict(data)
        return self._me

    def get_state(self, user_id: int) -> Optional[str]:
        return self.state_manager.get_state(user_id)

    def set_state(self, user_id: int, state: str):
        self.state_manager.set_state(user_id, state)

    def get_state_data(self, user_id: int) -> Dict[str, Any]:
        return self.state_manager.get_data(user_id)

    def update_state_data(self, user_id: int, **kwargs):
        self.state_manager.update_data(user_id, **kwargs)

    def reset_state(self, user_id: int):
        self.state_manager.reset(user_id)

    def _get_state_context(self, user_id: int) -> StateContext:
        return StateContext(self, user_id)

    def message_handler(
        self,
        commands: Optional[List[str]] = None,
        regexp: Optional[str] = None,
        func: Optional[Callable] = None,
        content_types: Optional[List[str]] = None,
        chat_types: Optional[List[str]] = None,
        state: Optional[Union[str, List[str]]] = None
    ):
        def decorator(handler):
            handler_obj = MessageHandler(
                callback=handler,
                commands=commands,
                regexp=regexp,
                func=func,
                content_types=content_types,
                chat_types=chat_types,
                state=state
            )
            self.message_handlers.append(handler_obj)
            return handler
        return decorator

    def callback_query_handler(
        self,
        func: Optional[Callable] = None,
        data: Optional[Union[str, re.Pattern]] = None,
        state: Optional[Union[str, List[str]]] = None
    ):
        def decorator(handler):
            handler_obj = CallbackQueryHandler(
                callback=handler,
                func=func,
                data=data,
                state=state
            )
            self.callback_query_handlers.append(handler_obj)
            return handler
        return decorator

    def middleware_handler(self, update_types: Optional[List[str]] = None):
        def decorator(handler):
            handler_obj = MiddlewareHandler(
                callback=handler,
                update_types=update_types
            )
            self.middleware_handlers.append(handler_obj)
            return handler
        return decorator

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Union[types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup] = None,
        reply_to: int = None,
        **kwargs
    ) -> dict:
        markup_dict = reply_markup.to_dict() if reply_markup else None
        return apihelper.send_message(
            self.token,
            chat_id,
            text,
            reply_markup=markup_dict,
            reply_to=reply_to,
            **kwargs
        )

    def reply_to(self, message: types.Message, text: str, **kwargs) -> dict:
        return self.send_message(
            message.chat.id,
            text,
            reply_to=message.id,
            **kwargs
        )

    def send_photo(
        self,
        chat_id: int,
        photo: Union[str, bytes, object],
        caption: str = None,
        reply_markup: Union[types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup] = None,
        **kwargs
    ) -> dict:
        return apihelper.send_photo(
            self.token,
            chat_id,
            photo,
            caption=caption,
            **kwargs
        )

    def send_document(
        self,
        chat_id: int,
        document: Union[str, bytes, object],
        caption: str = None,
        reply_markup: Union[types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup] = None,
        **kwargs
    ) -> dict:
        return apihelper.send_document(
            self.token,
            chat_id,
            document,
            caption=caption,
            **kwargs
        )

    def answer_callback_query(
        self,
        callback_query_id: str,
        user_id: int,
        peer_id: int,
        event_data: Optional[Dict[str, Any]] = None,
        text: str = None
    ) -> dict:
        params = {
            'event_id': callback_query_id,
            'user_id': user_id,
            'peer_id': peer_id,
        }
        
        if event_data is not None:
             params['event_data'] = json.dumps(event_data)
        elif text:
            params['event_data'] = json.dumps({"type": "show_snackbar", "text": text})

        return apihelper._make_request(
            self.token,
            'messages.sendMessageEventAnswer',
            params
        )

    def polling(self, non_stop: bool = True, interval: int = 1):
        self._polling = True

        while self._polling:
            try:
                if not self.lp_server:
                    self.lp_server = apihelper.get_long_poll_server(self.token, self.group_id)

                raw_updates = apihelper.get_long_poll_updates(
                    self.lp_server.server,
                    self.lp_server.key,
                    self.lp_server.ts
                )

                parsed_updates = apihelper.process_updates(raw_updates)

                for update_data in parsed_updates:
                    self._process_update(update_data)

                if 'ts' in raw_updates:
                    self.lp_server.ts = raw_updates['ts']

            except exception.VKAPIError as e:
                self.lp_server = None
                if not non_stop:
                    raise
                time.sleep(interval)

            except Exception as e:
                print(f"Polling error: {e}")
                if not non_stop:
                    raise
                time.sleep(interval)

    def get_fsm(self, user_id: int, fsm_name: str = "default") -> 'FiniteStateMachine':
        state = self.get_state(user_id)
        fsm = FSMRegistry.get_or_create(fsm_name)
        fsm.current_state = state
        return fsm

    def set_fsm_state(self, user_id: int, state: str, fsm_name: str = "default"):
        fsm = self.get_fsm(user_id, fsm_name)
        fsm.transition(fsm.current_state, state, None)
        self.set_state(user_id, state)

    def _process_update(self, update_data: dict):
        update = types.Update(
            update_id=0,
            type=update_data['type'],
            object=update_data['object']
        )

        for middleware in self.middleware_handlers:
            if middleware.check(update):
                result = middleware.process(self, update)
                if result is False:
                    return

        if update.message:
            user_id = update.message.from_id
            current_state = self.get_state(user_id)
            state_context = self._get_state_context(user_id)
            
            for handler in self.message_handlers:
                if handler.check(update, current_state):
                    if handler.accepts_state:
                        handler.callback(update.message, state_context)
                    else:
                        handler.callback(update.message)
                    break

        elif update.callback_query:
            user_id = update.callback_query.from_id
            current_state = self.get_state(user_id)
            state_context = self._get_state_context(user_id)
            
            for handler in self.callback_query_handlers:
                if handler.check(update, current_state):
                    if handler.accepts_state:
                        handler.callback(update.callback_query, state_context)
                    else:
                        handler.callback(update.callback_query)
                    break

    def stop_polling(self):
        self._polling = False

__all__ = [
    'VKBot',
    'types',
    'exception',
    'util',
    'StateManager',
    'MemoryStorage',
    'RedisStorage',
    'StateContext',
    'StatesGroup',
    'FiniteStateMachine',
    'FSMRegistry'
]
