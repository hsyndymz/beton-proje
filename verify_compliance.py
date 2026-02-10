import sys
import os

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

from logic.engineering import evaluate_mix_compliance

def test_compliance():
    print("--- KTŞ 2023 Uyum Testi Başlıyor ---\n")

    # Test Case 1: Fail S/C (XF4 requires max 0.45)
    mix_fail_wc = {
        "class": "C30/37 Yol Betonu", # "Yol" keyword triggers specific logic
        "exposure_class": "XF4",
        "wc": 0.48, # VIOLATION
        "cement": 350,
        "filler_content": 3.0,
        "sand_content": 45.0,
        "grading_violation": False
    }
    
    print("Test 1: Yüksek S/Ç (0.48 > 0.45)")
    res1 = evaluate_mix_compliance(mix_fail_wc)
    print(f"Status: {res1['status']}")
    print("Violations:", res1['violations'])
    print("-" * 30)

    # Test Case 2: Fail Cement (XF4 requires min 340)
    mix_fail_cem = {
        "class": "C30/37 Yol Betonu",
        "exposure_class": "XF4",
        "wc": 0.44,
        "cement": 330, # VIOLATION (Min 340)
        "filler_content": 3.0,
        "sand_content": 45.0
    }
    
    print("Test 2: Düşük Çimento (330 < 340)")
    res2 = evaluate_mix_compliance(mix_fail_cem)
    print(f"Status: {res2['status']}")
    print("Violations:", res2['violations'])
    print("-" * 30)
    
    # Test Case 3: Pass
    mix_pass = {
        "class": "C30/37 Yol Betonu",
        "exposure_class": "XF4",
        "wc": 0.44,
        "cement": 345, # OK (>340)
        "filler_content": 3.0, # OK (1-5)
        "sand_content": 45.0 # OK
    }
    
    print("Test 3: Uygun Karışım (S/Ç 0.44, Cem 345)")
    res3 = evaluate_mix_compliance(mix_pass)
    print(f"Status: {res3['status']}")
    print("Violations:", res3['violations'])
    print("-" * 30)

if __name__ == "__main__":
    with open('verification_results.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        test_compliance()
