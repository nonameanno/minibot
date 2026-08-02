# MiniBot 项目交接文档

> 把这份文档完整粘贴给新对话，它能完整接手我们的进度。

---

## 一、用户背景

- **目标**：找 AI 应用开发实习岗，正在准备简历和面试
- **当前技术栈**：Python 基础 + requests + FastAPI，前端零基础(HTML/JS 刚开始接触)
- **学习方式偏好**：一步一步带着走，每行代码都要能看懂，用中文，多用类比解释，不懂就问
- **API Key**：有多个（OpenAI / Claude / DeepSeek 都有），当前用 **DeepSeek**（便宜）
- **时间**：充裕，3-4 周，要做完整版
- **部署**：先本地跑通，后期再上云 + Docker

---

## 二、我们已经学完的概念（用户已理解，无需重讲）

通过研读开源项目 nanobot 源码，用户已掌握以下概念（能用自己的话解释）：

| 概念 | 用户的理解程度 |
|---|---|
| 项目文件夹结构（名片/文档/源代码三分类） | 已掌握 |
| 消息总线 / 生产者-消费者模式（bus/） | 已掌握，用公交车类比 |
| "允许重复优于过早抽象"的工程原则 | 已掌握，能面试作答 |
| AI Agent 的 tool-calling loop（核心循环） | 已掌握，能背出面试答案 |
| Function Calling 机制（name + description + JSON Schema） | 已掌握 |
| Context Window 问题 + 三层上下文管理 | 已掌握 |
| 长期记忆 / Dream 两阶段固化机制 | 已了解概念 |
| loop.py vs runner.py vs providers/ 的分工 | 已掌握 |
| **Python 生成器 + yield**(通过 stream_chat 实践) | ✅ 本轮学的 |
| **SSE 协议格式**(`data: {json}\n\n` + `[DONE]`) | ✅ 本轮学的 |
| **流式 tool_calls 增量拼接**(index/id/name/arguments 分批到达) | ✅ 本轮学的 |
| **fetch + ReadableStream**(前端流式接收) | ✅ 本轮学的 |
| **HTML 三件套**(HTML 骨架 / CSS 装修 / JS 行为) | ✅ 本轮初识 |
| **CORS 跨域机制**(为啥 file:// 打开会被拦、CORSMiddleware 用法) | ✅ 本轮学的 |

---

## 三、我们决定要做的项目

### 项目名：MiniBot
**一句话定位**：一个能用工具、有长期记忆的 AI 研究助手，全栈自研（不依赖 LangChain / LangGraph）

**为什么这么做（重要，面试要讲）**：
- 不用 LangChain 是加分项——面试官不喜欢只会调框架不懂原理的候选人
- 完全基于用户已有技术栈（Python + FastAPI）+ 我们学的概念
- 能写进简历，有量化指标

### 三期计划

**第一期 MVP** —— ✅ **已完成**：
- ✅ FastAPI `/chat` 接口
- ✅ Tool-calling loop（自己实现，不用 LangChain）
- ✅ 工具：`web_search`、`web_fetch`、`save_note` / `read_note`（在 agent/tools.py）
- ✅ SQLite 存对话历史（storage/database.py，文件 storage/minibot.db）

**第二期 Memory** —— ✅ **已完成**：
- ✅ 上下文自动截断（runner.py 内实现）
- ✅ 老对话 LLM 摘要压缩（runner.py 内实现）
- ✅ Dream 机制：`POST /dream` 端点触发，把关键事实写进 `memory/{session_id}.md`
- ✅ 下次新会话自动加载对应 session 的记忆文件

**流式收尾** —— ✅ **已完成**：
- ✅ `stream_chat(user_message, session_id)` 生成器函数(runner.py)，支持工具调用循环
- ✅ `/chat` 端点改造成 `StreamingResponse` + SSE 格式
- ✅ 已通过 curl.exe 和前端 fetch 两种方式验证

**第三期 亮点** —— 🚧 **进行中**:
- ✅ 3.1a: 最小 HTML + fetch 读流(warmup)
- ✅ 3.1b: 输入框 + 发送按钮 + 打字机效果 + SSE 解析
- 🚧 3.1c: **正在做** —— StaticFiles 挂载,浏览器直接访问 `http://localhost:8000/`
- ⏳ 3.2: 量化指标(token 用量、工具调用次数、Dream 触发次数)
- ⏳ 3.3: Docker 化 + 云部署

---

## 四、项目目录结构（当前实际状态）

```
minibot/
│
├── main.py                     ← FastAPI 应用入口
│                                 端点: /health, /chat(流式), /dream
│                                 中间件: CORSMiddleware(allow_origins=["*"])
│                                 挂载: static/ 到 /(StaticFiles + html=True)
├── requirements.txt
├── .env                        ← API Key(DeepSeek, TAVILY),不上 git
├── .gitignore
├── body.json                   ← curl 测试用 request body 文件
├── test_stream.py              ← warmup 测试脚本(可删)
│
├── agent/
│   ├── __init__.py
│   ├── runner.py               ← ⭐ 核心:chat() + stream_chat() + 上下文管理
│   ├── dream.py                ← Dream 机制
│   └── tools.py                ← 工具定义 (save_note/read_note/web_fetch/web_search)
│
├── static/                     ← ⭐ 前端目录 (本次新增)
│   └── index.html              ← 前端聊天页(输入框+打字机+SSE 解析)
│
├── memory/                     ← 每个 session 一个 md
│   └── {session_id}.md
│
├── storage/
│   ├── __init__.py
│   ├── database.py             ← init_db / load_history / save_message
│   ├── memory_store.py         ← load_memory / save_memory(带路径穿越校验)
│   └── minibot.db              ← SQLite 数据库文件
│
└── notes/                      ← save_note 工具写出的笔记
```

---

## 五、本轮完成的核心代码要点

### `agent/runner.py` 新增 `stream_chat()`

关键结构：

```python
def stream_chat(user_message: str, session_id: str):
    # 1. 初始化(和 chat() 一样): load_history, 加 system prompt, append user_msg, 
    #    maybe_compress, load_memory 拼进 system prompt, trim_message
    
    MAX_ITERATIONS = 10
    for _ in range(MAX_ITERATIONS):
        message_to_send = trim_message(messages, max_turns=10)
        
        full_reply = ""
        finish_reason = None
        tool_calls_buffer = {}   # 小本本: {index: {"id","name","arguments"}}
        
        stream = client.chat.completions.create(..., stream=True)
        
        for chunk in stream:
            if not chunk.choices: continue
            choice = chunk.choices[0]
            delta = choice.delta
            
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            
            if delta.content:
                full_reply += delta.content
                yield delta.content
            
            if delta.tool_calls:
                # 按 index 累积 id/name/arguments 到 tool_calls_buffer
                # arguments 用 += 拼接(是一段段来的)
                ...
        
        # 分支 A: 纯文本 → 存库 → return
        if finish_reason == "stop":
            if full_reply:
                assistant_msg = {"role": "assistant", "content": full_reply}
                messages.append(assistant_msg); save_message(...)
            return
        
        # 分支 B: 工具调用 → 组装 assistant_msg → 执行工具 → continue
        if finish_reason == "tool_calls":
            # 手动组装带 tool_calls 的 assistant_msg,存库
            # yield "\n[调用工具 XXX...]\n" 给用户可见
            # 挨个 json.loads(arguments) + dispatch_tool + append tool_msg + save
            continue
    
    yield "\n[已达到循环最大迭代次数,未得到最终的答案。]"
```

### `main.py` 关键变化

1. **顶部新增导入**:
```python
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from agent.runner import chat, stream_chat
```

2. **CORS 中间件** (`app = FastAPI()` 之后):
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], 
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```

3. **`/chat` 端点改造**:
```python
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    def event_generator():
        for piece in stream_chat(request.message, request.session_id):
            data = json.dumps({"text": piece}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

4. **文件末尾**(所有路由之后):
```python
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

⚠️ **注意**：原来的 `@app.get("/") def root(): return {"message":"..."}` 需要**删除**,否则会拦截根路径,mount 拿不到。

### `static/index.html` 关键点

- 输入框 + 发送按钮 + `<pre>` 输出区
- `fetch('/chat', ...)` 相对路径(同源)
- `response.body.getReader() + TextDecoder` 读流
- 用 `buffer` 缓冲 + `.split('\n\n')` 拆消息(**注意 SSE 消息可能跨 chunk**)
- 后端 SSE 前缀是 `data:`(**没有空格**),所以 `part.slice(5)` 或者 `.slice(5).trim()`
- JSON.parse 时 `try/catch` 兜底

---

## 六、本轮踩过的坑 & 教训(帮助下一轮避坑)

| 坑 | 原因 | 解法 |
|---|---|---|
| `assistant` 拼成 `assitant` / `assitants` | 手抄英文单词的常见错误 | 只有 `a-s-s-i-s-t-a-n-t` 是正确拼法。任何角色字段发到 API 前先目测一遍 |
| 两条 user 消息连续 → 400 invalid_request | 上轮测试遗留在 DB,再跑相同 session_id 时叠加 | **每次流式测试换新 session_id**,或删掉 `storage/minibot.db` |
| `no such table: messages` | 直接 `python -m agent.runner` 绕过了 FastAPI 的 `init_db()` startup 事件 | 在 `if __name__ == "__main__":` 手动 `init_db()` |
| `save_memory(".../etc/hack","attck")` 触发 ValueError | 该行是测试路径穿越校验的调用,被误留在 memory_store.py 模块顶层,import 就执行 | 已删除 |
| PowerShell 里 `curl` 是 `Invoke-WebRequest` 别名,-H 参数不兼容 | Windows 陷阱 | 用 `curl.exe`(带.exe 绕开别名)。JSON body 用 `-d "@body.json"` 从文件读,避免 shell 转义地狱 |
| SSE `slice(6)` vs `slice(5)` | 后端实际发的是 `data:{"text":...}` 没有空格,前缀 5 字符 | `part.slice(5).trim()` 一劳永逸 |
| 前端 file:// 打开 → CORS 报错 | file:// origin 是 null,和 http://127.0.0.1:8000 不同源 | 后端加 CORSMiddleware,或者本次做的 3.1c(mount 静态目录到同源) |
| JS 模板字符串必须用反引号 `` ` ``,单引号里 `${var}` 是字面字符 | 手抄时容易搞错 | 反引号在 Tab 键上面,英文输入法 |
| `parts.pops()` → 报错 | 数组方法是 `pop`,没有 `pops` | 手抄错 |
| DeepSeek-v4-pro 有 `reasoning_content`(思考过程) | 大部分 chunk 的 `delta.content=None` 但 `reasoning_content` 有值 | 只判 `if delta.content:` 就自动跳过 reasoning 阶段 |
| `--reload` 检测 static/ 改动会触发重启,请求中途会 502/连接断 | uvicorn 默认监视工作目录 | 网络问题一般刷新就好;或启动时用 `--reload-dir agent --reload-dir storage` 限定监视范围 |

---

## 七、下一步(3.1c 收尾)

用户已经把 main.py 改好了(加了 StaticFiles mount + fetch 改成相对路径),但**忘了删除 `@app.get("/") def root()`** 那 3 行,导致访问 `http://127.0.0.1:8000/` 命中的是老 JSON 接口而不是 index.html。

**接手第一件事**:让用户把这 3 行删掉,uvicorn 自动重启后再打开 `http://127.0.0.1:8000/` 验证能直接进对话页面。



之后就是 3.2 / 3.3。

 

---

## 八、对你（新对话）的交互要求

**语言与节奏**:
- 全程用中文
- 一步一步带着写,每步做完让用户测试通过再继续
- 每行代码都要解释是干嘛的,用类比,不能只写代码不说话
- 遇到新概念要**先讲概念再写代码**(比如 async/await、yield、SSE、闭包 这些)
- 不要一次给太多代码,宁可分批给
- 进度跟踪用 TodoWrite

**⚠️ 代码修改的规则**(用户强烈反馈过多次,务必遵守):

1. **不要用 Edit/Write 工具直接改用户的代码文件**。发现 bug 或需要修改的地方,**只**做以下事:
   - 指出文件路径 + 行号
   - 说明"现在是什么样,应该改成什么样,为什么"
   - 让用户自己在编辑器里改完再反馈
   
   例外:只有用户明确说"你直接改"、"帮我改" 时才动 Edit/Write。

2. **需要看代码的时候在对话里贴出来给用户看**,让他自己敲一遍。用户明确表达过:"给我在对话框里写一下源码吧,我看完然后自己再去写一遍"——这是学习方式的核心。

3. **文档类文件**(比如本 handoff)用户明确要求更新时,可以直接写。

**给任务的粒度**:
- 用户偏好"验证 + 修正 + 下一步任务一次给完",让他并行推进。所以每轮回复末尾如果有下一步,直接给出下一步指令。
- 但每步内部,尽量拆到用户能安全跑完的最小单元。

**技术偏好**:
- 用 openai SDK(兼容 DeepSeek),不用 anthropic SDK
- 用 DeepSeek 模型省钱
- 每次流式测试**记得换新 session_id**,或先清 db
- Windows PowerShell 环境,curl 用 `curl.exe`,JSON body 从文件读

---

## 九、requirements.txt(参考)

```
fastapi==0.115.0
uvicorn==0.30.0
openai==1.54.0
httpx==0.27.0
python-dotenv==1.0.0
duckduckgo-search==6.3.0
tavily-python
pytest==8.3.0
pytest-asyncio==0.24.0
```
