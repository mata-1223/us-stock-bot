from ddgs import DDGS
from textblob import TextBlob
from typing import List, Dict, Any
import time

class NewsAgent:
    """
    특정 키워드에 대한 최신 뉴스를 검색하고 
    간단한 감성 분석(Sentiment Analysis)을 수행하는 에이전트입니다.
    """

    def __init__(self, max_results: int = 5):
        """
        Args:
            max_results (int): 검색할 뉴스 기사 최대 개수. Defaults to 5.
        """
        self.max_results = max_results

    def search_news(self, ticker: str) -> List[Dict[str, str]]:
        """
        DuckDuckGo를 통해 해당 종목의 최신 금융 뉴스를 검색합니다.
        
        Args:
            ticker (str): 종목 티커 (예: 'AAPL')

        Returns:
            List[Dict[str, str]]: 뉴스 제목, 링크, 본문 요약이 담긴 딕셔너리 리스트
        """
        query = f"{ticker} stock news financial"
        print(f"[*] Searching news for: {query}...")
        
        results = []
        try:
            # DDGS 인스턴스 생성 및 검색
            with DDGS() as ddgs:
                # news() 메서드 사용 (날짜순 정렬 불가시 text() 사용 등 유연하게 대처)
                news_gen = ddgs.news(query=query, max_results=self.max_results)
                
                for r in news_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "source": r.get("source", ""),
                        "url": r.get("url", "")
                    })
                    
        except Exception as e:
            print(f"[!] News search failed: {e}")
            
        return results

    def analyze_sentiment(self, news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        수집된 뉴스들의 제목/본문을 분석하여 평균 감성 점수를 도출합니다.
        (TextBlob 활용: -1.0 ~ 1.0 사이 점수)

        Returns:
            Dict: {score: float, summary: str, reasons: List[str]}
        """
        if not news_items:
            return {"score": 0.0, "summary": "No news found", "reasons": []}

        total_score = 0.0
        reasons = []

        print("[*] Analyzing sentiment...")
        for item in news_items:
            # 제목과 본문을 합쳐서 분석
            text = f"{item['title']} {item['body']}"
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity  # -1.0 (부정) ~ 1.0 (긍정)
            
            total_score += sentiment
            
            # 주요 뉴스 로깅 (감성 점수가 뚜렷한 경우)
            if abs(sentiment) > 0.1:
                mood = "Positive" if sentiment > 0 else "Negative"
                reasons.append(f"[{mood}] {item['title']} (Score: {sentiment:.2f})")

        avg_score = total_score / len(news_items)
        
        # 종합 의견 도출
        summary = "Neutral"
        if avg_score > 0.1: summary = "Bullish (Positive News)"
        elif avg_score < -0.1: summary = "Bearish (Negative News)"

        return {
            "score": avg_score,
            "summary": summary,
            "reasons": reasons
        }

# --- 실행 테스트 ---
if __name__ == "__main__":
    # AAPL이 아까 RSI가 낮았으므로, 악재가 있는지 검색해봅니다.
    agent = NewsAgent(max_results=5)
    
    ticker = "AAPL"
    news = agent.search_news(ticker)
    
    if news:
        print(f"\n--- Latest News for {ticker} ---")
        for n in news:
            print(f"- [{n['source']}] {n['title']}")
            
        analysis = agent.analyze_sentiment(news)
        print(f"\n--- AI Analysis Result ---")
        print(f"Sentiment Score: {analysis['score']:.2f}")
        print(f"Opinion: {analysis['summary']}")
        print("Key Factors:")
        for r in analysis['reasons']:
            print(f"  {r}")
    else:
        print("News not found.")