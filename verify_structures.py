import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from logic.engineering import evaluate_mix_compliance

def test_structures():
    print("--- Yapı Tipi Uyumluluk Testi (Bina vs Yol) ---\n")

    # Senaryo 1: Standart Bina (C25/30 - XC1)
    # Class ismi tam eşleşmeli ki CONCRETE_RULES["C25/30"] çekilsin.
    mix_bina = {
        "class": "C25/30", 
        "exposure_class": "XC1",
        "wc": 0.60,      # C25/30 için limit 0.60. (Yol olsa 0.45) -> KABUL
        "cement": 280,   # C25/30 için min 280. (Yol olsa 340) -> KABUL
        "filler_content": 3.0,
        "sand_content": 45.0,
        "grading_violation": False,
        "pred_mpa": 32.0 # Hedef 30, Tahmin 32 -> KABUL
    }
    
    print(f"Test 1: Bina {mix_bina['class']} [XC1]")
    res1 = evaluate_mix_compliance(mix_bina)
    print(f"Sonuç: {res1['status']} (Beklenen: GREEN)")
    if res1['violations']: print("İhlaller:", res1['violations'])
    print("-" * 30)

    # Senaryo 2: Sanat Yapısı (C30/37 Sanat Yapısı - XD1)
    # Dictionary'de "C30/37 Sanat Yapısı" yok, default C30/37'ye döner (Doğru).
    # "Yol" kelimesi yok -> Standart XD1 limitleri (S/Ç 0.55, Cem 300)
    mix_kopru = {
        "class": "C30/37 Sanat Yapısı",
        "exposure_class": "XD1",
        "wc": 0.50,      # 0.55'in altında -> KABUL
        "cement": 320,   # 300'ün üstünde -> KABUL
        "filler_content": 3.0,
        "sand_content": 45.0,
        "pred_mpa": 40.0 # Hedef 37, Tahmin 40 -> KABUL
    }
    
    print(f"Test 2: Sanat Yapısı {mix_kopru['class']} [XD1]")
    res2 = evaluate_mix_compliance(mix_kopru)
    print(f"Sonuç: {res2['status']} (Beklenen: GREEN)")
    if res2['violations']: print("İhlaller:", res2['violations'])
    print("-" * 30)
    
    # Senaryo 3: Beton Yol (C30/37 Beton Yol - XF4)
    # "Yol" kelimesi var -> KTŞ 2023 limitleri (S/Ç 0.45, Cem 340)
    mix_yol = {
        "class": "C30/37 Beton Yol",
        "exposure_class": "XF4",
        "wc": 0.50,      # 0.45'ten büyük -> RED
        "cement": 320,   # 340'tan küçük -> RED
        "pred_mpa": 40.0
    }
    
    print(f"Test 3: Yol {mix_yol['class']} [XF4] (Kontrol)")
    res3 = evaluate_mix_compliance(mix_yol)
    print(f"Sonuç: {res3['status']} (Beklenen: RED)")
    if res3['violations']: print("İhlaller:", res3['violations'])
    print("-" * 30)

if __name__ == "__main__":
    with open('verification_structures.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        test_structures()
