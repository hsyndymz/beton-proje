import streamlit as st
import os
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from logic.data_manager import (
    veriyi_yukle, veriyi_kaydet, havuz_yukle, havuz_kaydet, 
    tesis_faktor_yukle, tesis_faktor_kaydet
)
from logic.engineering import (
    calculate_passing, calculate_theoretical_mpa, evaluate_mix_compliance, 
    classify_plant, get_std_limits
)
from logic.ai_model import train_prediction_model, predict_strength_ai, generate_suggestions
from logic.report_generator import generate_kgm_raporu
from logic.state_manager import init_session_state
from logic.modular_tabs import render_tab_1, render_tab_2, render_tab_3, render_tab_4, render_tab_5, render_tab_management
from logic.auth_manager import check_login, register_user

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="BetaMix AI - KGM Beton Dizayn", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# --- LOGIN SİSTEMİ ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    # Giriş ekranında sidebar'ı gizle
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown('<div style="padding: 1rem; border-radius: 10px; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;">', unsafe_allow_html=True)
        st.title("🏗️ BETON TASARIMA GİRİŞ")
        
        l_tab, r_tab = st.tabs(["🔑 Giriş Yap", "📝 Kaydol (Üyelik Başvurusu)"])
        
        with l_tab:
            user_input = st.text_input("Kullanıcı Adı", key="login_user")
            pass_input = st.text_input("Şifre", type="password", key="login_pass")
            if st.button("Sisteme Gir", use_container_width=True):
                login_res = check_login(user_input, pass_input)
                if isinstance(login_res, dict) and "error" in login_res:
                    st.warning(f"⏳ {login_res['error']}")
                elif login_res:
                    st.session_state['authenticated'] = True
                    st.session_state['user_info'] = login_res
                    st.session_state['username'] = user_input
                    st.success("Giriş başarılı! Yükleniyor...")
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")
        with r_tab:
            reg_name = st.text_input("Ad Soyad", key="reg_name")
            reg_user = st.text_input("Kullanıcı Adı", key="reg_user")
            reg_pass = st.text_input("Şifre", type="password", key="reg_pass")
            if st.button("Başvuru Yap", use_container_width=True):
                if not reg_name or not reg_user or not reg_pass:
                    st.error("Lütfen tüm alanları doldurun!")
                else:
                    success, msg = register_user(reg_user, reg_pass, reg_name)
                    if success:
                        st.success("✅ Başvurunuz başarıyla alındı! SuperAdmin onayı sonrası giriş yapabilirsiniz.")
                        st.info("💡 Genellikle 24 saat içinde onaylanır.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- SANTRAL SEÇİMİ (Multi-Plant) ---
if 'active_plant' not in st.session_state:
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    user_info = st.session_state['user_info']
    
    plants_db = {}
    if os.path.exists("data/plants.json"):
        with open("data/plants.json", "r", encoding="utf-8") as f:
            plants_db = json.load(f)
            
    # SuperAdmin istisnası: Tüm santrallere erişim sağla
    if user_info.get('role') == 'SuperAdmin':
        user_plants = list(plants_db.keys())
    else:
        user_plants = user_info.get('assigned_plants', ['merkez'])
    
    options = {p_id: plants_db.get(p_id, {"name": p_id})["name"] for p_id in user_plants}
    
    col_s1, col_s2, col_s3 = st.columns([1, 1.5, 1])
    with col_s2:
        st.markdown('<div style="padding: 2rem; border-radius: 10px; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;">', unsafe_allow_html=True)
        st.title("🏭 Santral Seçimi")
        st.write(f"Hoş geldiniz, **{user_info.get('full_name')}**")
        selected_p = st.selectbox("Lütfen çalışmak istediğiniz santrali seçin:", 
                                  options=list(options.keys()), 
                                  format_func=lambda x: options[x])
        if st.button("Santrale Giriş Yap", use_container_width=True):
            st.session_state['active_plant'] = selected_p
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Giriş yapılmış ve santral seçilmişse devam et...
user_info = st.session_state['user_info']
is_admin = user_info.get('role') in ["Admin", "SuperAdmin"]
is_super_admin = user_info.get('role') == "SuperAdmin"

# CSS: Kararlı Mühendislik Arayüzü
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    
    div.stMetric {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    /* Sadece etiketler ve düz metinler beyaz olsun */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }
    
    /* Giriş kutularının içindeki yazıların okunabilir olması için (siyah kalmalı) */
    section[data-testid="stSidebar"] input {
        color: #1e293b !important;
        background-color: white !important;
    }
    
    .stButton button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL VERİLER ---
elek_serisi = [31.5, 22.4, 16.0, 11.2, 8.0, 5.6, 4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.063]
materials = ["No:2 (15-25)", "No:1 (5-15)", "K.Kum (0-5)", "D.Kum (0-7)"]

CONCRETE_RULES = {
    "C25/30": {"min_mpa": 30, "target_mpa": 33},
    "C30/37": {"min_mpa": 37, "target_mpa": 40},
    "C35/45": {"min_mpa": 45, "target_mpa": 48},
    "C40/50": {"min_mpa": 50, "target_mpa": 54}
}

TS_STANDARDS_CONTEXT = """
TS 802: Beton Karışım Hesabı Esasları
TS EN 206: Beton - Özellik, Performans, İmalat ve Uygunluk
KGM Teknik Şartnamesi Kısım 16: Beton ve Betonarme İşleri
"""

def get_global_qc_history(include_pool=True):
    active_p = st.session_state.get('active_plant', 'merkez')
    all_data = veriyi_yukle(plant_id=active_p)
    global_hist = []
    for p_name, p_data in all_data.items():
        if isinstance(p_data, dict) and "qc_history" in p_data:
            global_hist.extend(p_data["qc_history"])
    
    if include_pool:
        # Global AI Havuzunu da ekle (Yeni santraller için kritik)
        pool_data = havuz_yukle()
        # Pool verilerinde predicted_mpa eksik olabilir, 
        # ancak classify_plant zaten predicted_mpa varsa diff hesaplar.
        global_hist.extend(pool_data)
        
    return global_hist

def btn_optimize_click():
    st.info("Optimizasyon motoru başlatılıyor (TS 802)...")
    # Bu fonksiyon state update yapar

# --- SIDEBAR & PROJE YÖNETİMİ ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/tr/b/bb/KGM_Logo.png", width=100)
    st.title("PROJE DETAYI")
    
    # Kullanıcı Bilgisi ve Çıkış
    st.caption(f"👤 {user_info.get('full_name', st.session_state['username'])} ({user_info.get('role', 'User')})")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()
    
    if st.button("🔄 Santral Değiştir", use_container_width=True):
        if 'active_plant' in st.session_state:
            del st.session_state['active_plant']
            st.rerun()
        
    st.markdown("---")
    
    # API Anahtarları
    with st.expander("🔑 API Ayarları"):
        google_key = st.text_input("Google API Key", type="password")
        deepseek_key = st.text_input("DeepSeek Key", type="password")
        selected_provider = st.selectbox("AI Sağlayıcı", ["Google Gemini", "DeepSeek (Beta)"])

    # Proje Seçimi ve Yükleme Mantığı
    def project_load_callback():
        # Session state'den güncel seçili projeyi al ve yükle
        if 'proj_selector' in st.session_state:
            from logic.state_manager import SessionStateInitializer
            active_p = st.session_state.get('active_plant', 'merkez')
            SessionStateInitializer.load_project_data(st.session_state.proj_selector, plant_id=active_p)

    active_p = st.session_state.get('active_plant', 'merkez')
    all_data = veriyi_yukle(plant_id=active_p)
    project_list = list(all_data.keys())
    if not project_list: project_list = ["Yeni Proje"]
    
    proje = st.selectbox(
        "📁 Proje Seçiniz", 
        project_list, 
        key="proj_selector", 
        on_change=project_load_callback
    )
    
    # --- KRİTİK FİKS: Tek proje veya ilk yüklemede veriyi otomatik çek ---
    if 'proj_data' not in st.session_state or st.session_state.get('loaded_project_name') != proje:
        project_load_callback()
        st.session_state['loaded_project_name'] = proje
    
    # Yeni Proje Girişi ve İşlemler
    new_proj_name = st.text_input("🆕 Yeni Proje Adı")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("💾 Kaydet", help="Seçili projeyi veya yenisini kaydeder"):
            st.session_state['trigger_save'] = True
            st.session_state['save_target_name'] = new_proj_name if new_proj_name else proje
            
    with c_btn2:
        if is_admin:
            if st.button("🗑️ Sil", help="Seçili projeyi sistemden kaldırır"):
                from logic.data_manager import projesi_sil
                active_p = st.session_state.get('active_plant', 'merkez')
                if projesi_sil(proje, plant_id=active_p):
                    st.warning(f"'{proje}' silindi.")
                    st.rerun()
        else:
            st.button("🗑️ Sil", disabled=True, help="Silme yetkiniz yok")

    st.markdown("---")
    st.subheader("🏗️ Şantiye Bilgileri")
    plant_val = all_data.get(proje, {}).get("plant_name", "KGM-91 Santral")
    tesis_adi = st.text_input("Santral / Tesis Adı", value=plant_val)
    hedef_sinif = st.selectbox("Hedef Beton Sınıfı", list(CONCRETE_RULES.keys()))
    litoloji = st.selectbox("Agrega Litolojisi", [
        "Bazalt (Diyarbakır/Gaziantep)",
        "Kalker (Mardin/Şanlıurfa)",
        "Dere Malzemesi (Dicle/Fırat)",
        "Kalker (Standart)",
        "Bazalt (Standart)",
        "Granit"
    ])
    
    st.info(f"**Standart:** {CONCRETE_RULES[hedef_sinif]['min_mpa']} MPa Min.")

    # Çevresel Etki ve ASR Risk Girişleri
    st.markdown("---")
    from logic.engineering import EXPOSURE_CLASSES, ASR_LITHOLOGY_RISK
    col_dur1, col_dur2 = st.columns(2)
    with col_dur1:
        exp_class = st.selectbox("Çevresel Etki Sınıfı (TS EN 206)", list(EXPOSURE_CLASSES.keys()), index=list(EXPOSURE_CLASSES.keys()).index(st.session_state.get('exposure_class', 'XC3')), key="exposure_class")
        st.caption(f"ℹ️ {EXPOSURE_CLASSES[exp_class]['desc']}")
    with col_dur2:
        # Litolojiye göre varsayılan ASR riskini öner
        suggested_asr = ASR_LITHOLOGY_RISK.get(litoloji, "Belirtilmemiş")
        asr_stat = st.selectbox("ASR Reaktivite (Laboratuvar)", 
                                ["Düzeltme Gerekmiyor (İnert)", "Potansiyel Reaktif", "Yüksek Reaktif"], 
                                index=0 if "Düşük" in suggested_asr else 1, key="asr_status")
        st.caption(f"🔔 Litoloji Analizi: {suggested_asr}")

    st.markdown("---")
    selected_model_name = st.selectbox(
        "🤖 Gemini Modeli Seçin", 
        [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-pro-exp",
            "gemini-2.0-flash-exp", 
            "gemini-2.0-flash-lite-preview-0817",
            "gemini-1.5-pro-latest", 
            "gemini-1.5-pro-002",
            "gemini-1.5-pro-001",
            "gemini-1.5-pro", 
            "gemini-1.5-flash-latest", 
            "gemini-1.5-flash-002",
            "gemini-1.5-flash-001",
            "gemini-1.5-flash", 
            "gemini-1.5-flash-8b-latest",
            "gemini-1.5-flash-8b",
            "gemini-pro", 
            "gemini-pro-vision",
            "gemini-1.0-pro"
        ],
        index=0,
        help="API anahtarınızın desteklediği modeli seçin. 2.0 modelleri en güncel olanlardır."
    )
    
# AI Model Hazırlama
import google.generativeai as genai
if google_key:
    genai.configure(api_key=google_key)
    try:
        model = genai.GenerativeModel(selected_model_name)
    except Exception as e:
        st.sidebar.error(f"Model yüklenemedi: {selected_model_name}")
        model = None
else:
    model = None

from openai import OpenAI
deepseek_client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com") if deepseek_key else None

# Tesis Bazlı Saha Faktörü
active_p = st.session_state.get('active_plant', 'merkez')
current_site_factor = tesis_faktor_yukle(tesis_adi, plant_id=active_p)

# --- ANA PANEL ---
tab_titles = ["📊 Malzeme Kütüphanesi", "📈 Karışım Dizaynı", "📉 Şantiye QC", "📄 Raporlar & Çıktı"]
if is_super_admin:
    tab_titles.extend(["🧠 AI Eğitim Merkezi", "👥 Kullanıcı Yönetimi"])

tabs = st.tabs(tab_titles)
tab1, tab2, tab4, tab3 = tabs[0:4]
if is_super_admin:
    tab5 = tabs[4]
    tab6 = tabs[5]

with tab1:
    current_rhos, current_was, current_las, current_mbs, computed_passing, active_mats, all_ri_values = render_tab_1(elek_serisi)

with tab2:
    render_tab_2(
        proje=proje,
        tesis_adi=tesis_adi,
        hedef_sinif=hedef_sinif,
        litoloji=litoloji,
        elek_serisi=elek_serisi,
        materials=materials,
        active_mats=active_mats,
        current_rhos=current_rhos,
        current_was=current_was,
        current_las=current_las,
        current_mbs=current_mbs,
        current_site_factor=current_site_factor,
        get_global_qc_history=get_global_qc_history
    )

with tab4:
    TARGET_LIMITS = {
        "C25/30": {"max_wc": 0.60, "min_mpa": 30},
        "C30/37": {"max_wc": 0.55, "min_mpa": 37},
        "C35/45": {"max_wc": 0.50, "min_mpa": 45},
        "C40/50": {"max_wc": 0.45, "min_mpa": 50},
        "C50/60": {"max_wc": 0.40, "min_mpa": 60}
    }
    render_tab_4(proje, tesis_adi, TARGET_LIMITS, hedef_sinif, get_global_qc_history, is_admin=is_admin)

with tab3:
    render_tab_3(proje, selected_provider, TS_STANDARDS_CONTEXT)

if is_super_admin:
    with tab5:
        render_tab_5(is_admin=is_admin)
    with tab6:
        from logic.modular_tabs import render_tab_management
        render_tab_management(is_super_admin=is_super_admin)
    
    # AI Report Processing (If requested from the tab)
    if 'ai_report_prompt' in st.session_state:
        prompt = st.session_state.pop('ai_report_prompt')
        with st.spinner("AI Teknik Rapor oluşturuluyor..."):
            try:
                res_text = ""
                if selected_provider == "Google Gemini" and model:
                    res_text = model.generate_content(prompt).text
                elif selected_provider == "DeepSeek (Beta)" and deepseek_client:
                    res_text = deepseek_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}]).choices[0].message.content
                
                if res_text:
                    st.session_state['ai_report_output'] = res_text
                    st.rerun()
            except Exception as e:
                st.error(f"AI Hatası: {e}")

# Excel Rapor (Sidebar'a veya Tab 3'e taşındı ama butonu burada tutabiliriz de, 
# kullanıcı talebine göre sidebar'a ekliyorum)
with st.sidebar:
    st.markdown("---")
    if st.button("📥 EXCEL RAPOR İNDİR"):
        # Excel oluşturan fonksiyon
        def create_excel_lite():
            output = BytesIO()
            workbook = pd.ExcelWriter(output, engine='xlsxwriter')
            pd.DataFrame({"Parametre": ["Proje", "Tesis"], "Değer": [proje, tesis_adi]}).to_excel(workbook, sheet_name='Rapor')
            workbook.close()
            output.seek(0)
            return output
        st.download_button("Dosyayı İndir", create_excel_lite(), file_name=f"{proje}.xlsx")

# --- TETİKLENEN KAYDETME İŞLEMİ (NameError Önleyici) ---
if st.session_state.get('trigger_save'):
    p_to_save = st.session_state.pop('save_target_name', proje)
    active_p = st.session_state.get('active_plant', 'merkez')
    
    # Mevcut veriyi kontrol et (QC geçmişini korumak için)
    existing_all_data = veriyi_yukle(plant_id=active_p)
    
    # Eğer "Farklı Kaydet" yapılıyorsa (isim değiştiyse), 
    # eski projenin QC verilerini yeni projeye miras bırakalım.
    existing_qc = []
    if proje in existing_all_data:
        existing_qc = existing_all_data[proje].get("qc_history", [])
    elif p_to_save in existing_all_data:
        existing_qc = existing_all_data[p_to_save].get("qc_history", [])

    # Tüm değişkenler artık render_tab_1 ve render_tab_2'den sonra tanımlı
    d = {
        "rhos": current_rhos, "was": current_was, "ri": all_ri_values, 
        "las": [st.session_state.get(f"la_{i}", 0.0) for i in range(4)],
        "mbs": [st.session_state.get(f"mb_{i}", 0.0) for i in range(4)],
        "m1s": [st.session_state.get(f"m1_{i}", 0.0) for i in range(4)],
        "p": [st.session_state.get('p1', 25), st.session_state.get('p2', 25), st.session_state.get('p3', 25), st.session_state.get('p4', 25)],
        "cim": st.session_state.get('cimento_val', 350), 
        "su": st.session_state.get('su_val', 180), 
        "kat": st.session_state.get('katki_val', 1.0), 
        "elek": elek_serisi, 
        "active": active_mats,
        "ucucu": st.session_state.get('ucucu_kul', 0), 
        "hava": st.session_state.get('hava_yuzde', 1.5), 
        "plant_name": tesis_adi,
        "qc_history": existing_qc, # QC Verilerini Pakete Ekle
        "exp_class": st.session_state.get('exposure_class', 'XC3'),
        "asr_stat": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor (İnert)')
    }
    veriyi_kaydet(p_to_save, d, plant_id=active_p)
    st.session_state['trigger_save'] = False
    st.success(f"✔️ '{p_to_save}' başarıyla kaydedildi.")
    st.rerun()
