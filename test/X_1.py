# test\X_1.py

import subprocess

def chat_with_deepseek(message):
    result = subprocess.run([r'C:\Users\bushc\AppData\Local\Programs\Ollama\ollama.exe', 'run', 'deepseek-r1'], 
                            input=message, text=True, capture_output=True, encoding='utf-8')  # 添加 encoding='utf-8'
    return result.stdout

if __name__ == "__main__":
    while True:
        user_input = input("你: ")
        if user_input.lower() == 'exit':
            print("聊天结束！")
            break
        response = chat_with_deepseek(user_input)
        print("Deepseek: " + response)
