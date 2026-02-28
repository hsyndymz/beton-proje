import json
import os
import streamlit as st

DATA_DIR = "data"
PLANTS_FILE = os.path.join(DATA_DIR, "plants.json")

@st.cache_data(ttl=600)
def santralleri_yukle():
    if os.path.exists(PLANTS_FILE):
        with open(PLANTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"merkez": {"name": "Merkez Santral", "location": "Şanlıurfa"}}

def santral_kaydet(p_id, p_data):
    plants = santralleri_yukle()
    # Cache'i temizle çünkü veri değişti
    santralleri_yukle.clear()
    plants[p_id] = p_data
    with open(PLANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(plants, f, ensure_ascii=False, indent=4)

def santral_sil(p_id):
    plants = santralleri_yukle()
    if p_id in plants:
        if p_id == "merkez": return False, "Merkez santral silinemez."
        # Cache'i temizle
        santralleri_yukle.clear()
        del plants[p_id]
        with open(PLANTS_FILE, "w", encoding="utf-8") as f:
            json.dump(plants, f, ensure_ascii=False, indent=4)
        return True, "Santral silindi."
    return False, "Santral bulunamadı."

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
    # Cache'i temizle
    veriyi_yukle.clear()

@st.cache_data(ttl=300)
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
        veriyi_yukle.clear()
        return True
    return False

# --- AI EĞİTİM HAVUZU (GLOBAL) ---
# Havuz hala KÜRESEL kalıyor (Tüm santrallerin ortak aklı)
POOL_FILE = os.path.join(DATA_DIR, "ai_training_pool.json")

def havuz_kaydet(data_list):
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    havuz_yukle.clear()

@st.cache_data(ttl=3600)
def havuz_yukle():
    if os.path.exists(POOL_FILE):
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# --- SANTRAL / TESİS FAKTÖRLERİ (SANTRAL BAZLI) ---
def get_factor_path(plant_id="merkez"):
    return os.path.join(DATA_DIR, f"factors_{plant_id}.json")

@st.cache_data(ttl=600)
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
    tesis_faktor_yukle.clear()

# --- AI TEKNİK BÜLTEN (KÜRESEL PAYLAŞIM) ---
SHARED_INSIGHTS_FILE = os.path.join(DATA_DIR, "shared_insights.json")

def shared_insight_kaydet(insight):
    insights = shared_insight_yukle() # Cache'den değil, direkt dosyadan okumalı aslında ama append için farketmez
    insights.append(insight)
    # Son 15 bülten kaydını tutalım
    with open(SHARED_INSIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(insights[-15:], f, ensure_ascii=False, indent=4)
    shared_insight_yukle.clear()

@st.cache_data(ttl=3600)
def shared_insight_yukle():
    if os.path.exists(SHARED_INSIGHTS_FILE):
        with open(SHARED_INSIGHTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def shared_insight_sil(index):
    insights = shared_insight_yukle()
    if 0 <= index < len(insights):
        del insights[index]
        with open(SHARED_INSIGHTS_FILE, "w", encoding="utf-8") as f:
            json.dump(insights, f, ensure_ascii=False, indent=4)
        shared_insight_yukle.clear()

# --- KGM ONAYLI ARŞİV (2011 - GÜNÜMÜZ) ---
KGM_ARCHIVE_FILE = os.path.join(DATA_DIR, "kgm_approved_archive.json")

def kgm_arsiv_kaydet(data_list):
    with open(KGM_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    kgm_arsiv_yukle.clear()

@st.cache_data(ttl=3600)
def kgm_arsiv_yukle():
    if os.path.exists(KGM_ARCHIVE_FILE):
        with open(KGM_ARCHIVE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def kgm_arsiv_ekle(record):
    """Tek bir onayı arşive ekler."""
    archive = kgm_arsiv_yukle()
    record["is_approved"] = True
    record["source"] = "KGM Official (2011 Archive)"
    archive.append(record)
    kgm_arsiv_kaydet(archive)
