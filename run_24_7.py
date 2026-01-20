"""
7/24 Çalışan Bitcoin Cüzdan Kurtarma Botu
Sunucuda çalıştırmak için optimize edilmiş
"""
import sys
import time
from btc_recovery import BTCRecovery
from config import *

def main():
    print("="*70)
    print("🚀 BITCOIN CÜZDAN KURTARMA BOTU - 7/24 MOD")
    print("="*70)
    print(f"\n📱 Telegram bildirimleri: {'✓ Aktif' if TELEGRAM_BOT_TOKEN else '✗ Devre dışı'}")
    print(f"📝 Bilinen kelimeler: {len(KNOWN_WORDS) if KNOWN_WORDS else 'Yok (tamamen rastgele)'}")
    print(f"🎯 Maksimum deneme: {'Sınırsız' if MAX_ATTEMPTS is None else f'{MAX_ATTEMPTS:,}'}")
    print(f"⏰ Durum raporu: Her {STATUS_UPDATE_INTERVAL/3600:.1f} saatte bir")
    print("\n" + "="*70)
    
    # Uyarı (ama otomatik devam et - Colab için)
    if not KNOWN_WORDS or len(KNOWN_WORDS) < 8:
        print("\n⚠️  UYARI: Çok az kelime biliyorsun!")
        print("   Bulma ihtimali astronomik derecede düşük.")
        print("   En az 8-10 kelime bilmen önerilir.")
        print("\n   Otomatik olarak başlatılıyor...")
    
    print("\n🚀 Bot başlatılıyor...")
    print("   Ctrl+C ile durdurabilirsin\n")
    
    try:
        # Recovery başlat
        recovery = BTCRecovery(
            known_words=KNOWN_WORDS,
            known_positions=KNOWN_POSITIONS,
            telegram_token=TELEGRAM_BOT_TOKEN,
            telegram_chat_id=TELEGRAM_CHAT_ID
        )
        
        # Sınırsız çalıştır
        recovery.brute_force(max_attempts=MAX_ATTEMPTS)
        
    except KeyboardInterrupt:
        print("\n\n⛔ Kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"\n\n❌ HATA: {e}")
        # Telegram'a hata bildir
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            from telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            notifier.send_error(f"Bot durdu: {str(e)}")
        raise

if __name__ == "__main__":
    main()
