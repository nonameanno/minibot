import os
from openai import OpenAI
from dotenv import load_dotenv
from storage.database import load_history
from storage.memory_store import load_memory,save_memory
from storage.metrics import record_dream

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

_client = OpenAI(
    api_key=api_key,
    base_url=base_url
)


DREAM_SYSTEM_PROMPT = """你是一个记忆整理助手,专门维护用户的长期档案

你的任务:根据【已有记忆】和【本次会话】,输出一份**更新后的用户档案**。

输出规则:
1. 只保留稳定的、跨会话有价值的信息:用户身份、偏好、长期目标、正在做的事
2. 忽略琐碎的一次性对话(比如"1+1等于几""今天天气")
3. 使用 Markdown 格式,用 ## 分小节(如 ## 基本信息 / ## 偏好 / ## 长期任务)
4. 如果新信息与已有记忆冲突,以**新信息**为准
5. 用户没说的东西不要瞎编
6. 输出**纯 markdown 内容**,不要加 ```markdown 包裹,不要开场白

如果本次会话没有新的稳定信息可以添加，原样输出【已有记忆】的内容（不要清空、不要输出"空档案"标记）。

"""

def _format_conversation(messages:list[dict]) ->str:
    """"把messages列表拼成给LLM看的纯文本对话"""
    lines = []
    for m in messages:
        role = m.get("role","?")
        content = m.get("content") or ""
        if role in ("user","assistant") and content:
            lines.append(f"[{role} {content}]")
    return "\n".join(lines)

def dream(session_id:str) ->str:
    """整理 session_id 的长期记忆,写入 memory/{session_id}.md,并返回新内容。"""
    messages = load_history(session_id)
    existing_memory = load_memory(session_id)
    conversation = _format_conversation(messages)

    user_prompt = f"""[已有记忆]
    {existing_memory if conversation else "(暂无)"}

    [本次会话]
    {conversation if conversation else "暂无"}

    请输出更新后的用户档案。 """

    response = _client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":DREAM_SYSTEM_PROMPT},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.3
    )

    new_memory = response.choices[0].message.content.strip()
    if not new_memory or "空档案" in new_memory:
        return existing_memory

    save_memory(session_id,new_memory)

    record_dream(session_id=session_id)

    return new_memory







        


