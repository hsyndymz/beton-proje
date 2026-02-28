import json
import os
import streamlit as st

DATA_DIR = "data"
OCAK_FILE = os.path.join(DATA_DIR, "ocaklar.json")

@st.cache_data(ttl=600)
def ocaklari_yukle():
    if os.path.exists(OCAK_FILE):
        with open(OCAK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def ocak_kaydet(ocak_id, ocak_data):
    ocaklar = ocaklari_yukle()
    ocaklar[ocak_id] = ocak_data
    with open(OCAK_FILE, "w", encoding="utf-8") as f:
        json.dump(ocaklar, f, ensure_ascii=False, indent=4)
    ocaklari_yukle.clear()

def ocak_sil(ocak_id):
    ocaklar = ocaklari_yukle()
    if ocak_id in ocaklar:
        del ocaklar[ocak_id]
        with open(OCAK_FILE, "w", encoding="utf-8") as f:
            json.dump(ocaklar, f, ensure_ascii=False, indent=4)
        ocaklari_yukle.clear()
        return True, "Ocak silindi."
    return False, "Ocak bulunamadı."
