import os
from google import genai
from dotenv import load_dotenv
from typing import List, Dict

# 환경 변수 로드
load_dotenv()

class LLMNewsAgent:
    """
    Google Gemini (New SDK)를 사용하여 뉴스를 분석하고 
    투자 인사이트를 제공하는 고지능 에이전트입니다.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("[!] Error: GEMINI_API_KEY가 설정되지 않았습니다.")
            return

        # [변경점] 새로운 클라이언트 초기화 방식
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"[!] Gemini Client Init Failed: {e}")

    def analyze_news(self, ticker: str, news_items: List[Dict[str, str]]) -> Dict[str, str]:
        """
        뉴스 목록을 받아 LLM에게 분석을 요청합니다.
        """
        if not news_items:
            return {"summary": "관련된 뉴스가 없습니다.", "sentiment": "NEUTRAL", "score": 0.0}

        # LLM에게 보낼 프롬프트 구성
        headlines = "\n".join([f"- {item['title']}" for item in news_items])
        
        prompt = f"""
        You are a professional Wall Street financial analyst.
        Analyze the following news headlines for the stock '{ticker}'.
        
        [Headlines]
        {headlines}
        
        [Instructions]
        1. Determine the overall sentiment (BULLISH, BEARISH, or NEUTRAL).
        2. Provide a sentiment score between -1.0 (Very Negative) and 1.0 (Very Positive).
        3. Write a brief, 1-sentence analysis explaining the reason in Korean(한국어).
        
        [Output Format]
        Please output strictly in the following format:
        SENTIMENT: [BULLISH/BEARISH/NEUTRAL]
        SCORE: [Numeric Score]
        REASON: [Korean Analysis]
        """

        try:
            # 모델 호출
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',  # gemini-2.5-flash
                contents=prompt
            )
            
            # 응답 텍스트 추출
            if response.text:
                text = response.text.strip()
            else:
                return {"summary": "응답 없음", "sentiment": "NEUTRAL", "score": 0.0}
            
            # 파싱 로직
            lines = text.split('\n')
            result = {"summary": "분석 실패", "sentiment": "NEUTRAL", "score": 0.0}
            
            for line in lines:
                if "SENTIMENT:" in line:
                    result["sentiment"] = line.split(":")[1].strip()
                elif "SCORE:" in line:
                    try:
                        result["score"] = float(line.split(":")[1].strip())
                    except:
                        result["score"] = 0.0
                elif "REASON:" in line:
                    result["summary"] = line.split(":")[1].strip()
            
            return result

        except Exception as e:
            print(f"[!] LLM Analysis Failed: {e}")
            return {"summary": "AI 분석 중 오류 발생", "sentiment": "ERROR", "score": 0.0}