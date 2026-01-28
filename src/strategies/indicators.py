import pandas as pd
import numpy as np
from typing import Optional

class TechnicalAnalyzer:
    """
    주가 데이터(DataFrame)를 받아 기술적 지표를 계산하고
    매매 신호(Signal)를 생성하는 클래스입니다.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df (pd.DataFrame): [Date, Ticker, Open, High, Low, Close, Volume] 컬럼을 가진 데이터프레임
        """
        # 원본 데이터 보존을 위해 복사
        self.df = df.copy()
        
        # 데이터가 비어있지 않은지 확인
        if self.df.empty:
            raise ValueError("Input DataFrame is empty.")
            
        # 날짜 오름차순 정렬 (지표 계산의 정확성을 위해 필수)
        self.df = self.df.sort_values(by=['ticker', 'date'])

    def add_sma(self, window: int = 20) -> 'TechnicalAnalyzer':
        """
        단순 이동 평균(Simple Moving Average)을 계산하여 컬럼에 추가합니다.
        
        Args:
            window (int): 이동 평균 기간 (예: 20일, 50일, 200일)
        """
        col_name = f'sma_{window}'
        
        # 종목별(ticker)로 그룹화하여 이동평균 계산
        self.df[col_name] = self.df.groupby('ticker')['close'].transform(
            lambda x: x.rolling(window=window).mean()
        )
        return self

    def add_rsi(self, window: int = 14) -> 'TechnicalAnalyzer':
        """
        상대 강도 지수(RSI)를 계산하여 컬럼에 추가합니다.
        RSI는 70 이상이면 과매수(매도 고려), 30 이하이면 과매도(매수 고려)로 해석합니다.

        Args:
            window (int): RSI 계산 기간. Defaults to 14.
        """
        col_name = f'rsi_{window}'

        def calculate_rsi_series(series: pd.Series) -> pd.Series:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

            rs = gain / loss
            # loss가 0인 경우(무한대) 처리
            rs = rs.replace([np.inf, -np.inf], 0)
            return 100 - (100 / (1 + rs))

        self.df[col_name] = self.df.groupby('ticker')['close'].transform(calculate_rsi_series)
        return self

    def add_bollinger_bands(self, window: int = 20, num_std: int = 2) -> 'TechnicalAnalyzer':
        """
        볼린저 밴드(Bollinger Bands)를 계산합니다 (Upper, Middle, Lower).
        """
        # 중간 밴드 (SMA)
        self.df['bb_mid'] = self.df.groupby('ticker')['close'].transform(
            lambda x: x.rolling(window=window).mean()
        )
        
        # 표준편차
        std_dev = self.df.groupby('ticker')['close'].transform(
            lambda x: x.rolling(window=window).std()
        )

        self.df['bb_upper'] = self.df['bb_mid'] + (std_dev * num_std)
        self.df['bb_lower'] = self.df['bb_mid'] - (std_dev * num_std)
        
        return self

    def apply_strategy_rsi_reversal(self, rsi_threshold: int = 30) -> pd.DataFrame:
        """
        [전략] RSI 역추세 전략 적용
        - 조건: RSI가 threshold(기본 30) 이하인 경우 '매수(Buy)' 신호 발생
        
        Returns:
            pd.DataFrame: 매수 신호가 뜬 행들만 필터링하여 반환
        """
        # 먼저 지표가 있는지 확인하고 없으면 계산
        rsi_col = f'rsi_14'
        if rsi_col not in self.df.columns:
            self.add_rsi(14)

        # 매수 신호 조건: RSI < 30 (과매도 구간)
        signal_mask = self.df[rsi_col] < rsi_threshold
        
        # 결과 필터링 (최근 날짜 기준)
        signals = self.df[signal_mask].copy()
        
        return signals

    def get_result(self) -> pd.DataFrame:
        """최종 처리된 데이터프레임을 반환합니다."""
        return self.df

# --- 실행 테스트 ---
if __name__ == "__main__":
    # 1. 저장된 Parquet 데이터 로드
    try:
        df = pd.read_parquet("data/stock_price.parquet")
        print(f"[*] Loaded data with {len(df)} rows.")

        # 2. 분석기 초기화
        analyzer = TechnicalAnalyzer(df)

        # 3. 지표 추가 (Method Chaining 활용)
        analyzer.add_sma(20).add_rsi(14).add_bollinger_bands()
        
        # 4. 전체 데이터 확인
        full_data = analyzer.get_result()
        print("\n--- Indicators Added ---")
        print(full_data[['date', 'ticker', 'close', 'rsi_14', 'bb_upper']].tail())

        # 5. 매수 신호 탐색 (RSI < 40으로 테스트)
        print("\n--- Buy Signals (RSI < 40) ---")
        buy_signals = analyzer.apply_strategy_rsi_reversal(rsi_threshold=40)
        
        if not buy_signals.empty:
            print(buy_signals[['date', 'ticker', 'close', 'rsi_14']])
        else:
            print("No buy signals found.")

    except FileNotFoundError:
        print("[!] data/stock_price.parquet 파일이 없습니다. stock_loader.py를 먼저 실행하세요.")