import json
import os

DATA_DIR = "data"
PLANTS_FILE = os.path.join(DATA_DIR, "plants.json")

def santralleri_yukle():
    if os.path.exists(PLANTS_FILE):
        with open(PLANTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"merkez": {"name": "Merkez Santral", "location": "Şanlıurfa"}}

def santral_kaydet(p_id, p_data):
    plants = santralleri_yukle()
    plants[p_id] = p_data
    with open(PLANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(plants, f, ensure_ascii=False, indent=4)

def get_db_path(plant_id="merkez"):
    """Santral ID'sine göre proje dosya yolunu döner."""
    if not plant_id: plant_id = "merkez"
    return os.path.join(DATA_DIR, f"projects_{plant_id}.json")

def veriyi_kaydet(isim, data, plant_id="merkez"):
    db_file = get_db_path(plant_id)
    projeler = {}
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f: projeler = json.load(f)
    projeler[isim] = data
    with open(db_file, "w", encoding="utf-8") as f: json.dump(projeler, f, ensure_ascii=False, indent=4)

def veriyi_yukle(plant_id="merkez"):
    db_file = get_db_path(plant_id)
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def projesi_sil(isim, plant_id="merkez"):
    db_file = get_db_path(plant_id)
    projeler = {}
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f: projeler = json.load(f)
    if isim in projeler:
        del projeler[isim]
        with open(db_file, "w", encoding="utf-8") as f: json.dump(projeler, f, ensure_ascii=False, indent=4)
        return True
    return False

# --- AI EĞİTİM HAVUZU (GLOBAL) ---
# Havuz hala KÜRESEL kalıyor (Tüm santrallerin ortak aklı)
POOL_FILE = os.path.join(DATA_DIR, "ai_training_pool.json")

def havuz_kaydet(data_list):
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

def havuz_yukle():
    if os.path.exists(POOL_FILE):
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# --- SANTRAL / TESİS FAKTÖRLERİ (SANTRAL BAZLI) ---
def get_factor_path(plant_id="merkez"):
    return os.path.join(DATA_DIR, f"factors_{plant_id}.json")

def tesis_faktor_yukle(tesis_adi, plant_id="merkez"):
    f_path = get_factor_path(plant_id)
    if os.path.exists(f_path):
        with open(f_path, "r", encoding="utf-8") as f:
            faz = json.load(f)
            return faz.get(tesis_adi, 1.0)
    return 1.0

def tesis_faktor_kaydet(tesis_adi, deger, plant_id="merkez"):
    f_path = get_factor_path(plant_id)
    faz = {}
    if os.path.exists(f_path):
        with open(f_path, "r", encoding="utf-8") as f:
            faz = json.load(f)
    faz[tesis_adi] = deger
    with open(f_path, "w", encoding="utf-8") as f:
        json.dump(faz, f, ensure_ascii=False, indent=4)
