"""
Colab için direkt başlatıcı - Input gerektirmez
"""
from btc_recovery import BTCRecovery

# Config'den al
try:
    from config import *
except ImportError:
    print("❌ config.py bulunamadı!")
    print("Önce config.py oluştur!")
    exit(1)

print("="*70)
print("🚀 BITCOIN CÜZDAN KURTARMA BOTU")
print("="*70)
print(f"\n📱 Telegram: {'✓ Aktif' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else '✗ Devre dışı'}")
print(f"📝 Bilinen kelimeler: {len(KNOWN_WORDS) if KNOWN_WORDS else 0}")
print(f"🎯 Maksimum deneme: {'Sınırsız' if MAX_ATTEMPTS is None else f'{MAX_ATTEMPTS:,}'}")
print("\n" + "="*70 + "\n")

if not KNOWN_WORDS:
    print("⚠️  Hiç kelime girilmemiş! Tamamen rastgele deneme yapılacak.")
    print("   Bu pratikte imkansız. En az 8-10 kelime gir!\n")

# Recovery başlat
recovery = BTCRecovery(
    known_words=KNOWN_WORDS,
    known_positions=KNOWN_POSITIONS if KNOWN_POSITIONS else None,
    telegram_token=TELEGRAM_BOT_TOKEN if 'TELEGRAM_BOT_TOKEN' in dir() else None,
    telegram_chat_id=TELEGRAM_CHAT_ID if 'TELEGRAM_CHAT_ID' in dir() else None
)

print("🚀 Bot başlatılıyor...\n")

# Çalıştır
try:
    recovery.brute_force(max_attempts=MAX_ATTEMPTS if 'MAX_ATTEMPTS' in dir() else None)
except KeyboardInterrupt:
    print("\n\n⛔ Durduruldu!")
except Exception as e:
    print(f"\n\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
