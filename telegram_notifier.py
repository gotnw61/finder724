import requests
import json
from typing import Optional

class TelegramNotifier:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Telegram bot bildirici
        
        Bot oluşturmak için:
        1. Telegram'da @BotFather'a git
        2. /newbot komutunu kullan
        3. Bot token'ı al
        4. Chat ID için: @userinfobot'a /start yaz
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        
        if not self.enabled:
            print("⚠️  Telegram bildirimleri devre dışı (token veya chat_id yok)")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Telegram'a mesaj gönder"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Telegram gönderim hatası: {e}")
            return False
    
    def send_wallet_found(self, mnemonic: str, addresses: dict, balances: dict):
        """Cüzdan bulundu bildirimi"""
        balance_text = ""
        for coin, balance in balances.items():
            if balance > 0:
                balance_text += f"💰 <b>{coin}:</b> {balance}\n📍 {addresses[coin]}\n\n"
        
        message = f"""
🎉🎉🎉 <b>CÜZDAN BULUNDU!</b> 🎉🎉🎉

{balance_text}
📝 <b>Mnemonic:</b>
<code>{mnemonic}</code>

⚠️ <b>HEMEN GÜVENLI BİR YERE TAŞIYIN!</b>
"""
        return self.send_message(message)
    
    def send_status_update(self, attempts: int, valid_seeds: int, wallets_found: int, 
                          wallets_checked: int, uptime_hours: float):
        """Durum güncellemesi"""
        message = f"""
📊 <b>Durum Raporu</b>

💰 <b>Coinler:</b> BTC + ETH + SOL

🔍 Toplam deneme: {attempts:,}
✓ Geçerli seed: {valid_seeds:,}
💰 Bakiyeli cüzdan: {wallets_found}
📭 Kontrol edilen: {wallets_checked}
⏱️ Çalışma süresi: {uptime_hours:.1f} saat
⚡ Hız: {attempts/(uptime_hours*3600):.0f} deneme/sn
"""
        return self.send_message(message)
    
    def send_startup(self, known_words: list):
        """Başlangıç bildirimi"""
        message = f"""
🚀 <b>Multi-Coin Bot Başlatıldı</b>

💰 <b>Desteklenen Coinler:</b>
• Bitcoin (BTC)
• Ethereum (ETH)
• Solana (SOL)

📝 Bilinen kelimeler: {len(known_words)}
🎯 Hedef: Cüzdan kurtarma
⏰ Başlangıç: {self._get_timestamp()}

Bot 7/24 çalışmaya başladı!
Her 1 saatte durum raporu gelecek.
"""
        return self.send_message(message)
    
    def send_error(self, error_message: str):
        """Hata bildirimi"""
        message = f"""
❌ <b>HATA</b>

{error_message}

⏰ {self._get_timestamp()}
"""
        return self.send_message(message)
    
    def _get_timestamp(self):
        """Zaman damgası"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
