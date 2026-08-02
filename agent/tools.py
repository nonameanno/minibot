from pathlib import Path
import httpx
import re
from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

def save_note(title:str,content:str) ->str:
     # 1. 确保 notes 文件夹存在
    # 2. 拼出文件路径 notes/{title}.md
    # 3. 打开文件、写入 content
    # 4. 返回一句提示
    Path("notes").mkdir(exist_ok=True)

    filename = f"{title}.md"
    filepath = f"notes/{filename}"

    with open(filepath,"w",encoding="utf-8") as f:
        f.write(content)

    return f"Saved to {filepath}"

def read_note(title:str) ->str:
    title = title.strip()
    filepath = f"notes/{title}.md"

    if Path(f"notes/{title}.md").exists():
        with open(filepath,"r",encoding="utf-8") as f:
            content = f.read()
            return content
    else:
        return f"note '{title}' not found "

def web_fetch(url:str) ->str:
    response = httpx.get(url,timeout=10)
    response.raise_for_status()

    text = re.sub(r"<[^>]+>","",response.text)
    text = re.sub(r"\s+"," ",text).strip()

    if len(text) > 3000:
        text = text[:3000] + "\n...(truncated)"

    return text

def web_search(query:str) ->str:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query,max_results=5)
    results = response.get("results",[])
    

    if not results:
        return "未找到结果"

    lines = []
    for i,r in enumerate(results,start=1):
        lines.append(f"{i},{r["title"]}\n  {r["url"]}\n  {r["content"]}")

    return "\n\n".join(lines)
    


if __name__ == "__main__":
    pass
    
    




