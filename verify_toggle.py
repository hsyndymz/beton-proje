import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from logic.engineering import evaluate_mix_compliance

def test_toggle():
    print("--- Standart Seçimi Toggle Testi ---\n")

    # Kontrol Karışımı: "Yol" projesi ama S/Ç 0.50 (Normalde KTŞ'ye göre RED)
    mix_yol = {
        "class": "C30/37 Beton Yol",
        "exposure_class": "XF4",
        "wc": 0.50,      # KTŞ: RED (Max 0.45) | TS EN 206: KABUL (XF4 Max 0.50/0.45? XF4 normalde 0.45 ama biz 206 modunda esneklik var mı bakacağız)
                         # Düzeltme: TS EN 206'da XF4 için max 0.45 veya 0.50 olabilir, ancak bizim kodda exp_limits['XC3'] default çekiyor eğer XF4 yoksa.
                         # Dur, EXPOSURE_CLASSES sözlüğüne bakalım. XF4: max_wc 0.45.
                         # Yani TS EN 206 modunda da XF4 seçilirse 0.45 sınırına takılır.
                         # Amaç "Yol" kelimesinden gelen EKSTRA katılığı (varsa) kaldırmak veya
                         # Kullanıcı "Yol" yazsa bile "TS EN 206" seçtiğinde, kodun "enforce_kts_road" flag'ini False yapıp yapmadığını görmek.
        "cement": 320,   # KTŞ: RED (Min 340) | TS EN 206: KABUL (XF4 Min 340? Hayır, XC4 vb. 300)
    }
    
    # 1. Mod: KTŞ 2023 (Varsayılan / Katı)
    print(f"Test 1: KTŞ 2023 Modu {mix_yol['class']}")
    res1 = evaluate_mix_compliance(mix_yol, standard_mode="KTS")
    print(f"Sonuç: {res1['status']} (Beklenen: RED)")
    if res1['violations']: print("İhlaller:", res1['violations'])
    print("-" * 30)

    # 2. Mod: TS EN 206 (Esnek / Genel Yapı)
    # Burada kullanıcı "Yol" yazmış olsa bile, standart modu 206 seçtiği için
    # Kodun "enforce_kts_road" false olmalı.
    # Ancak XF4'ün kendisi de 0.45 max wc istiyor olabilir.
    # Bu yüzden karışımı XC4 (Max 0.50) olarak değiştirelim veya XF4'ün 206 limitlerine bakalım.
    # EXPOSURE_CLASSES["XF4"]["min_cem"] = 340. Demek ki 206'da da 340.
    # Farkı görmek için XC4 (0.50, 300) kullanalım.
    
    mix_esnek = {
        "class": "C30/37 Beton Yol (Yan Yol)",
        "exposure_class": "XC4", # XC4: Max 0.50, Min 300
        "wc": 0.48,      # KTŞ Yol (0.45) -> RED | XC4 (0.50) -> KABUL
        "cement": 310,   # KTŞ Yol (340) -> RED | XC4 (300) -> KABUL
    }
    
    print(f"Test 2: KTŞ 2023 Modu [XC4 ama Yol ismi var]")
    res2 = evaluate_mix_compliance(mix_esnek, standard_mode="KTS")
    print(f"Sonuç: {res2['status']} (Beklenen: RED - Çünkü 'Yol' ismi var)")
    if res2['violations']: print("İhlaller:", res2['violations'])
    print("-" * 30)
    
    print(f"Test 3: TS EN 206 Modu [XC4 ve Yol ismi var]")
    res3 = evaluate_mix_compliance(mix_esnek, standard_mode="TS_EN_206")
    print(f"Sonuç: {res3['status']} (Beklenen: GREEN - Çünkü KTŞ zorlaması kapalı)")
    if res3['violations']: print("İhlaller:", res3['violations'])
    print("-" * 30)

if __name__ == "__main__":
    with open('verification_toggle.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        test_toggle()
