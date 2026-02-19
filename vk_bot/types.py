from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json

@dataclass
class User:
    id: int
    first_name: str = ""
    last_name: str = ""
    is_closed: bool = False
    can_access_closed: bool = True
    photo_100: Optional[str] = None
    online: bool = False
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def mention(self) -> str:
        return f"[id{self.id}|{self.first_name}]"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            id=data.get('id'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_closed=data.get('is_closed', False),
            can_access_closed=data.get('can_access_closed', True),
            photo_100=data.get('photo_100'),
            online=data.get('online', False)
        )

@dataclass
class Chat:
    id: int
    type: str = "private"
    title: Optional[str] = None
    photo_100: Optional[str] = None
    
    @classmethod
    def from_peer_id(cls, peer_id: int) -> 'Chat':
        if peer_id > 2000000000:
            return cls(
                id=peer_id,
                type="group",
                title=f"Chat {peer_id - 2000000000}"
            )
        else:
            return cls(
                id=peer_id,
                type="private"
            )

@dataclass
class Photo:
    id: int
    owner_id: int
    access_key: Optional[str] = None
    sizes: List[dict] = field(default_factory=list)
    
    @property
    def attachment(self) -> str:
        base = f"photo{self.owner_id}_{self.id}"
        if self.access_key:
            base += f"_{self.access_key}"
        return base
    
    @property
    def url(self) -> Optional[str]:
        if not self.sizes:
            return None
        max_size = max(self.sizes, key=lambda x: x.get('width', 0) * x.get('height', 0))
        return max_size.get('url')

@dataclass
class Document:
    id: int
    owner_id: int
    title: str = ""
    size: int = 0
    ext: str = ""
    url: Optional[str] = None
    access_key: Optional[str] = None
    
    @property
    def attachment(self) -> str:
        base = f"doc{self.owner_id}_{self.id}"
        if self.access_key:
            base += f"_{self.access_key}"
        return base

@dataclass
class Video:
    id: int
    owner_id: int
    title: str = ""
    description: str = ""
    duration: int = 0
    access_key: Optional[str] = None
    
    @property
    def attachment(self) -> str:
        base = f"video{self.owner_id}_{self.id}"
        if self.access_key:
            base += f"_{self.access_key}"
        return base

@dataclass
class Audio:
    id: int
    owner_id: int
    artist: str = ""
    title: str = ""
    duration: int = 0
    url: Optional[str] = None
    
    @property
    def attachment(self) -> str:
        return f"audio{self.owner_id}_{self.id}"

@dataclass
class Message:
    id: int
    date: datetime
    peer_id: int
    from_id: int
    text: str = ""
    out: bool = False
    important: bool = False
    deleted: bool = False
    attachments: List[Dict] = field(default_factory=list)
    reply_message: Optional['Message'] = None
    fwd_messages: List['Message'] = field(default_factory=list)
    payload: Optional[dict] = None
    action: Optional[dict] = None
    _from_user: Optional[User] = None
    _chat: Optional[Chat] = None
    
    @property
    def chat(self) -> Chat:
        if not self._chat:
            self._chat = Chat.from_peer_id(self.peer_id)
        return self._chat
    
    @property
    def from_user(self) -> Optional[User]:
        return self._from_user
    
    @property
    def content_type(self) -> str:
        if self.text:
            return "text"
        elif self.attachments:
            return self.attachments[0].get('type', 'unknown')
        elif self.action:
            return f"action_{self.action.get('type')}"
        return "unknown"
    
    @property
    def is_private(self) -> bool:
        return self.peer_id == self.from_id
    
    def get_photos(self) -> List[Photo]:
        photos = []
        for att in self.attachments:
            if att.get('type') == 'photo':
                photo_data = att.get('photo', {})
                photos.append(Photo(
                    id=photo_data.get('id'),
                    owner_id=photo_data.get('owner_id'),
                    access_key=photo_data.get('access_key'),
                    sizes=photo_data.get('sizes', [])
                ))
        return photos
    
    def get_documents(self) -> List[Document]:
        docs = []
        for att in self.attachments:
            if att.get('type') == 'doc':
                doc_data = att.get('doc', {})
                docs.append(Document(
                    id=doc_data.get('id'),
                    owner_id=doc_data.get('owner_id'),
                    title=doc_data.get('title', ''),
                    size=doc_data.get('size', 0),
                    ext=doc_data.get('ext', ''),
                    url=doc_data.get('url'),
                    access_key=doc_data.get('access_key')
                ))
        return docs
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        return cls(
            id=data.get('id'),
            date=datetime.fromtimestamp(data.get('date', 0)),
            peer_id=data.get('peer_id'),
            from_id=data.get('from_id'),
            text=data.get('text', ''),
            out=data.get('out', False),
            important=data.get('important', False),
            deleted=data.get('deleted', False),
            attachments=data.get('attachments', []),
            payload=data.get('payload'),
            action=data.get('action'),
        )

class KeyboardButton:
    def __init__(self, text: str, color: str = "primary"):
        self.text = text
        self.color = color
    
    def to_dict(self) -> dict:
        return {
            "action": {
                "type": "text",
                "label": self.text
            },
            "color": self.color
        }

class InlineKeyboardButton:
    def __init__(
        self,
        text: str,
        callback_data: str = None,
        url: str = None,
        vk_app_id: int = None,
        owner_id: int = None,
        hash: str = None
    ):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.vk_app_id = vk_app_id
        self.owner_id = owner_id
        self.hash = hash
    
    def to_dict(self) -> dict:
        action = {"type": "text", "label": self.text}
        
        if self.callback_data:
            action["type"] = "callback"
            action["payload"] = json.dumps({"data": self.callback_data})
        elif self.url:
            action["type"] = "open_link"
            action["link"] = self.url
        elif self.vk_app_id:
            action["type"] = "open_app"
            action["app_id"] = self.vk_app_id
            if self.owner_id:
                action["owner_id"] = self.owner_id
            if self.hash:
                action["hash"] = self.hash
        
        return {"action": action}

class ReplyKeyboardMarkup:
    def __init__(self, one_time_keyboard: bool = False):
        self.keyboard: List[List[KeyboardButton]] = []
        self.one_time_keyboard = one_time_keyboard
    
    def add(self, *buttons: KeyboardButton):
        row = list(buttons)
        if row:
            self.keyboard.append(row)
        return self
    
    def row(self, *buttons: KeyboardButton):
        return self.add(*buttons)
    
    def to_dict(self) -> dict:
        return {
            "buttons": [
                [btn.to_dict() for btn in row]
                for row in self.keyboard
            ],
            "one_time": self.one_time_keyboard
        }

class InlineKeyboardMarkup:
    def __init__(self):
        self.keyboard: List[List[InlineKeyboardButton]] = []
    
    def add(self, *buttons: InlineKeyboardButton):
        row = list(buttons)
        if row:
            self.keyboard.append(row)
        return self
    
    def row(self, *buttons: InlineKeyboardButton):
        return self.add(*buttons)
    
    def to_dict(self) -> dict:
        return {
            "buttons": [
                [btn.to_dict() for btn in row]
                for row in self.keyboard
            ],
            "inline": True
        }

@dataclass
class CallbackQuery:
    id: str
    from_id: int
    peer_id: int
    message_id: int
    payload: Optional[dict] = None
    data: Optional[str] = None
    _message: Optional[Message] = None
    _from_user: Optional[User] = None
    
    @property
    def message(self) -> Optional[Message]:
        return self._message
    
    @property
    def from_user(self) -> Optional[User]:
        return self._from_user
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CallbackQuery':
        payload = data.get('payload')
        if payload and isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                pass
        
        data_value = None
        if payload and isinstance(payload, dict):
            data_value = payload.get('data')
        
        return cls(
            id=data.get('event_id'),
            from_id=data.get('user_id'),
            peer_id=data.get('peer_id'),
            message_id=data.get('conversation_message_id'),
            payload=payload,
            data=data_value
        )

@dataclass
class Update:
    update_id: int
    type: str
    object: dict
    _message: Optional[Message] = None
    _callback_query: Optional[CallbackQuery] = None
    
    @property
    def message(self) -> Optional[Message]:
        if self.type == 'message_new' and not self._message:
            self._message = Message.from_dict(self.object.get('message', {}))
        return self._message
    
    @property
    def callback_query(self) -> Optional[CallbackQuery]:
        if self.type == 'message_event' and not self._callback_query:
            self._callback_query = CallbackQuery.from_dict(self.object)
        return self._callback_query