import os
import json
import sys

# Proje ana dizinini path'e ekle
sys.path.append(os.getcwd())

from logic.data_manager import ocak_kaydet, ocaklari_yukle, ocak_sil

def test_quarry_ops():
    print("Testing Quarry Operations...")
    
    test_id = "test_ocak_1"
    test_data = {
        "name": "Test Ocağı",
        "lat": 37.5,
        "lon": 38.5,
        "lithology": "Bazalt",
        "la_wear": 15.0,
        "mb_value": 0.2,
        "asr_risk": "İnert",
        "cementation_index": 1.2,
        "description": "Test açıklaması",
        "updated_at": "2026-02-03 16:30"
    }
    
    # 1. Kaydet
    ocak_kaydet(test_id, test_data)
    print("Save OK")
    
    # 2. Yükle ve Kontrol Et
    ocaklar = ocaklari_yukle()
    if test_id in ocaklar and ocaklar[test_id]["name"] == "Test Ocağı":
        print("Load OK")
    else:
        print("Load FAILED")
        return False
        
    # 3. Sil
    if ocak_sil(test_id):
        print("Delete OK")
    else:
        print("Delete FAILED")
        return False
        
    # 4. Silindiğini Kontrol Et
    ocaklar_after = ocaklari_yukle()
    if test_id not in ocaklar_after:
        print("Final Consistency OK")
    else:
        print("Final Consistency FAILED")
        return False
        
    return True

if __name__ == "__main__":
    if test_quarry_ops():
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ TESTS FAILED")
        sys.exit(1)
