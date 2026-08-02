from pathlib import Path
import os
import json


MEMORY_DIR = Path("memory")

#把session_id拼成一个路径
def _memory_path(session_id:str) ->Path:
    if "/" in session_id or "//" in session_id or ".." in session_id:
        raise ValueError(f"非法的session_id:{session_id}")
    return MEMORY_DIR/f"{session_id}.md"

def load_memory(session_id:str) ->str:
    """读取该 session 的长期记忆。文件不存在时返回空字符串。"""
    path = _memory_path(session_id)
    
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")

def save_memory(session_id:str,content:str) ->None:
    MEMORY_DIR.mkdir(exist_ok=True)
    path = _memory_path(session_id)
    path.write_text(content,encoding="utf-8")



