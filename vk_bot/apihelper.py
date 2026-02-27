import json
import pathlib
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, BinaryIO

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exception import VKAPIError

API_URL = "https://api.vk.com/method/"
API_VERSION = "5.131"
USER_AGENT = "VK Bot Python/0.1"
TIMEOUT = 30
LONG_POLL_TIMEOUT = 25

_proxy: dict[str, str] | None = None
_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": USER_AGENT,
        })

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)

        if _proxy:
            _session.proxies.update(_proxy)

    return _session


def set_proxy(proxy: dict[str, str]):
    global _proxy, _session
    _proxy = proxy
    _session = None


def _make_request(
    token: str,
    method: str,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    http_method: str = "GET",
) -> dict:
    session = get_session()

    url = API_URL + method
    request_params = params.copy() if params else {}
    request_params.update({"access_token": token, "v": API_VERSION})

    try:
        if http_method.upper() == "GET":
            response = session.get(url, params=request_params, timeout=TIMEOUT)
        elif files:
            response = session.post(
                url, params=request_params, files=files, timeout=TIMEOUT * 2
            )
        else:
            response = session.post(url, data=request_params, timeout=TIMEOUT)

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            error = data["error"]
            raise VKAPIError(
                error_code=error.get("error_code", 0),
                error_msg=error.get("error_msg", "Unknown error"),
                request_params=request_params,
            )

        return data.get("response", {})

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error: {e}") from e
    except json.JSONDecodeError as e:
        raise ConnectionError(f"Invalid JSON response: {e}") from e


def get_me(token: str) -> dict:
    result = _make_request(token, "users.get")
    return result[0] if result else {}


def send_message(
    token: str,
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
    reply_to: int | None = None,
    **kwargs,
) -> dict:
    params = {
        "peer_id": chat_id,
        "message": text,
        "random_id": int(time.time() * 1000),
        **kwargs,
    }

    if reply_markup and isinstance(reply_markup, dict):
        params["keyboard"] = json.dumps(reply_markup)

    if reply_to:
        params["reply_to"] = reply_to

    return _make_request(token, "messages.send", params)


def reply_to_message(token: str, message: dict, text: str, **kwargs) -> dict:
    chat_id = message.get("peer_id") or message.get("user_id")
    reply_to = message.get("id")
    return send_message(token, chat_id, text, reply_to=reply_to, **kwargs)


def send_photo(
    token: str,
    chat_id: int,
    photo: str | bytes | BinaryIO,
    caption: str | None = None,
    **kwargs,
) -> dict:
    upload_server = get_messages_upload_server(token, peer_id=chat_id)
    uploaded = upload_photo_to_server(token, upload_server["upload_url"], photo)
    saved_photos = save_uploaded_photo(
        token, uploaded["photo"], uploaded["server"], uploaded["hash"]
    )

    if not saved_photos:
        raise ValueError("Failed to save photo")

    photo_info = saved_photos[0]
    attachment = f"photo{photo_info['owner_id']}_{photo_info['id']}"

    params = {
        "peer_id": chat_id,
        "attachment": attachment,
        "random_id": int(time.time() * 1000),
        **kwargs,
    }

    if caption:
        params["message"] = caption

    return _make_request(token, "messages.send", params)


def get_docs_upload_server(token: str, peer_id: int | None = None) -> dict:
    params = {}
    if peer_id:
        params["peer_id"] = peer_id
    return _make_request(token, "docs.getMessagesUploadServer", params)


def get_messages_upload_server(token: str, peer_id: int | None = None) -> dict:
    """Get upload server URL for photos.

    Args:
        token: VK API token.
        peer_id: Peer ID (required for sending to group chats).
    """
    params: dict[str, Any] = {}
    if peer_id:
        params["peer_id"] = peer_id
    return _make_request(token, "photos.getMessagesUploadServer", params)


def _to_bytes_io(data: str | bytes | BinaryIO, name: str = "picture.jpg") -> BytesIO:
    if isinstance(data, str):
        bytes_io = BytesIO(pathlib.Path(data).read_bytes())
    elif isinstance(data, bytes):
        bytes_io = BytesIO(data)
    elif isinstance(data, BytesIO):
        bytes_io = data
    else:
        bytes_io = BytesIO(data.read())
    bytes_io.seek(0)
    bytes_io.name = name
    return bytes_io


def upload_photo_to_server(
    token: str, upload_url: str, photo: str | bytes | BinaryIO
) -> dict:
    session = get_session()
    file = _to_bytes_io(photo, "photo.jpg")
    response = session.post(upload_url, files={"photo": file}, timeout=TIMEOUT * 2)
    response.raise_for_status()
    return response.json()


def save_uploaded_photo(token: str, photo: str, server: int, hash: str) -> list:
    params = {"photo": photo, "server": server, "hash": hash}
    return _make_request(token, "photos.saveMessagesPhoto", params)


def send_document(
    token: str,
    chat_id: int,
    document: str | bytes | BinaryIO,
    title: str | None = None,
    caption: str | None = None,
    **kwargs,
) -> dict:
    upload_server = get_docs_upload_server(token, peer_id=chat_id)
    uploaded = upload_document_to_server(token, upload_server["upload_url"], document)
    saved_docs = save_uploaded_document(token, uploaded["file"], title=title)

    if not saved_docs:
        raise ValueError("Failed to save document")

    doc_info = saved_docs["doc"]
    attachment = f"doc{doc_info['owner_id']}_{doc_info['id']}"

    params = {
        "peer_id": chat_id,
        "attachment": attachment,
        "random_id": int(time.time() * 1000),
        **kwargs,
    }

    if caption:
        params["message"] = caption

    return _make_request(token, "messages.send", params)


def upload_document_to_server(
    token: str, upload_url: str, document: str | bytes | BinaryIO
) -> dict:
    session = get_session()
    file = _to_bytes_io(document, "document.dat")
    response = session.post(upload_url, files={"file": file}, timeout=TIMEOUT * 2)
    response.raise_for_status()
    return response.json()


def save_uploaded_document(
    token: str, file_data: str, title: str | None = None
) -> list:
    params = {"file": file_data}
    if title:
        params["title"] = title
    return _make_request(token, "docs.save", params)


@dataclass
class LongPollServer:
    server: str
    key: str
    ts: str
    pts: int | None = None


def get_group_id(token: str) -> int:
    result = _make_request(token, "groups.getById")
    groups = result if isinstance(result, list) else result.get("groups", [])
    if not groups:
        raise ValueError(
            "Unable to get group_id. Check that the token is a community token."
        )
    return groups[0]["id"]


def get_long_poll_server(token: str, group_id: int) -> LongPollServer:
    result = _make_request(token, "groups.getLongPollServer", {"group_id": group_id})

    return LongPollServer(
        server=result["server"],
        key=result["key"],
        ts=result["ts"],
        pts=result.get("pts"),
    )


def get_long_poll_updates(
    server: str, key: str, ts: str, wait: int = LONG_POLL_TIMEOUT
) -> dict:
    session = get_session()

    url = f"{server}?act=a_check&key={key}&ts={ts}&wait={wait}"

    try:
        response = session.get(url, timeout=wait + 5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Long poll error: {e}") from e


def parse_update(update_data: list) -> dict | None:
    if not update_data:
        return None

    event_type = update_data[0]

    if event_type == 4:
        return {
            "type": "message_new",
            "object": {
                "id": update_data[1],
                "flags": update_data[2],
                "peer_id": update_data[3],
                "timestamp": update_data[4],
                "text": update_data[5] if len(update_data) > 5 else "",
                "attachments": update_data[6] if len(update_data) > 6 else [],
            },
        }
    if event_type == 8:
        return {
            "type": "user_online",
            "object": {"user_id": update_data[1], "timestamp": update_data[2]},
        }

    return None


def process_updates(raw_updates: dict) -> list[dict]:
    """Extract updates from Bots Long Poll response.

    Returns events as-is since Bots Long Poll API returns
    ready-to-use JSON objects with type and object fields.
    """
    return raw_updates.get("updates", [])


def create_keyboard(buttons: list[list[dict]], one_time: bool = False) -> dict:
    return {"buttons": buttons, "one_time": one_time}


def create_inline_keyboard(buttons: list[list[dict]]) -> dict:
    return {"inline": True, "buttons": buttons}


def extract_attachment_id(attachment: str) -> tuple[int | None, int | None]:
    if "_" not in attachment:
        return None, None

    type_part, id_part = attachment.split("_", 1)
    import re

    match = re.search(r"\d+$", type_part)
    owner_id = int(match.group()) if match else int(type_part)

    media_id = int(id_part.split("_")[0])
    return owner_id, media_id


def is_group_chat(peer_id: int) -> bool:
    return peer_id > 2000000000


def get_user_id_from_peer(peer_id: int) -> int:
    if is_group_chat(peer_id):
        return peer_id - 2000000000
    return peer_id
