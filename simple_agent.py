import re
import ollama  # pip install ollama (이미 설치하셨죠?)

# 1. 도구(Tool) 정의: AI가 사용할 수 있는 함수
def get_stock_price(ticker):
    """주식 종목 코드를 넣으면 현재 가격(가짜)을 반환함"""
    print(f"   [Tool] 🔎 {ticker} 가격 조회 중...")
    mock_data = {
        "AAPL": 150,
        "TSLA": 200,
        "NVDA": 500
    }
    return mock_data.get(ticker.upper(), 0)

# 2. 시스템 프롬프트: ReAct 패턴 (로컬 모델이 잘 알아듣게 조금 더 강조함)
SYSTEM_PROMPT = """
You are a smart AI Agent. You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer.

Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:
get_stock_price:
    e.g. get_stock_price: AAPL
    Returns the current price of the stock.

Example session:
Question: What is the price of AAPL?
Thought: I should check the price of AAPL.
Action: get_stock_price: AAPL
PAUSE

You will then be called again with this:
Observation: 150

Then you output:
Answer: The price of AAPL is 150.
"""

class SimpleAgent:
    def __init__(self):
        # [변경] Groq 대신 로컬 Ollama 모델 사용
        # llama3가 설치되어 있어야 합니다. (터미널: ollama pull llama3)
        self.model = "llama3" 
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def run(self, question):
        print(f"🤖 User: {question}")
        self.messages.append({"role": "user", "content": f"Question: {question}"})

        # --- Agent Loop ---
        max_steps = 10
        for i in range(max_steps):
            # [변경] ollama.chat 함수 사용
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
            )
            response_text = response['message']['content']
            
            print(f"\n🧠 AI Thought (Step {i+1}):\n{response_text}")

            # 2. 'Action' 찾기 (정규표현식)
            # 로컬 모델은 가끔 "Action: get_stock_price: AAPL" 뒤에 불필요한 공백을 넣기도 해서 strip() 필수
            action_match = re.search(r"Action: (\w+): (.+)", response_text)

            if action_match:
                # 도구 사용 감지!
                tool_name = action_match.group(1)
                tool_input = action_match.group(2).strip()
                
                # 3. 도구 실행
                observation = ""
                if tool_name == "get_stock_price":
                    price = get_stock_price(tool_input)
                    observation = f"Observation: {price}"
                else:
                    observation = f"Observation: Error - Tool {tool_name} not found"

                print(f"👀 {observation}")

                # 4. 결과 기록 (중요: Ollama는 role='assistant'로 넣어줘야 대화가 이어짐)
                self.messages.append({"role": "assistant", "content": response_text})
                self.messages.append({"role": "user", "content": observation})
                
            elif "Answer:" in response_text:
                # 5. 최종 답변
                try:
                    final_answer = response_text.split("Answer:")[1].strip()
                except:
                    final_answer = response_text # 형식이 조금 깨져도 내용 전체 출력
                
                print(f"\n🎉 Final Answer: {final_answer}")
                return final_answer
            
            else:
                # 행동 없이 생각만 한 경우
                self.messages.append({"role": "assistant", "content": response_text})

# 실행
if __name__ == "__main__":
    agent = SimpleAgent()
    print("🚀 Local Ollama Agent 시작!")
    # 질문: "애플"과 "테슬라" 가격을 각각 조회해서 더해야 함
    agent.run("애플(AAPL)과 테슬라(TSLA)의 주가 합계는 얼마야?")