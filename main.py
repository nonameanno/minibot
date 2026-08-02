from fastapi import FastAPI
from pydantic import BaseModel
from agent.runner import stream_chat
from storage.database import init_db
from agent.dream import dream
from fastapi.responses import StreamingResponse
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from storage.metrics import get_session_metrics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许所有来源(开发用,生产要指定具体域名)
    allow_credentials=True,
    allow_methods=["*"],       # 允许所有 HTTP 方法(GET/POST/...)
    allow_headers=["*"],       # 允许所有请求头
)


@app.get("/health")
async def health_check():
    return {"status":"ok","message":"MiNiBot is running!"}



@app.on_event("startup")
async def start_up():
    init_db()

class ChatRequest(BaseModel):
    message:str
    session_id:str
    
@app.post("/chat")
async def chat_endpoint(request:ChatRequest):
    def event_generator():
        for piece in stream_chat(request.message,request.session_id):
            data = json.dumps({"text":piece},ensure_ascii=False)
            yield f"data:{data}\n\n"
        yield "data:[DONE]\n\n"


    return StreamingResponse(event_generator(), media_type="text/event-stream")


class DreamRequest(BaseModel):
    session_id:str

@app.post("/dream")
async def dream_endpoint(request:DreamRequest):
    memory_text = dream(request.session_id)
    return {"memory":memory_text}

@app.get("/metrics/{session_id}")
async def metrics_endpoint(session_id:str):
    return get_session_metrics(session_id)
    


app.mount("/", StaticFiles(directory="static", html=True), name="static") #把某个"子应用"挂到主 app 的某个路径下。挂载 / 就是挂到网站根

    