import pandas as pd
import time
from datetime import datetime
from src.collectors.stock_loader import StockDataLoader
from src.strategies.indicators import TechnicalAnalyzer
from src.agents.news_agent import NewsAgent
from src.utils.notifier import TelegramBot
from src.agents.llm_agent import get_llm_agent
from src.db_manager import DBManager

def main():

    print("[*] Starting Quant Bot Process...")
    # DB 매니저 초기화
    db_manager = DBManager()

    # 1. 설정 및 봇 초기화
    tickers = ["AAPL", "TSLA", "NVDA", "AMZN", "GOOGL", "SPY", "JOBY"]
    bot = TelegramBot()
    
    # 리포트 메시지를 담을 문자열 버퍼
    report_msg = f"🚀 *US Stock Quant Report* 🚀\n"
    report_msg += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
    report_msg += "--------------------------------\n"


    # 2. 데이터 수집
    loader = StockDataLoader(tickers)
    df = loader.fetch_daily_data(period="6mo")
    
    if df.empty:
        print("[!] Data fetch failed.")
        return

    # 3. 전략 적용
    analyzer = TechnicalAnalyzer(df)
    analyzer.add_sma(20).add_rsi(14).add_bollinger_bands()
    
    # [테스트용] RSI < 70 (많이 잡히게 설정)
    # [실전용] RSI < 40 으로 변경 권장
    rsi_threshold = 70
    buy_signals = analyzer.apply_strategy_rsi_reversal(rsi_threshold=rsi_threshold)
    
    latest_date = df['date'].max()
    today_signals = buy_signals[buy_signals['date'] == latest_date]

    if today_signals.empty:
        msg = "✅ 오늘은 매수 시그널이 없습니다. (No Action)"
        print(msg)
        bot.send_message(msg)
        return

    print(f"\n🔎 Found {len(today_signals)} stocks. Analyzing news...\n")
    
    # 4. AI 에이전트 분석 및 리포트 작성
    news_agent = NewsAgent(max_results=5) # 검색 담당 (기존 에이전트 활용)
    try:
        brain_agent = get_llm_agent()            # 분석 담당 AI
    except Exception as e:
        print(f"[!] AI Agent Init Failed: {e}")
        return

    # 전체 종목 개수 파악
    total_signals = len(today_signals)

    for i, (_, row) in enumerate(today_signals.iterrows()):
        
        ticker = row['ticker']
        price = row['close']
        rsi = row['rsi_14']
        
        print(f"Analyzing {ticker} ({i+1}/{total_signals})...")

        # 1. 뉴스 검색
        news_items = news_agent.search_news(ticker)
        
        # 2. LLM 분석
        ai_result = brain_agent.analyze_news(ticker, news_items)
        
        summary = ai_result['summary']
        score = ai_result['score']
        sentiment = ai_result['sentiment']

        analysis_data = {
                    'ticker': ticker,
                    'price': price,
                    'rsi': rsi,
                    'score': score,
                    'sentiment': sentiment,
                    'summary': summary
                }
        
        db_manager.save_analysis(analysis_data)

        # 이모지 결정
        icon = "⚖️"
        if score > 0.2: icon = "🔥"
        elif score < -0.2: icon = "💧"

        # 메시지 구성
        report_msg += f"🎯 *{ticker}* (RSI: {rsi:.1f})\n"
        report_msg += f"💰 Price: ${price:.2f}\n"
        report_msg += f"{icon} AI: {summary}\n"
        report_msg += f"📊 Score: {score} ({sentiment})\n"
        
        if news_items:
            top_news = news_items[0]['title'].replace("[", "(").replace("]", ")")
            report_msg += f"📰 News: {top_news}\n"
        
        report_msg += "--------------------------------\n"
        
        # [수정 3] 마지막 종목이 아닐 때만 15초 대기
        if i < total_signals - 1:
            # print(f"[*] Sleeping 15s to avoid API rate limit...")
            # time.sleep(15)
            pass
        else:
            # print("[*] All analysis complete. Skipping sleep.")
            print("[*] All analysis complete.")

    # 5. 최종 리포트 전송
    print("\n[*] Sending Report to Telegram...")
    bot.send_message(report_msg)
    print("[*] Done!")

if __name__ == "__main__":
    main()