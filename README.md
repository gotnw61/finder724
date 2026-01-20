# Bitcoin Seed Phrase Recovery Tool

⚠️ **ÖNEMLİ UYARILAR:**
- Bu araç SADECE kendi cüzdanınızı kurtarmak içindir
- 2 kelime ile 10 bilinmeyen kelime için 2048^10 = ~1.27 septilyon kombinasyon var
- Modern bir bilgisayarda bu işlem 40 trilyon yıl sürer
- Bu gerçekçi bir kurtarma yöntemi DEĞİLDİR, sadece eğitim amaçlıdır

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
python btc_recovery.py
```

Program sizden şunları soracak:
1. Bildiğiniz kelimeleri (virgülle ayırın)
2. Bu kelimelerin pozisyonlarını biliyor musunuz?
3. Kaç deneme yapılsın?

## Nasıl Çalışır?

1. **Checksum Doğrulama**: BIP39 standardına göre geçersiz kombinasyonları eler
2. **Seed Türetme**: Geçerli mnemonic'lerden seed oluşturur
3. **Adres Türetme**: Seed'den Bitcoin adresi türetir (BIP44 path)
4. **Bakiye Kontrolü**: Blockchain.info API ile bakiye kontrol eder
5. **Kayıt**: Bakiyeli cüzdanları `found_wallets.json` dosyasına kaydeder

## Gerçekçi Beklentiler

**Senaryolar:**

| Bilinen Kelime | Bilinmeyen | Kombinasyon | Tahmini Süre |
|----------------|------------|-------------|--------------|
| 10 kelime      | 2 kelime   | ~4 milyon   | Birkaç saat  |
| 8 kelime       | 4 kelime   | ~17 trilyon | Yıllar       |
| 2 kelime       | 10 kelime  | ~1.27 septilyon | 40 trilyon yıl |

**Öneriler:**
- Eğer 6+ kelime hatırlıyorsanız, bu araç işe yarayabilir
- 2-3 kelime ile kurtarma pratikte imkansızdır
- Seed phrase'i başka yerlerden bulmaya çalışın (yedekler, notlar, e-postalar)

## API Rate Limits

Blockchain.info API ücretsizdir ama rate limit vardır:
- Saniyede 1 istek önerilir
- Çok fazla istek yaparsanız IP'niz engellenebilir
- Script otomatik olarak 0.5 saniye bekler

## Alternatif Çözümler

1. **BTCRecover**: Profesyonel açık kaynak araç
   - https://github.com/3rdIteration/btcrecover
   - GPU desteği var
   - Daha gelişmiş stratejiler

2. **Profesyonel Yardım**: 
   - Wallet recovery uzmanları
   - Genellikle başarı ücreti alırlar (%20-30)

3. **Hafıza Teknikleri**:
   - Hipnoterapi
   - Eski cihazlarınızı kontrol edin
   - Bulut yedeklerinizi tarayın

## Güvenlik

- Script'i sadece kendi bilgisayarınızda çalıştırın
- Bulunan cüzdanları hemen güvenli bir yere taşıyın
- `found_wallets.json` dosyasını güvenli tutun ve paylaşmayın

## Lisans

Bu araç eğitim amaçlıdır. Kendi sorumluluğunuzda kullanın.
