import os
import time
from abc import ABC, abstractmethod
from typing import List, Dict

# 라이브러리 임포트
from google import genai # Gemini
from groq import Groq             # Groq
import ollama                     # Ollama
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 추상 클래스 (설계도)
# ==========================================
class BaseLLMAgent(ABC):
    @abstractmethod
    def analyze_news(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, str]:
        pass

    def _get_common_prompt(self, ticker, headlines):
        return f"""
        You are a professional Wall Street financial analyst.
        Analyze the following news headlines for the stock '{ticker}'.
        
        [Headlines]
        {headlines}
        
        [Instructions]
        1. Determine the overall sentiment (BULLISH, BEARISH, or NEUTRAL).
        2. Provide a sentiment score between -1.0 (Very Negative) and 1.0 (Very Positive).
        3. Write a brief, 1-sentence analysis explaining the reason in Korean(한국어).
        
        [Output Format]
        Please output strictly in the following format (No markdown, No bold):
        SENTIMENT: [BULLISH/BEARISH/NEUTRAL]
        SCORE: [Numeric Score]
        REASON: [Korean Analysis]
        """

    def _parse_response(self, text: str) -> Dict[str, str]:
        lines = text.split('\n')
        result = {"summary": "분석 실패", "sentiment": "NEUTRAL", "score": 0.0}
        
        for line in lines:
            line = line.strip()
            if "SENTIMENT:" in line:
                result["sentiment"] = line.split(":", 1)[1].strip()
            elif "SCORE:" in line:
                try:
                    clean_score = line.split(":", 1)[1].strip().replace('*', '').replace('#', '')
                    result["score"] = float(clean_score)
                except:
                    result["score"] = 0.0
            elif "REASON:" in line:
                result["summary"] = line.split(":", 1)[1].strip()
        return result

# ==========================================
# 2. 구현체: Google Gemini (Free)
# ==========================================
class GeminiAgent(BaseLLMAgent):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: print("[!] Warning: GEMINI_API_KEY missing")
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except: pass

    def analyze_news(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, str]:
        if not news_items: return {"summary": "뉴스 없음", "sentiment": "NEUTRAL", "score": 0.0}
        prompt = self._get_common_prompt(ticker, "\n".join([f"- {i['title']}" for i in news_items]))

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                if response.text: return self._parse_response(response.text)
            except Exception as e:
                if "429" in str(e):
                    print(f"[Gemini] Quota limit. Waiting 20s... (Retry {attempt+1})")
                    time.sleep(20)
                else:
                    print(f"[Gemini] Error: {e}")
                    break
        return {"summary": "Gemini 오류", "sentiment": "ERROR", "score": 0.0}

# ==========================================
# 3. 구현체: Groq (Free Beta, Fast)
# ==========================================
class GroqAgent(BaseLLMAgent):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if not api_key: print("[!] Warning: GROQ_API_KEY missing")
        self.client = Groq(api_key=api_key)

    def analyze_news(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, str]:
        if not news_items: return {"summary": "뉴스 없음", "sentiment": "NEUTRAL", "score": 0.0}
        prompt = self._get_common_prompt(ticker, "\n".join([f"- {i['title']}" for i in news_items]))

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return self._parse_response(completion.choices[0].message.content)
        except Exception as e:
            print(f"[Groq] Error: {e}")
            return {"summary": "Groq 오류", "sentiment": "ERROR", "score": 0.0}

# ==========================================
# 4. 구현체: Ollama (Local, Unlimited)
# ==========================================
class OllamaAgent(BaseLLMAgent):
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        # Ollama는 별도 키 필요 없음 (로컬 실행)

    def analyze_news(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, str]:
        if not news_items: return {"summary": "뉴스 없음", "sentiment": "NEUTRAL", "score": 0.0}
        prompt = self._get_common_prompt(ticker, "\n".join([f"- {i['title']}" for i in news_items]))

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return self._parse_response(response['message']['content'])
        except Exception as e:
            print(f"[Ollama] Error: Ollama가 실행 중인지 확인하세요! (Error: {e})")
            return {"summary": "Ollama 오류", "sentiment": "ERROR", "score": 0.0}

# ==========================================
# 5. 팩토리 (Factory)
# ==========================================
def get_llm_agent():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    print(f"[*] Initializing AI Provider: {provider.upper()}")
    
    if provider == "groq":
        return GroqAgent()
    elif provider == "ollama":
        return OllamaAgent()
    elif provider == "gemini":
        return GeminiAgent()
    else:
        print(f"[!] Unknown provider '{provider}'. Fallback to Gemini.")
        return GeminiAgent()