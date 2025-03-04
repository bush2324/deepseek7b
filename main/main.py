from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

# 初始化 FastAPI 應用
app = FastAPI()

# 初始化 Deepseek 模型
ollama_path = r'C:\Users\bushc\AppData\Local\Programs\Ollama\ollama.exe'
llm = ChatOllama(model="deepseek-r1", temperature=0.7, ollama_path=ollama_path)

# Prompt 模板
template = """
你是我的餐廳採購助手，我每天點菜的品項大致相同，但數量會變化。你的任務是：

記錄我今天提供的品項與數量，整理成清單。

單位統一使用「斤、兩」，小於 1 兩的部分記為 0。

與昨天的清單對比，確保品項一致，並提醒我確認。

問題: {question}
請用簡單且清晰的語言回答。
"""

prompt = PromptTemplate(template=template, input_variables=["question"])
chain = LLMChain(llm=llm, prompt=prompt)

class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat(request: ChatRequest):
    result = chain.run(request.question)
    return {"user_input": request.question, "ai_response": result}

@app.get("/")
async def read_root():
    return {"message": "~內網測試成功"}

responses = {
    "葉家豪": "超雄聖體",
    "溫維智": "旗津第一長髮男"
}

@app.get("/api/測試")
async def test_api(name: str):
    response = responses.get(name, "未知的人物")
    return {"input": name, "output": response}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)
