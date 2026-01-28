import yfinance as yf
import pandas as pd
from typing import List
import os

class StockDataLoader:
    """
    미국 주식 시장 데이터를 수집하고 전처리하는 클래스입니다.
    Yahoo Finance API(yfinance)를 기반으로 작동합니다.
    """

    def __init__(self, tickers: List[str]):
        """
        StockDataLoader를 초기화합니다.

        Args:
            tickers (List[str]): 수집할 종목 티커 리스트 (예: ['AAPL', 'TSLA', 'NVDA'])
        """
        self.tickers: List[str] = tickers

    def fetch_daily_data(self, period: str = "1y") -> pd.DataFrame:
        """
        지정된 기간 동안의 일봉(Daily) 데이터를 수집합니다.

        Args:
            period (str): 데이터 수집 기간 (예: '1mo', '6mo', '1y'). Defaults to "1y".

        Returns:
            pd.DataFrame: [Date, Ticker, Open, High, Low, Close, Volume] 컬럼을 가진 DataFrame.
        """
        if not self.tickers:
            print("Warning: 티커 리스트가 비어 있습니다.")
            return pd.DataFrame()

        print(f"[*] Fetching data for {len(self.tickers)} tickers: {self.tickers}")
        
        # yfinance 다운로드 (수정 주가 반영)
        df: pd.DataFrame = yf.download(
            tickers=self.tickers,
            period=period,
            group_by='ticker',
            auto_adjust=True,
            actions=False,
            progress=False
        )

        if df.empty:
            return pd.DataFrame()

        # 데이터 구조 평탄화 (Flattening)
        if len(self.tickers) == 1:
            ticker = self.tickers[0]
            df['Ticker'] = ticker
            df = df.reset_index()
        else:
            # MultiIndex -> Long Format 변환
            df = df.stack(level=0)
            df.index.names = ['Date', 'Ticker']
            df = df.reset_index()

        # 컬럼 소문자 변환
        df.columns = [str(col).lower() for col in df.columns]
        
        # 날짜 컬럼 타입 보장
        df['date'] = pd.to_datetime(df['date'])

        print(f"[*] Successfully loaded {len(df)} rows.")
        return df

    def save_to_parquet(self, df: pd.DataFrame, path: str = "data/stock_price.parquet") -> None:
        """
        데이터를 Parquet 형식으로 저장합니다.
        """
        if df.empty:
            print("[!] 저장할 데이터가 없습니다.")
            return
        
        # 저장 경로의 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(path), exist_ok=True)
            
        try:
            df.to_parquet(path, index=False)
            print(f"[*] Data saved to {path}")
        except Exception as e:
            print(f"[!] Error saving parquet: {e}")

# --- 실행 테스트 (Main) ---
if __name__ == "__main__":
    # 테스트용 티커: 애플, 테슬라, 엔비디아, S&P500 ETF
    target_tickers: List[str] = ["AAPL", "TSLA", "NVDA", "SPY"]
    
    loader = StockDataLoader(tickers=target_tickers)
    
    # 1. 데이터 수집 (최근 1개월)
    data: pd.DataFrame = loader.fetch_daily_data(period="1mo")
    
    # 2. 결과 출력
    print("\n--- Data Preview ---")
    print(data.head())
    print("--------------------\n")
    
    # 3. 파일 저장 테스트
    loader.save_to_parquet(data)