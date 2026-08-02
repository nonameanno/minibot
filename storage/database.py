import sqlite3

import json

DEFAULT_DB_PATH = "storage/minibot.db"
#建立连接
def get_conn():
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    #改变数据库查询结果的返回格式
    conn.row_factory = sqlite3.Row 
    return conn

#初始化表
def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY ,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        payload TEXT NOT NULL,
        create_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics(
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id     TEXT NOT NULL,
        event_type     TEXT NOT NULL,     -- 'llm_call' / 'tool_call' / 'dream'
        tool_name      TEXT,              -- 只有 tool_call 会填
        prompt_tokens      INTEGER,       -- 只有 llm_call 会填
        completion_tokens  INTEGER,
        total_tokens       INTEGER,
        created_at     TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
    conn.commit()
    conn.close()

#根据会话id加载历史记录
def load_history(session_id:str) ->list[dict]:
    conn = get_conn()
    cursor = conn.execute(
        "SELECT payload FROM messages where session_id = ? ORDER BY id",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row["payload"]) for row in rows]

#保存信息
def save_message(session_id:str,message:str) ->None:
    conn = get_conn()
    conn.execute(
    "INSERT INTO messages (session_id, role, payload) VALUES (?, ?, ?)",
        (session_id, message["role"], json.dumps(message, ensure_ascii=False))
    )
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    init_db()   
    save_message("test_1",{"role":"user","content":"你好！"})
    save_message("test_1",{"role":"assistant","content":"你也好"})
    print(load_history("test_1"))
