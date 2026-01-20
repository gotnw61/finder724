import hashlib
import hmac
import requests
import time
import json
from itertools import product
from typing import List, Optional, Dict
from telegram_notifier import TelegramNotifier

# BIP39 kelime listesi (İngilizce)
BIP39_WORDLIST_URL = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"

class BTCRecovery:
    def __init__(self, known_words: List[str], known_positions: Optional[List[int]] = None, 
                 telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        """
        known_words: Bildiğin kelimeler
        known_positions: Bu kelimelerin pozisyonları (0-11 arası, None ise tüm pozisyonlar denenir)
        telegram_token: Telegram bot token (opsiyonel)
        telegram_chat_id: Telegram chat ID (opsiyonel)
        """
        self.known_words = known_words
        self.known_positions = known_positions
        self.wordlist = self.load_wordlist()
        self.found_wallets = []
        self.attempts = 0
        self.telegram = TelegramNotifier(telegram_token, telegram_chat_id)
        
    def load_wordlist(self) -> List[str]:
        """BIP39 kelime listesini yükle"""
        try:
            response = requests.get(BIP39_WORDLIST_URL)
            return response.text.strip().split('\n')
        except:
            print("Kelime listesi indirilemedi, yerel liste kullanılıyor...")
            # Fallback: İlk 100 kelime (test için)
            return ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract"]
    
    def mnemonic_to_seed(self, mnemonic: str, passphrase: str = "") -> bytes:
        """Mnemonic'i seed'e çevir (BIP39)"""
        mnemonic_bytes = mnemonic.encode("utf-8")
        salt = ("mnemonic" + passphrase).encode("utf-8")
        return hashlib.pbkdf2_hmac("sha512", mnemonic_bytes, salt, 2048)
    
    def validate_checksum(self, words: List[str]) -> bool:
        """BIP39 checksum doğrulaması"""
        try:
            # Kelimeleri index'e çevir
            indices = [self.wordlist.index(word) for word in words]
            
            # 11-bit binary string'lere çevir
            bits = ''.join([bin(idx)[2:].zfill(11) for idx in indices])
            
            # Entropy ve checksum'ı ayır
            entropy_bits = bits[:len(bits) - len(bits)//33]
            checksum_bits = bits[len(bits) - len(bits)//33:]
            
            # Entropy'yi byte'lara çevir
            entropy_bytes = int(entropy_bits, 2).to_bytes(len(entropy_bits)//8, 'big')
            
            # Checksum hesapla
            hash_bytes = hashlib.sha256(entropy_bytes).digest()
            hash_bits = bin(int.from_bytes(hash_bytes, 'big'))[2:].zfill(256)
            
            # Checksum'ı karşılaştır
            expected_checksum = hash_bits[:len(checksum_bits)]
            
            return checksum_bits == expected_checksum
        except:
            return False
    
    def seed_to_addresses(self, seed: bytes) -> Dict[str, str]:
        """Seed'den BTC, ETH, SOL adresleri türet"""
        addresses = {}
        
        try:
            from bip32utils import BIP32Key
            
            # Master key
            master_key = BIP32Key.fromEntropy(seed[:64])
            
            # BTC: m/44'/0'/0'/0/0
            try:
                btc_key = master_key.ChildKey(44 + 2**31).ChildKey(0 + 2**31).ChildKey(0 + 2**31).ChildKey(0).ChildKey(0)
                addresses['BTC'] = btc_key.Address()
            except Exception as e:
                addresses['BTC'] = f"ERROR: {str(e)}"
            
            # ETH: m/44'/60'/0'/0/0
            try:
                eth_key = master_key.ChildKey(44 + 2**31).ChildKey(60 + 2**31).ChildKey(0 + 2**31).ChildKey(0).ChildKey(0)
                # ETH adresi için public key'den adres türet
                pub_key = eth_key.PublicKey()
                # Keccak256 hash (web3 gerekli)
                try:
                    from web3 import Web3
                    keccak_hash = Web3.keccak(pub_key[1:])  # İlk byte'ı atla
                    addresses['ETH'] = '0x' + keccak_hash[-20:].hex()
                except ImportError:
                    addresses['ETH'] = "LIBRARY_REQUIRED: web3"
            except Exception as e:
                addresses['ETH'] = f"ERROR: {str(e)}"
            
            # SOL: m/44'/501'/0'/0'
            try:
                sol_key = master_key.ChildKey(44 + 2**31).ChildKey(501 + 2**31).ChildKey(0 + 2**31).ChildKey(0 + 2**31)
                # Solana base58 encode
                try:
                    import base58
                    addresses['SOL'] = base58.b58encode(sol_key.PublicKey()).decode('utf-8')
                except ImportError:
                    addresses['SOL'] = "LIBRARY_REQUIRED: base58"
            except Exception as e:
                addresses['SOL'] = f"ERROR: {str(e)}"
                
        except Exception as e:
            addresses['BTC'] = f"ERROR: {str(e)}"
            addresses['ETH'] = f"ERROR: {str(e)}"
            addresses['SOL'] = f"ERROR: {str(e)}"
        
        return addresses
    
    def check_balances(self, addresses: Dict[str, str]) -> Dict[str, float]:
        """BTC, ETH, SOL bakiyelerini kontrol et"""
        balances = {}
        
        # BTC
        if addresses.get('BTC') and not addresses['BTC'].startswith('ERROR') and addresses['BTC'] != 'LIBRARY_REQUIRED':
            try:
                url = f"https://blockchain.info/q/addressbalance/{addresses['BTC']}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    balances['BTC'] = int(response.text) / 100000000
                else:
                    balances['BTC'] = 0.0
            except:
                balances['BTC'] = 0.0
        else:
            balances['BTC'] = 0.0
        
        # ETH
        if addresses.get('ETH') and not addresses['ETH'].startswith('ERROR') and 'LIBRARY_REQUIRED' not in addresses['ETH']:
            try:
                # Etherscan API (rate limit: 5 req/sec)
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={addresses['ETH']}&tag=latest"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == '1':
                        balances['ETH'] = int(data['result']) / 1e18
                    else:
                        balances['ETH'] = 0.0
                else:
                    balances['ETH'] = 0.0
            except:
                balances['ETH'] = 0.0
        else:
            balances['ETH'] = 0.0
        
        # SOL
        if addresses.get('SOL') and not addresses['SOL'].startswith('ERROR') and 'LIBRARY_REQUIRED' not in addresses['SOL']:
            try:
                # Solana RPC
                url = "https://api.mainnet-beta.solana.com"
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [addresses['SOL']]
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        balances['SOL'] = data['result']['value'] / 1e9
                    else:
                        balances['SOL'] = 0.0
                else:
                    balances['SOL'] = 0.0
            except:
                balances['SOL'] = 0.0
        else:
            balances['SOL'] = 0.0
        
        return balances
    
    def save_found_wallet(self, mnemonic: str, addresses: Dict[str, str], balances: Dict[str, float]):
        """Bulunan cüzdanı kaydet"""
        wallet_info = {
            "mnemonic": mnemonic,
            "addresses": addresses,
            "balances": balances,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.found_wallets.append(wallet_info)
        
        # Dosyaya kaydet
        with open("found_wallets.json", "a") as f:
            f.write(json.dumps(wallet_info) + "\n")
        
        # Ekrana büyük bir uyarı yazdır
        print(f"\n\n{'='*70}")
        print(f"🎉🎉🎉 CÜZDAN BULUNDU! 🎉🎉🎉")
        print(f"{'='*70}")
        for coin, balance in balances.items():
            if balance > 0:
                print(f"💰 {coin}: {balance}")
                print(f"📍 Adres: {addresses[coin]}")
        print(f"📝 Mnemonic: {mnemonic}")
        print(f"💾 Kaydedildi: found_wallets.json")
        print(f"{'='*70}\n")
        
        # Telegram'a bildir
        self.telegram.send_wallet_found(mnemonic, addresses, balances)
    
    def brute_force(self, max_attempts: int = None):
        """Brute force deneme - max_attempts None ise sınırsız"""
        print(f"Başlangıç bilgileri:")
        print(f"- Bilinen kelimeler: {self.known_words if self.known_words else 'Yok (tamamen rastgele)'}")
        print(f"- Bilinen pozisyonlar: {self.known_positions}")
        print(f"- Toplam kelime sayısı: {len(self.wordlist)}")
        print(f"- Maksimum deneme: {'Sınırsız (Ctrl+C ile durdurun)' if max_attempts is None else max_attempts}")
        
        if len(self.known_words) <= 2:
            print(f"\nDikkat: {len(self.known_words) if self.known_words else 0} kelime ile {12 - len(self.known_words) if self.known_words else 12} bilinmeyen için kombinasyon sayısı astronomik!")
        
        start_time = time.time()
        last_update_time = start_time
        last_telegram_update = start_time
        valid_checksums = 0
        wallets_with_balance = 0
        wallets_without_balance = 0
        
        # Telegram başlangıç bildirimi
        self.telegram.send_startup(self.known_words)
        
        # Eğer bilinen kelime varsa sabit pozisyonlara koy
        fixed_positions = {}
        if self.known_words:
            if self.known_positions and len(self.known_positions) == len(self.known_words):
                fixed_positions = dict(zip(self.known_positions, self.known_words))
            else:
                for i, word in enumerate(self.known_words):
                    fixed_positions[i] = word
        
        if fixed_positions:
            print(f"Sabit pozisyonlar: {fixed_positions}")
        else:
            print("Tamamen rastgele 12 kelime deneniyor...")
        
        print("\n" + "="*70)
        print("ÇALIŞIYOR... (Ctrl+C ile durdurun)")
        print("="*70)
        
        # Diğer pozisyonlar için rastgele kelimeler dene
        unknown_positions = [i for i in range(12) if i not in fixed_positions]
        
        try:
            while True:
                # Max attempt kontrolü
                if max_attempts is not None and self.attempts >= max_attempts:
                    break
                
                # 12 kelimelik liste oluştur
                words = [None] * 12
                
                # Bilinen kelimeleri yerleştir
                for pos, word in fixed_positions.items():
                    words[pos] = word
                
                # Bilinmeyen pozisyonlara rastgele kelimeler yerleştir
                import random
                for pos in unknown_positions:
                    words[pos] = random.choice(self.wordlist)
                
                self.attempts += 1
                
                # Checksum kontrolü
                if self.validate_checksum(words):
                    valid_checksums += 1
                    mnemonic = " ".join(words)
                    
                    # Seed ve adresler oluştur
                    seed = self.mnemonic_to_seed(mnemonic)
                    addresses = self.seed_to_addresses(seed)
                    
                    # En az bir adres başarılı mı?
                    has_valid_address = any(
                        not addr.startswith('ERROR') and 'LIBRARY_REQUIRED' not in addr 
                        for addr in addresses.values()
                    )
                    
                    if has_valid_address:
                        # Bakiyeleri kontrol et (rate limit için bekle)
                        time.sleep(0.5)  # API rate limit
                        balances = self.check_balances(addresses)
                        
                        # Toplam bakiye
                        total_balance = sum(balances.values())
                        
                        if total_balance > 0:
                            wallets_with_balance += 1
                            self.save_found_wallet(mnemonic, addresses, balances)
                        else:
                            wallets_without_balance += 1
                
                # İlerleme raporu (her 0.5 saniyede bir güncelle)
                current_time = time.time()
                if current_time - last_update_time >= 0.5:
                    elapsed = current_time - start_time
                    rate = self.attempts / elapsed
                    
                    # Tek satırda güncelleme (carriage return ile)
                    status = f"\r📊 Aranan: {self.attempts:,} | ✓ Geçerli: {valid_checksums:,} | 💰 Bakiyeli: {wallets_with_balance} | 📭 Bakiyesiz: {wallets_without_balance} | ⚡ {rate:.0f} d/sn | ⏱️  {elapsed:.0f}sn"
                    print(status, end='', flush=True)
                    last_update_time = current_time
                
                # Telegram durum güncellemesi (her 1 saatte bir)
                if current_time - last_telegram_update >= 3600:
                    elapsed_hours = (current_time - start_time) / 3600
                    self.telegram.send_status_update(
                        self.attempts, valid_checksums, wallets_with_balance,
                        wallets_without_balance, elapsed_hours
                    )
                    last_telegram_update = current_time
        
        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            print(f"\n\n{'='*70}")
            print("⛔ Kullanıcı tarafından durduruldu!")
            print(f"{'='*70}")
            print(f"📊 Toplam aranan: {self.attempts:,}")
            print(f"✓ Geçerli seed: {valid_checksums:,}")
            print(f"💰 Bakiyeli cüzdan: {wallets_with_balance}")
            print(f"📭 Bakiyesiz cüzdan: {wallets_without_balance}")
            print(f"⏱️  Süre: {elapsed:.0f} saniye ({elapsed/60:.1f} dakika)")
            print(f"⚡ Ortalama hız: {self.attempts/elapsed:.2f} deneme/sn")
            print(f"{'='*70}\n")
            return False
        except Exception as e:
            # Hata durumunda Telegram'a bildir
            self.telegram.send_error(str(e))
            raise
        
        if max_attempts is not None:
            elapsed = time.time() - start_time
            print(f"\n\n{'='*70}")
            print(f"✅ {max_attempts:,} deneme tamamlandı")
            print(f"{'='*70}")
            print(f"✓ Geçerli seed: {valid_checksums:,}")
            print(f"💰 Bakiyeli cüzdan: {wallets_with_balance}")
            print(f"📭 Bakiyesiz cüzdan: {wallets_without_balance}")
            print(f"⏱️  Süre: {elapsed:.0f} saniye")
            print(f"{'='*70}\n")
        return False


if __name__ == "__main__":
    # Config'den ayarları al
    try:
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, KNOWN_WORDS, KNOWN_POSITIONS, MAX_ATTEMPTS
        
        print("="*70)
        print("Bitcoin Seed Phrase Recovery Tool")
        print("="*70)
        print(f"\n📱 Telegram: {'✓ Aktif' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else '✗ Devre dışı'}")
        print(f"📝 Bilinen kelimeler: {len(KNOWN_WORDS) if KNOWN_WORDS else 0}")
        print(f"🎯 Maksimum deneme: {'Sınırsız' if MAX_ATTEMPTS is None else f'{MAX_ATTEMPTS:,}'}")
        print("\n" + "="*70 + "\n")
        
        if not KNOWN_WORDS:
            print("⚠️  Hiç kelime girilmemiş! Tamamen rastgele deneme yapılacak.")
            print("   Bu pratikte imkansız. En az 8-10 kelime önerilir!\n")
        
        print("🚀 Bot başlatılıyor...\n")
        
        # Recovery başlat
        recovery = BTCRecovery(
            known_words=KNOWN_WORDS, 
            known_positions=KNOWN_POSITIONS if KNOWN_POSITIONS else None,
            telegram_token=TELEGRAM_BOT_TOKEN,
            telegram_chat_id=TELEGRAM_CHAT_ID
        )
        recovery.brute_force(max_attempts=MAX_ATTEMPTS)
        
    except ImportError as e:
        print("❌ config.py bulunamadı veya eksik!")
        print(f"Hata: {e}")
        print("\nÖnce config.py oluştur!")
    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()
