import os
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class TelegramBot:
    """
    텔레그램 메시지 전송을 담당하는 클래스입니다.
    """
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            print("[!] Warning: .env 파일에 텔레그램 설정이 없습니다.")

    def send_message(self, message: str) -> None:
        """
        지정된 Chat ID로 메시지를 전송합니다.
        """
        if not self.token or not self.chat_id:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"  # 마크다운 스타일 지원
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print("[*] Telegram message sent successfully.")
            else:
                print(f"[!] Failed to send message: {response.text}")
        except Exception as e:
            print(f"[!] Telegram Error: {e}")

# --- 테스트 실행 ---
if __name__ == "__main__":
    bot = TelegramBot()
    bot.send_message("🚀 테스트 메시지입니다.\n**굵게** 표시도 가능합니다.")