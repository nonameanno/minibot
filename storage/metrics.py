from storage.database import get_conn

def record_llm_call(session_id:str,prompt_tokens:int,
                    completion_tokens:int,total_tokens:int) ->None:
    """记录调用一次llm的token消耗"""
    conn = get_conn()
    conn.execute(
        "INSERT INTO metrics (session_id,event_type,prompt_tokens,completion_tokens,total_tokens)"
        "VALUES (?,?,?,?,?)",
        (session_id,"llm_call",prompt_tokens,completion_tokens,total_tokens)
    )
    conn.commit()
    conn.close

def record_tool_call(session_id:str,tool_name:str) ->None:
    "记录一次工具调用"
    conn = get_conn()
    conn.execute(
        "INSERT INTO metrics (session_id,event_type,tool_name)"
        "VALUES (?,?,?)",
        (session_id,"tool_call",tool_name)
    )
    conn.commit()
    conn.close

def record_dream(session_id:str) ->None:
    """记录一次Dream触发"""
    conn = get_conn()
    conn.execute(
        "INSERT INTO metrics (session_id,event_type)"
        "VALUES (?,?)",
        (session_id,"dream")
    )
    conn.commit()
    conn.close()


    """把某个 session 的所有埋点原始行,汇总成一个字典"""
def get_session_metrics(session_id):
    conn = get_conn()

    #1) LLM 调用次数 + token 三件套
    row = conn.execute(
        "SELECT COUNT(*) AS llm_calls, "
        "COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens, "
        "COALESCE(SUM(completion_tokens), 0) AS completion_tokens, "
        "COALESCE(SUM(total_tokens), 0) AS total_tokens "
        "FROM metrics WHERE session_id = ? AND event_type = 'llm_call'",
        (session_id,)
    ).fetchone()
    llm_calls, prompt_tokens, completion_tokens, total_tokens = row

    # 2) 工具调用按名字分组
    tool_rows = conn.execute(
        "SELECT tool_name, COUNT(*) FROM metrics "
        "WHERE session_id = ? AND event_type = 'tool_call' "
        "GROUP BY tool_name",
        (session_id,)
    ).fetchall()
    tool_calls_by_name = {name: cnt for name, cnt in tool_rows}
    tool_calls_total = sum(tool_calls_by_name.values())

    # 3) dream 次数
    dream_count = conn.execute(
        "SELECT COUNT(*) FROM metrics WHERE session_id = ? AND event_type = 'dream'",
        (session_id,)
    ).fetchone()[0]

    conn.close()

    return {
        "session_id": session_id,
        "llm_calls": llm_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tool_calls_total": tool_calls_total,
        "tool_calls_by_name": tool_calls_by_name,
        "dream_count": dream_count,
    }

   
  



