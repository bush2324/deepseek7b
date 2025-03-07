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
import random
import re

# 初始化 FastAPI 應用
app = FastAPI()

# 初始化 Deepseek 模型
ollama_path = r'C:\Users\bushc\AppData\Local\Programs\Ollama\ollama.exe'
llm = ChatOllama(model="deepseek-r1", temperature=0.7, ollama_path=ollama_path)

# 測試資料儲存檔案
DATA_FILE = "sup_data.json"
CSV_FILE = "Hotel_C_f.csv"

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

class AddDataRequest(BaseModel):
    data: dict

# 記錄最近匹配的飯店
last_match = None

# 擴充台灣所有縣市的匹配範圍（統一「台」和「臺」）
def extract_location(question):
    locations = set()
    question = question.replace("台", "臺")  # 確保台灣地名的一致性
    city_pattern = re.compile(r"(臺北|新北|桃園|臺中|臺南|高雄|基隆|新竹|苗栗|彰化|南投|雲林|嘉義|屏東|宜蘭|花蓮|臺東|澎湖|金門|連江|臺北市|新北市|桃園市|臺中市|臺南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|澎湖縣|金門縣|連江縣)")
    matches = city_pattern.findall(question)
    locations.update(matches)
    print(f"識別出的地點：{locations}")  # Debug 輸出
    return list(locations)

# 推薦飯店函數（改進地名匹配方式）
def recommend_hotels(locations):
    filtered_hotels = [hotel for hotel in csv_data if 'Add' in hotel and any(loc in hotel['Add'] for loc in locations)]
    print(f"篩選出的飯店數量：{len(filtered_hotels)}，篩選條件：{locations}")  # Debug 輸出
    if not filtered_hotels:
        return f"抱歉，找不到位於 {'、'.join(locations)} 的飯店。"
    sampled_hotels = random.sample(filtered_hotels, min(len(filtered_hotels), 2))
    response = "這裡有一些推薦的飯店：\n"
    for hotel in sampled_hotels:
        response += format_hotel_response(hotel) + "\n"
    return response

# 查詢 CSV 的主要函數
def match_csv_data(question):
    global last_match
    question_lower = question.lower()
    best_match = None
    best_score = 0
    
    # 若問題為「更多資訊」，直接回傳 last_match
    if last_match and ('更多資訊' in question_lower or '詳細資料' in question_lower):
        return format_hotel_response(last_match)
    
    # 檢查是否有地點關鍵字
    location_keywords = extract_location(question_lower)
    if location_keywords:
        return recommend_hotels(location_keywords)
    
    for row in csv_data:
        for value in row.values():
            if isinstance(value, str):
                score = fuzz.partial_ratio(question_lower, value.lower())
                if score > best_score and score >= 70:
                    best_score = score
                    best_match = row
    
    if best_match:
        last_match = best_match  # 記住最後查詢的飯店
        return format_hotel_response(best_match)
    
    return "抱歉，我無法找到相關的資料，請提供更具體的問題！"

# 格式化飯店回應
def format_hotel_response(hotel):
    response = (
        f"🏨 {hotel['Name']} 位於 {hotel['Add']}。\n"
        f"📞 聯絡電話: {hotel['Tel']}\n"
        f"💰 價格範圍: {hotel['LowestPrice']} 元 - {hotel['CeilingPrice']} 元\n"
    )
    if 'Serviceinfo' in hotel and isinstance(hotel['Serviceinfo'], str) and '自行車友善' in hotel['Serviceinfo']:
        response += "🚲 這間民宿提供自行車友善服務，適合喜愛騎行的旅客！\n"
    return response

@app.post("/chat")
async def chat(request: ChatRequest):
    csv_answer = match_csv_data(request.question)
    if csv_answer:
        memory.save_context({"question": request.question}, {"answer": str(csv_answer)})
        return {"user_input": request.question, "ai_response": str(csv_answer)}
    
    result = chain.run({"question": request.question})
    return {"user_input": request.question, "ai_response": result}

@app.post("/add_data")
async def add_data(request: AddDataRequest):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
    
    knowledge_base.append(request.data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=4)
    
    return {"message": "資料已新增", "data": request.data}

@app.get("/")
async def read_root():
    return {"message": "~內網測試成功"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)