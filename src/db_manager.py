import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class StockAnalysis(Base):
    __tablename__ = 'daily_analysis'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    ticker = Column(String(10))
    price = Column(Float)
    rsi = Column(Float)
    ai_score = Column(Float)
    ai_sentiment = Column(String(20))
    ai_summary = Column(Text)

class DBManager:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("[!] Warning: DATABASE_URL not found. DB disabled.")
            self.engine = None
            return

        try:
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            print("[*] Database Connected Successfully.")
        except Exception as e:
            print(f"[!] DB Connection Failed: {e}")
            self.engine = None

    def save_analysis(self, data: dict):
        """
        분석 결과를 저장하되, '같은 날짜 + 같은 종목'이 있으면 덮어씁니다(Update).
        """
        if not self.engine: return

        session = self.Session()
        try:
            # 1. 오늘 날짜 구하기 (YYYY-MM-DD)
            today = datetime.now().date()
            ticker = data['ticker']

            # 2. 이미 오늘 저장된 데이터가 있는지 확인 (SELECT)
            # func.date()를 써서 시간(HH:MM:SS)은 무시하고 날짜만 비교
            existing_record = session.query(StockAnalysis).filter(
                StockAnalysis.ticker == ticker,
                func.date(StockAnalysis.created_at) == today
            ).first()

            if existing_record:
                # [CASE 1] 이미 있으면 -> 내용만 업데이트 (Update)
                print(f"   🔄 Updating existing record for {ticker}...")
                existing_record.price = data['price']
                existing_record.rsi = data['rsi']
                existing_record.ai_score = data.get('score', 0.0)
                existing_record.ai_sentiment = data.get('sentiment', 'NEUTRAL')
                existing_record.ai_summary = data.get('summary', '')
                existing_record.created_at = datetime.now() # 수정 시간 갱신
            else:
                # [CASE 2] 없으면 -> 새로 추가 (Insert)
                print(f"   💾 Inserting new record for {ticker}...")
                new_record = StockAnalysis(
                    ticker=ticker,
                    price=data['price'],
                    rsi=data['rsi'],
                    ai_score=data.get('score', 0.0),
                    ai_sentiment=data.get('sentiment', 'NEUTRAL'),
                    ai_summary=data.get('summary', '')
                )
                session.add(new_record)

            session.commit()
            
        except Exception as e:
            print(f"   ⚠️ DB Error: {e}")
            session.rollback()
        finally:
            session.close()