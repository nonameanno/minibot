from dotenv import load_dotenv
import os
from openai import OpenAI
from agent.tools import save_note,read_note,web_fetch,web_search
import json
from storage.database import load_history,save_message,init_db
from storage.memory_store import load_memory
from storage.metrics import record_llm_call,record_tool_call

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

TOOLS_SCHEMA =[ {
    "type":"function",
    "function":{
        "name":"save_note",
        "description":"把一条笔记保存到本地",
        "parameters":{
            "type":"object",
            "properties":{
                "title":{"type":"string","description":"笔记标题，用作文件名"},
                "content":{"type":"string","description":"笔记正文内容"}
            },
            "required":["title","content"]
        }
    }
},
{
    "type":"function",
    "function":{
        "name":"read_note",
        "description":"根据标题读取之前保存的笔记内容",
        "parameters":{
            "type":"object",
            "properties":{
                "title":{"type":"string","description":"要读取的之前笔记的标题"}
            },
            "required":["title"]
        }
    }
},
{
    "type":"function",
    "function":{
        "name":"web_fetch",
        "description":"抓取指定URL网页的纯文本内容，当用户给你了具体链接想让你看时用",
        "parameters":{
            "type":"object",
            "properties":{
                "url":{"type":"string","description":"要抓取的完整的URL"}
            },
            "required":["url"]
            }
        }       
},
{
    "type":"function",
    "function":{
        "name":"web_search",
        "description":"用Tavily搜索引擎搜索关键词,并返回前几条摘要",
        "parameters":{
            "type":"object",
            "properties":{"query":{"type":"string","description":"搜索的关键词"}} ,
            "required":["query"]
        }
    }
}
]

#函数电话簿，把所有的函数放在一个箱子里
TOOL_MAP = {
    "save_note": save_note,
    "read_note": read_note,
    "web_fetch": web_fetch,
    "web_search": web_search
}


client = OpenAI(
    api_key=api_key,
    base_url=base_url
)



#工具执行器
def dispatch_tool(name:str,arguments:dict) ->str:
    if name not in TOOL_MAP:
        return f"未知工具：{name}"
    
    try:
        #根据名称动态调用工具并返回结果
        return TOOL_MAP[name](**arguments) 
    except Exception as e:
        return f"工具{name} 执行出错：{e}"


#上下文自动截断
def trim_message(messages:list[dict],max_turns:int = 10) ->list[dict]:
    if not messages:
        return []
    if messages[0].get("role") == "system":
        system_msg = messages[0]
        rest = messages[1:]
    else:
        system_msg = None
        rest = messages

    user_count = 0                       #用来记要找几个用户信息
    cut = 0                               ## 刀的位置：默认是 0（也就是不切，全保留）
    for i in range(len(rest)-1,-1,-1):     #i 代表的是当前看的那条消息在列表里的座位号（下标），而不是你数了多少个数。
        if rest[i].get("role") == "user":
            user_count += 1
            if user_count == max_turns:
                cut = i                    #找到了要切割的节点了
                break
    trimed = rest[cut:]
    if system_msg:
        return [system_msg] + trimed
    return trimed


#summarize_messages()
'''它要干啥？

输入：一个 list[dict]（若干条消息）
输出：一个字符串(LLM 生成的摘要）

思路：调 LLM,但不带 tools,就单纯让它读一段对话记录、吐一段摘要。'''
def summarize_message(messages:list[dict]) ->str:
    lines = []
    for m in messages:
        role = m.get("role","unknow")
        content = m.get("content","") or ""
        if not content and m.get("tool_calls"):
            content = f"[调用了工具：{[tool_call["function"]["name"] for tool_call in m["tool_calls"]]}]"
        lines.append(f"[{role}]:{content}")
    conversation_text = "\n".join(lines)
    

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role":"system",
                "content":(
                     "你是对话摘要助手。请把下面这段对话历史压缩成一段简洁的中文摘要，"
                    "保留：用户的关键信息（姓名、地点、偏好）、已作出的决定、"
                    "未完成的任务、以及用户明确表达过的诉求。"
                    "不要用列表格式，直接一段话。控制在 100字内。"
                )
            },
            {
                "role":"user",
                "content":conversation_text
            }
        ]
    )
    return resp.choices[0].message.content


"""
如果消息总数超过 threshold,把老的部分压成一条 system 摘要消息。
keep_recent_turns: 保留最近 N 轮 user 起头的对话原文。
"""
def maybe_compress(messages:list,threshold: int=20,keep_recent_turns:int=4) ->list[dict]:
    if len(messages) <= threshold:
        return messages

    if messages[0].get("role") == "system":
        system_msg = messages[0]
        rest = messages[1:]
    else:
        system_msg = None
        rest = messages

    user_count = 0
    cut = None
    for i in range(len(rest)-1,-1,-1):
        if rest[i].get("role") == "user":
            user_count += 1
            if user_count == keep_recent_turns:
                cut = i
                break

    if cut is None or cut == 0:
        return messages

    to_summarize = rest[:cut]
    to_keep = rest[cut:]

    summarize_text = summarize_message(to_summarize)

    summary_msg = {
        "role":"system",
        "content":f"以下是之前对话的摘要(用于唤起记忆):\n{summarize_text}"
    }

    result = []
    if system_msg:
        result.append(system_msg)
    result.append(summary_msg)
    result.extend(to_keep)
    return result

def stream_chat(user_message:str,session_id:str):
    messages = load_history(session_id)

    if not messages:
        messages.append({
            "role":"system",
            "content":(
                 "你是一个工具型助手。规则："
                "1. 只有当用户明确要求时才调用工具（例如「保存」「读一下」「搜一下」「打开这个链接」）。"
                "2. 用户只是提问时，直接用你已有的知识回答，不要调用任何工具。"
                "3. 一次对话中不要主动串联多个工具（比如搜完不要自作主张去保存）。"
            )
        })
        save_message(session_id,messages[0])

    user_msg = {"role":"user","content":user_message}
    messages.append(user_msg)
    save_message(session_id,user_msg)

    messages = maybe_compress(messages)


    memory_text = load_memory(session_id)
    if memory_text and messages and messages[0].get("role") == "system":  #判断"第一条消息是不是 system prompt"。因为我们要把记忆拼进 system prompt 里,所以要确认第一条确实是 system prompt。

        '''把当前 system prompt 的文字部分取出来,存到 base_prompt 变量里。messages[0] 是一个字典,长这样:{"role": "system", "content": "你是一个工具型助手。规则:..."
        动作:把 messages[0] 原地覆盖成一个新的字典——role 还是 system,但 content 变成"原来的 system prompt + 分隔线 + 用户长期记忆"。'''

        base_prompt = messages[0]["content"]
        messages[0] = {
            "role": "system",
            "content": (
                f"{base_prompt}\n\n"  #原来的pormpt
                f"---\n"
                f"以下是你对该用户的长期记忆(用户档案),回答时可以参考:\n"
                f"{memory_text}"   #新加入的记忆
            ),
        }


    MAX_INTERATIONS = 10
    for _ in range(MAX_INTERATIONS):
        message_to_send = trim_message(messages,max_turns=10)

        full_reply = ""
        finish_reason = None
        tool_calls_buffer = {}    #后面每收到 tool_call 增量,就往这个字典里塞/更新。
        usage_data = None

        #DEBUG 用来看每次发给服务器的messages长什么样
        print(f"\n[DEBUG] 发送的 messages:")
        for m in message_to_send:
            print(f"  {m}")
            print()


        stream = client.chat.completions.create(
            model=model,
            messages=message_to_send,
            tools = TOOLS_SCHEMA,
            stream=True,
            stream_options={"include_usage":True}
        )   

        for chunk in stream:
            if chunk.usage:
                usage_data = chunk.usage
           
            if not chunk.choices: 
                continue  

            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta.content:
                full_reply += delta.content
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls_buffer[idx]["id"] = tc.id
                    if tc.function.name:
                        tool_calls_buffer[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_buffer[idx]["arguments"] += tc.function.arguments

        if usage_data:
            record_llm_call(
                session_id=session_id,
                prompt_tokens=usage_data.prompt_tokens,
                completion_tokens=usage_data.completion_tokens,
                total_tokens=usage_data.total_tokens,
            )
            
            ## ---- 分支 A:模型给了纯文本回复 ----
        if finish_reason == "stop":
            if full_reply:
                        assistant_msg = {"role":"assistant","content":full_reply}
                        messages.append(assistant_msg)
                        save_message(session_id,assistant_msg)
            return


            # ---- 分支 B:模型要调工具 ----    
            # 
            # 先存信息           
        if finish_reason == "tool_calls":
                # (1) 组装一条带 tool_calls 的 assistant 消息 + 存库
            tool_calls_list = []
            for idx in sorted(tool_calls_buffer.keys()):
                tool_calls_list.append({
                "id": tool_calls_buffer[idx]["id"],
                "type": "function",
                "function": {
                    "name": tool_calls_buffer[idx]["name"],
                    "arguments": tool_calls_buffer[idx]["arguments"],
                            }
                })
            assistant_msg = {
                    "role":"assistant",
                    "content":full_reply or None,
                    "tool_calls":tool_calls_list
                }
            messages.append(assistant_msg)
            save_message(session_id,assistant_msg)

                #调用  
            for idx in sorted(tool_calls_buffer.keys()):
                name = tool_calls_buffer[idx]["name"]
                arguments = json.loads(tool_calls_buffer[idx]["arguments"])
                yield f"\n[调用工具{name}]\n"
                result = dispatch_tool(name,arguments)

                record_tool_call(session_id=session_id,tool_name=name)

                tool_msg = {
                    "role":"tool",
                    "tool_call_id":tool_calls_buffer[idx]["id"],
                    "content":result
                }
                messages.append(tool_msg)
                save_message(session_id,tool_msg)

       
    yield "\n[已达到循环最大迭代次数,未得到最终的答案。]"


'''if __name__ == "__main__":
    init_db()
    for piece in stream_chat("使用工具帮我搜一下python是什么", "test_tool_l"):
       print(piece,end="",flush=True)
    print()'''

    
        

   
     


    

