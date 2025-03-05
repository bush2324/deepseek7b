from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
import json
import os
import pandas as pd
from fuzzywuzzy import fuzz

# 初始化 FastAPI 應用
app = FastAPI()

# 初始化 Deepseek 模型
ollama_path = r'C:\Users\bushc\AppData\Local\Programs\Ollama\ollama.exe'
llm = ChatOllama(model="deepseek-r1", temperature=0.7, ollama_path=ollama_path)

# 測試資料儲存檔案
DATA_FILE = "sup_data.json"
CSV_FILE = "Hotel_C_f.csv"

# 初始化測試資料
if not os.path.exists(DATA_FILE):
    test_data = [
        {"question": "旗津哪裡可以租立槳?", "answer": "可以在旗津SUP俱樂部租借，地址是旗津海灘旁。"},
        {"question": "立槳價格是多少?", "answer": "旗津SUP租借價格約每小時500元。"},
        {"question": "旗津水域潮汐資訊怎麼查?", "answer": "可以透過中央氣象局或旗津SUP俱樂部的網站查詢最新潮汐資訊。"}
    ]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)

# 讀取CSV資料
def load_csv_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return df.to_dict(orient="records")
    return []

csv_data = load_csv_data()

# 記憶模組
memory = ConversationBufferMemory(memory_key="history", input_key="question")

# Prompt 模板
template =  """
你是一位旗津旅遊知識機器人，回答立槳活動、租借資訊、教學流程、水域資訊以及飯店民宿相關問題。

歷史對話：
{history}

問題: {question}
請簡明扼要回答。
"""

prompt = PromptTemplate(template=template, input_variables=["question", "history"])
chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

class ChatRequest(BaseModel):
    question: str

# 模糊比對 CSV 資料
def match_csv_data(question):
    question_lower = question.lower()
    best_match = None
    best_score = 0
    for row in csv_data:
        for value in row.values():
            if isinstance(value, str):
                score = fuzz.partial_ratio(question_lower, value.lower())
                if score > best_score and score >= 70:  # 分數門檻設定
                    best_score = score
                    best_match = row
    return best_match

@app.post("/chat")
async def chat(request: ChatRequest):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)

    # 嘗試比對 JSON 資料
    for item in knowledge_base:
        if item["question"] in request.question:
            memory.save_context({"question": request.question}, {"answer": item["answer"]})
            return {"user_input": request.question, "ai_response": item["answer"]}

    # 嘗試比對 CSV 資料
    csv_answer = match_csv_data(request.question)
    if csv_answer:
        memory.save_context({"question": request.question}, {"answer": str(csv_answer)})
        return {"user_input": request.question, "ai_response": str(csv_answer)}

    # 如果沒找到，則用LLM生成答案
    result = chain.run({"question": request.question})
    return {"user_input": request.question, "ai_response": result}

@app.post("/add_data")
async def add_data(data: dict):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
    
    knowledge_base.append(data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=4)
    
    return {"message": "資料已新增", "data": data}

@app.get("/")
async def read_root():
    return {"message": "~內網測試成功"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)