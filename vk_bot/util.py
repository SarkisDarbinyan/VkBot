import re
import json
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

def extract_command(text: str) -> Tuple[Optional[str], Optional[str]]:
    if not text or not text.startswith('/'):
        return None, None
    
    parts = text[1:].split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else None
    
    return command, args

def extract_mentions(text: str) -> List[int]:
    mentions = []
    
    pattern = r'\[id(\d+)\|.*?\]'
    mentions.extend([int(m) for m in re.findall(pattern, text)])
    
    pattern = r'@id(\d+)'
    mentions.extend([int(m) for m in re.findall(pattern, text)])
    
    return list(set(mentions))

def split_text(text: str, max_length: int = 4096) -> List[str]:
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current = ""
    
    for line in text.split('\n'):
        if len(current) + len(line) + 1 <= max_length:
            if current:
                current += '\n' + line
            else:
                current = line
        else:
            if current:
                parts.append(current)
            
            if len(line) > max_length:
                words = line.split(' ')
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 <= max_length:
                        if current:
                            current += ' ' + word
                        else:
                            current = word
                    else:
                        if current:
                            parts.append(current)
                        if len(word) > max_length:
                            for i in range(0, len(word), max_length):
                                parts.append(word[i:i+max_length])
                            current = ""
                        else:
                            current = word
            else:
                current = line
    
    if current:
        parts.append(current)
    
    return parts

def parse_payload(payload: Optional[str]) -> Optional[Dict]:
    if not payload:
        return None
    
    if isinstance(payload, dict):
        return payload
    
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except:
            return {'data': payload}
    
    return None

def build_attachment_string(owner_id: int, media_id: int, access_key: str = None) -> str:
    base = f"{owner_id}_{media_id}"
    if access_key:
        base += f"_{access_key}"
    return base

def parse_attachment_string(attachment: str) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    match = re.match(r'^(photo|video|doc|audio)(\d+)_(\d+)(?:_(.*))?$', attachment)
    if not match:
        return None, None, None, None
    
    return match.group(1), int(match.group(2)), int(match.group(3)), match.group(4)

def is_group_event(event_type: str) -> bool:
    group_events = [
        'group_join', 'group_leave', 'group_change_photo',
        'group_change_settings', 'group_officers_edit'
    ]
    return event_type in group_events

def format_time(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M')

def create_link(text: str, url: str) -> str:
    return f"[{url}|{text}]"