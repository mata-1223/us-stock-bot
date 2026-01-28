import pandas as pd
from datetime import datetime
from src.collectors.stock_loader import StockDataLoader
from src.strategies.indicators import TechnicalAnalyzer
from src.agents.news_agent import NewsAgent
from src.utils.notifier import TelegramBot

def main():
    # 1. 설정 및 봇 초기화
    tickers = ["AAPL", "TSLA", "NVDA", "AMZN", "GOOGL", "SPY"]
    bot = TelegramBot()
    
    # 리포트 메시지를 담을 문자열 버퍼
    report_msg = f"🚀 *US Stock Quant Report* 🚀\n"
    report_msg += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
    report_msg += "--------------------------------\n"

    print("[*] Starting Quant Bot Process...")

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
    news_agent = NewsAgent(max_results=3)

    for _, row in today_signals.iterrows():
        ticker = row['ticker']
        price = row['close']
        rsi = row['rsi_14']
        
        # 터미널 출력용
        print(f"Analyzing {ticker}...")

        # 뉴스 분석
        news_items = news_agent.search_news(ticker)
        sentiment = news_agent.analyze_sentiment(news_items)
        
        # 이모지 결정
        score = sentiment['score']
        icon = "⚖️"
        if score > 0.1: icon = "✅"
        elif score < -0.2: icon = "⚠️"

        # 메시지 구성 (Markdown 문법)
        report_msg += f"🎯 *{ticker}* (RSI: {rsi:.1f})\n"
        report_msg += f"💰 Price: ${price:.2f}\n"
        report_msg += f"{icon} AI: {sentiment['summary']} ({score:.2f})\n"
        
        if news_items:
            # 텔레그램은 특수문자 처리가 까다로워서 제목만 심플하게
            top_news = news_items[0]['title'].replace("[", "(").replace("]", ")")
            report_msg += f"📰 News: {top_news}\n"
        
        report_msg += "--------------------------------\n"

    # 5. 최종 리포트 전송
    print("\n[*] Sending Report to Telegram...")
    bot.send_message(report_msg)
    print("[*] Done!")

if __name__ == "__main__":
    main()