from typing import Callable, List, Optional, Union, Pattern, Dict, Any
import re
import inspect
from . import types
from .exception import VKAPIError

class Handler:
    def __init__(self, callback: Callable, **filters):
        self.callback = callback
        self.filters = filters
        
        sig = inspect.signature(callback)
        self.accepts_state = len(sig.parameters) >= 2
    
    def check(self, update: types.Update) -> bool:
        return True

class MessageHandler(Handler):
    def __init__(
        self,
        callback: Callable,
        commands: Optional[List[str]] = None,
        regexp: Optional[Union[str, Pattern]] = None,
        func: Optional[Callable] = None,
        content_types: Optional[List[str]] = None,
        chat_types: Optional[List[str]] = None,
        state: Optional[Union[str, List[str]]] = None,
        **kwargs
    ):
        super().__init__(callback, **kwargs)
        
        self.commands = [cmd.lower() for cmd in commands] if commands else None
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp
        self.func = func
        self.content_types = content_types or ['text']
        self.chat_types = chat_types
        self.state = state
    
    def check(self, update: types.Update, current_state: Optional[str] = None) -> bool:
        if not update.message:
            return False
        
        message = update.message
        
        if self.state is not None:
            if isinstance(self.state, list):
                if current_state not in self.state:
                    return False
            elif self.state != current_state:
                return False
            
        if self.chat_types and message.chat.type not in self.chat_types:
            return False
        
        if message.content_type not in self.content_types:
            return False
        
        if self.func and not self.func(message):
            return False
        
        if self.commands:
            if not message.text:
                return False
            
            from .util import extract_command
            cmd, _ = extract_command(message.text)
            if not cmd or cmd not in self.commands:
                return False
        
        if self.regexp:
            if not message.text:
                return False
            if not self.regexp.search(message.text):
                return False
        
        return True

class CallbackQueryHandler(Handler):
    def __init__(
        self,
        callback: Callable,
        func: Optional[Callable] = None,
        data: Optional[Union[str, Pattern]] = None,
        state: Optional[Union[str, List[str]]] = None,
        **kwargs
    ):
        super().__init__(callback, **kwargs)
        self.func = func
        self.data = re.compile(data) if isinstance(data, str) else data
        self.state = state
    
    def check(self,  update: types.Update, current_state: Optional[str] = None) -> bool:
        if not update.callback_query:
            return False
        
        cb = update.callback_query
        
        if self.state is not None:
            if isinstance(self.state, list):
                if current_state not in self.state:
                    return False
            elif self.state != current_state:
                return False
            
        if self.func and not self.func(cb):
            return False
        
        if self.data:
            if not cb.data:
                return False
            if not self.data.search(cb.data):
                return False
        
        return True

class ChatMemberHandler(Handler):
    def __init__(
        self,
        callback: Callable,
        func: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(callback, **kwargs)
        self.func = func
    
    def check(self, update: types.Update) -> bool:
        if update.type not in ['group_join', 'group_leave', 'group_change_settings']:
            return False
        
        if self.func and not self.func(update):
            return False
        
        return True

class MiddlewareHandler(Handler):
    def __init__(self, callback: Callable, update_types: Optional[List[str]] = None):
        super().__init__(callback)
        self.update_types = update_types
    
    def check(self, update: types.Update) -> bool:
        if self.update_types and update.type not in self.update_types:
            return False
        return True
    
    def process(self, bot, update: types.Update):
        return self.callback(bot, update)
