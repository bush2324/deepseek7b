from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import uvicorn
# 初始化 FastAPI 應用
app = FastAPI()

# 呼叫 Deepseek 進行聊天的函數
def chat_with_deepseek(message: str):
    result = subprocess.run([r'C:\Users\bushc\AppData\Local\Programs\Ollama\ollama.exe', 'run', 'deepseek-r1'], 
                            input=message, text=True, capture_output=True, encoding='utf-8')  # 添加 encoding='utf-8'
    return result.stdout

# 定義一個路由來處理 AI 聊天請求
@app.get("/chat")
async def chat_with_ai(user_message: str):
    response = chat_with_deepseek(user_message)
    return {"user_message": user_message, "ai_response": response}

# 定義根路徑的處理器（選擇性）
@app.get("/")
async def read_root():
    return {"message": "~內網測試成功會跳出這則訊息"}

responses = {
    "葉家豪": "超雄聖體",
    "溫維智": "旗津第一長髮男"
}

class InputName(BaseModel):
    name: str

@app.get("/api/測試")
async def test_api(name: str):
    # 根據名稱返回對應的結果，若找不到則返回錯誤訊息
    response = responses.get(name, "未知的人物")
    return {"input": name, "output": response}

# 啟動 FastAPI 服務器
if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)
