import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional, Union, BinaryIO, List
from dataclasses import dataclass
from .exception import VKAPIError

API_URL = "https://api.vk.com/method/"
API_VERSION = "5.131"
USER_AGENT = "VK Bot Python/0.1"
TIMEOUT = 30
LONG_POLL_TIMEOUT = 25

_proxy = None
_session = None

def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount('http://', adapter)
        _session.mount('https://', adapter)
        
        if _proxy:
            _session.proxies.update(_proxy)
    
    return _session

def set_proxy(proxy: dict):
    global _proxy, _session
    _proxy = proxy
    _session = None

def _make_request(
    token: str,
    method: str,
    params: Dict[str, Any] = None,
    files: Dict[str, Any] = None,
    http_method: str = 'GET'
) -> dict:
    session = get_session()
    
    url = API_URL + method
    request_params = params.copy() if params else {}
    request_params.update({
        'access_token': token,
        'v': API_VERSION
    })
    
    try:
        if http_method.upper() == 'GET':
            response = session.get(
                url,
                params=request_params,
                timeout=TIMEOUT
            )
        else:
            if files:
                response = session.post(
                    url,
                    params=request_params,
                    files=files,
                    timeout=TIMEOUT * 2
                )
            else:
                response = session.post(
                    url,
                    data=request_params,
                    timeout=TIMEOUT
                )
        
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            error = data['error']
            raise VKAPIError(
                error_code=error.get('error_code', 0),
                error_msg=error.get('error_msg', 'Unknown error'),
                request_params=request_params
            )
        
        return data.get('response', {})
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error: {e}") from e
    except json.JSONDecodeError as e:
        raise ConnectionError(f"Invalid JSON response: {e}") from e

def get_me(token: str) -> dict:
    result = _make_request(token, 'users.get')
    return result[0] if result else {}

def send_message(
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str = None,
    reply_markup: dict = None,
    reply_to: int = None,
    **kwargs
) -> dict:
    params = {
        'user_id': chat_id,
        'message': text,
        'random_id': int(time.time() * 1000),
        **kwargs
    }
    
    if parse_mode:
        params['parse_mode'] = parse_mode
    
    if reply_markup:
        if isinstance(reply_markup, dict):
            params['keyboard'] = json.dumps(reply_markup)
    
    if reply_to:
        params['reply_to'] = reply_to
    
    return _make_request(token, 'messages.send', params)

def reply_to_message(token: str, message: dict, text: str, **kwargs) -> dict:
    chat_id = message.get('peer_id') or message.get('user_id')
    reply_to = message.get('id')
    return send_message(token, chat_id, text, reply_to=reply_to, **kwargs)

def send_photo(
    token: str,
    chat_id: int,
    photo: Union[str, bytes, BinaryIO],
    caption: str = None,
    **kwargs
) -> dict:
    upload_server = get_messages_upload_server(token)
    uploaded = upload_photo_to_server(token, upload_server['upload_url'], photo)
    saved_photos = save_uploaded_photo(
        token,
        uploaded['photo'],
        uploaded['server'],
        uploaded['hash']
    )
    
    if not saved_photos:
        raise ValueError("Failed to save photo")
    
    photo_info = saved_photos[0]
    attachment = f"photo{photo_info['owner_id']}_{photo_info['id']}"
    
    params = {
        'user_id': chat_id,
        'attachment': attachment,
        'random_id': int(time.time() * 1000),
        **kwargs
    }
    
    if caption:
        params['message'] = caption
    
    return _make_request(token, 'messages.send', params)

def get_docs_upload_server(token: str) -> dict:
    return _make_request(token, 'docs.getMessagesUploadServer')

def get_messages_upload_server(token: str) -> dict:
    return _make_request(token, 'photos.getMessagesUploadServer')

def upload_photo_to_server(
    token: str,
    upload_url: str,
    photo: Union[str, bytes, BinaryIO]
) -> dict:
    session = get_session()
    
    if isinstance(photo, str):
        with open(photo, 'rb') as f:
            files = {'photo': f}
            response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    elif isinstance(photo, bytes):
        files = {'photo': photo}
        response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    else:
        files = {'photo': photo}
        response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    
    response.raise_for_status()
    return response.json()

def save_uploaded_photo(
    token: str,
    photo: str,
    server: int,
    hash: str
) -> list:
    params = {
        'photo': photo,
        'server': server,
        'hash': hash
    }
    return _make_request(token, 'photos.saveMessagesPhoto', params)

def send_document(
    token: str,
    chat_id: int,
    document: Union[str, bytes, BinaryIO],
    title: str = None,
    **kwargs
) -> dict:
    upload_server = get_docs_upload_server(token)
    uploaded = upload_document_to_server(token, upload_server['upload_url'], document)
    saved_docs = save_uploaded_document(
        token,
        uploaded['file'],
        title=title
    )
    
    if not saved_docs:
        raise ValueError("Failed to save document")
    
    doc_info = saved_docs[0]
    attachment = f"doc{doc_info['owner_id']}_{doc_info['id']}"
    
    params = {
        'user_id': chat_id,
        'attachment': attachment,
        'random_id': int(time.time() * 1000),
        **kwargs
    }
    
    return _make_request(token, 'messages.send', params)

def upload_document_to_server(
    token: str,
    upload_url: str,
    document: Union[str, bytes, BinaryIO]
) -> dict:
    session = get_session()
    
    if isinstance(document, str):
        with open(document, 'rb') as f:
            files = {'file': f}
            response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    elif isinstance(document, bytes):
        files = {'file': document}
        response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    else:
        files = {'file': document}
        response = session.post(upload_url, files=files, timeout=TIMEOUT * 2)
    
    response.raise_for_status()
    return response.json()

def save_uploaded_document(
    token: str,
    file_data: str,
    title: str = None
) -> list:
    params = {'file': file_data}
    if title:
        params['title'] = title
    return _make_request(token, 'docs.save', params)

@dataclass
class LongPollServer:
    server: str
    key: str
    ts: str
    pts: int = None

def get_long_poll_server(token: str) -> LongPollServer:
    result = _make_request(token, 'messages.getLongPollServer', {
        'need_pts': 1,
        'lp_version': 3
    })
    
    return LongPollServer(
        server=result['server'],
        key=result['key'],
        ts=result['ts'],
        pts=result.get('pts')
    )

def get_long_poll_updates(
    server: str,
    key: str,
    ts: str,
    wait: int = LONG_POLL_TIMEOUT
) -> dict:
    session = get_session()
    
    url = f"{server}?act=a_check&key={key}&ts={ts}&wait={wait}&mode=2&version=3"
    
    try:
        response = session.get(url, timeout=wait + 5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Long poll error: {e}") from e

def parse_update(update_data: list) -> Optional[dict]:
    if not update_data:
        return None
    
    event_type = update_data[0]
    
    if event_type == 4:
        return {
            'type': 'message_new',
            'object': {
                'id': update_data[1],
                'flags': update_data[2],
                'peer_id': update_data[3],
                'timestamp': update_data[4],
                'text': update_data[5] if len(update_data) > 5 else '',
                'attachments': update_data[6] if len(update_data) > 6 else [],
            }
        }
    elif event_type == 8:
        return {
            'type': 'user_online',
            'object': {
                'user_id': update_data[1],
                'timestamp': update_data[2]
            }
        }
    
    return None

def process_updates(raw_updates: dict) -> List[dict]:
    parsed = []
    
    if 'updates' in raw_updates:
        for update in raw_updates['updates']:
            parsed_update = parse_update(update)
            if parsed_update:
                parsed.append(parsed_update)
    
    return parsed

def create_keyboard(buttons: List[List[dict]], one_time: bool = False) -> dict:
    return {
        'buttons': buttons,
        'one_time': one_time
    }

def create_inline_keyboard(buttons: List[List[dict]]) -> dict:
    return {
        'inline': True,
        'buttons': buttons
    }

def extract_attachment_id(attachment: str) -> tuple:
    if '_' not in attachment:
        return None, None
    
    type_part, id_part = attachment.split('_', 1)
    import re
    match = re.search(r'\d+$', type_part)
    if match:
        owner_id = int(match.group())
    else:
        owner_id = int(type_part)
    
    media_id = int(id_part.split('_')[0])
    return owner_id, media_id

def is_group_chat(peer_id: int) -> bool:
    return peer_id > 2000000000

def get_user_id_from_peer(peer_id: int) -> int:
    if is_group_chat(peer_id):
        return peer_id - 2000000000
    return peer_id