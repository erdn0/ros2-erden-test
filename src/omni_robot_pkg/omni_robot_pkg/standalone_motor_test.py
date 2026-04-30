#!/usr/bin/env python3
"""
RoboClaw Bağımsız Motor Test Aracı

Bu script ROS2'den tamamen bağımsızdır. Doğrudan roboclaw_3 kütüphanesini kullanarak
UART portu üzerinden RoboClaw sürücülerine komut gönderir.
Sürücülerin içerisindeki donanım veya PID ayarları KOD İLE DEĞİŞTİRİLMEZ (overwrite edilmez),
bunun yerine doğrudan sürücünün EEPROM'una kaydedilmiş mevcut ayarlar kullanılır.
"""

import time
import sys

# roboclaw_3.py dosyası ile aynı dizinde olduğunuzu veya bu dizinin Python PATH'inde olduğunu varsayıyoruz.
try:
    from roboclaw_3 import Roboclaw
except ImportError:
    print("HATA: roboclaw_3.py bulunamadı! Lütfen bu scripti roboclaw_3.py ile aynı dizinde çalıştırın.")
    sys.exit(1)

# --- KONFİGÜRASYON ---
PORT = '/dev/ttyAMA0'
BAUDRATE = 38400

# Adresler
ADDR1 = 0x80  # 128 (RC1)
ADDR2 = 0x81  # 129 (RC2)

# Test Parametreleri
TEST_SPEED = 1000      # saniyedeki tick hızı (Kendi robotunuza göre azaltıp artırabilirsiniz)
TEST_DURATION = 2.0    # Her bir yön için çalışma süresi (saniye)
PAUSE_DURATION = 1.0   # Yön değiştirirken ve motor değiştirirken bekleme süresi

def test_motor(rc, addr, motor_channel, name):
    print(f"\n[{name}] testi başlıyor...")
    
    # 1. Pozitif (+) Yönde Çalıştır
    print(f"  -> İLERİ (+) yönde çalıştırılıyor... (Hız: {TEST_SPEED} ticks/sn)")
    if motor_channel == 1:
        rc.SpeedM1(addr, TEST_SPEED)
    else:
        rc.SpeedM2(addr, TEST_SPEED)
        
    time.sleep(TEST_DURATION)
    
    # 2. Durdur ve bekle
    print(f"  -> Durduruluyor...")
    if motor_channel == 1:
        rc.SpeedM1(addr, 0)
    else:
        rc.SpeedM2(addr, 0)
        
    time.sleep(PAUSE_DURATION)
    
    # 3. Negatif (-) Yönde Çalıştır
    print(f"  -> GERİ (-) yönde çalıştırılıyor... (Hız: {-TEST_SPEED} ticks/sn)")
    if motor_channel == 1:
        rc.SpeedM1(addr, -TEST_SPEED)
    else:
        rc.SpeedM2(addr, -TEST_SPEED)
        
    time.sleep(TEST_DURATION)
    
    # 4. Durdur
    print(f"  -> Durduruluyor...")
    if motor_channel == 1:
        rc.SpeedM1(addr, 0)
    else:
        rc.SpeedM2(addr, 0)
        
    time.sleep(PAUSE_DURATION)
    print(f"[{name}] testi tamamlandı.")

def main():
    print("="*50)
    print("ROBOCLAW BAĞIMSIZ MOTOR TEST ARACI")
    print("="*50)
    
    # RoboClaw nesnesini oluştur
    rc = Roboclaw(PORT, BAUDRATE)
    
    # Bağlantıyı aç
    if rc.Open() == 0:
        print(f"HATA: {PORT} bağlantı noktası açılamadı!")
        print("Lütfen kabloları ve bağlantı izinlerini kontrol edin:")
        print(f"  sudo chmod 666 {PORT}")
        sys.exit(1)
        
    print(f"Port başarıyla açıldı: {PORT} @ {BAUDRATE}")
    print("Sürücü içindeki PID ve ayarlar korunuyor (Overwrite EDİLMİYOR).")
    print(f"Her motor sırayla önce +, sonra - yönde {TEST_DURATION} saniye çalışacak.\n")
    
    try:
        # Motor Eşleştirmesi (roboclaw_driver_node.py ile birebir aynı):
        # 1. RC1 (0x80) M2 -> Teker 1 (Sağ-Ön)
        test_motor(rc, ADDR1, 2, "TEKER 1 (Sağ-Ön) - [Adres: 0x80, Kanal: M2]")
        
        # 2. RC2 (0x81) M2 -> Teker 2 (Sol-Ön)
        test_motor(rc, ADDR2, 2, "TEKER 2 (Sol-Ön) - [Adres: 0x81, Kanal: M2]")
        
        # 3. RC1 (0x80) M1 -> Teker 3 (Arka)
        test_motor(rc, ADDR1, 1, "TEKER 3 (Arka)   - [Adres: 0x80, Kanal: M1]")
        
        print("\nTÜM TESTLER BAŞARIYLA TAMAMLANDI!")
        
    except KeyboardInterrupt:
        print("\nTest kullanıcı tarafından zorla durduruldu!")
    finally:
        # Program kapanırken veya hata anında her şeyi güvenli konuma al (Sıfırla)
        print("Tüm motorlara GÜVENLİ DUR (Speed 0) komutu gönderiliyor...")
        rc.SpeedM1(ADDR1, 0)
        rc.SpeedM2(ADDR1, 0)
        rc.SpeedM1(ADDR2, 0)
        rc.SpeedM2(ADDR2, 0)

if __name__ == '__main__':
    main()
