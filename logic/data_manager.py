import json
import os

DB_FILE = "projeler.json"

def veriyi_kaydet(isim, data):
    projeler = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: projeler = json.load(f)
    projeler[isim] = data
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(projeler, f, ensure_ascii=False, indent=4)

def veriyi_yukle():
    return json.load(open(DB_FILE, "r", encoding="utf-8")) if os.path.exists(DB_FILE) else {}

def projesi_sil(isim):
    projeler = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: projeler = json.load(f)
    if isim in projeler:
        del projeler[isim]
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(projeler, f, ensure_ascii=False, indent=4)
        return True
    return False

# --- AI EĞİTİM HAVUZU (GLOBAL) ---
POOL_FILE = "ai_training_pool.json"

def havuz_kaydet(data_list):
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

def havuz_yukle():
    if os.path.exists(POOL_FILE):
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
# --- SANTRAL / TESİS FAKTÖRLERİ ---
FACTOR_FILE = "tesis_faktorleri.json"

def tesis_faktor_yukle(tesis_adi):
    if os.path.exists(FACTOR_FILE):
        with open(FACTOR_FILE, "r", encoding="utf-8") as f:
            faz = json.load(f)
            return faz.get(tesis_adi, 1.0)
    return 1.0

def tesis_faktor_kaydet(tesis_adi, deger):
    faz = {}
    if os.path.exists(FACTOR_FILE):
        with open(FACTOR_FILE, "r", encoding="utf-8") as f:
            faz = json.load(f)
    faz[tesis_adi] = deger
    with open(FACTOR_FILE, "w", encoding="utf-8") as f:
        json.dump(faz, f, ensure_ascii=False, indent=4)
