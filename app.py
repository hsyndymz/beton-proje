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
from logic.state_manager import init_session_state, SessionStateInitializer
from logic.modular_tabs import render_tab_1, render_tab_2, render_tab_3, render_tab_4, render_tab_5, render_tab_management, render_tab_ocak
from logic.auth_manager import check_login, register_user
from logic.ocak_manager import ocaklari_yukle

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Beton Tasarım Programı", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# --- LOGIN SİSTEMİ ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    # Giriş ekranında sidebar'ı gizle
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image("assets/logo.jpg", width=160)
        st.markdown('<h1 style="color: #333; border-bottom: none; display: flex; align-items: center; justify-content: center; gap: 10px;">🏗️ BETON TASARIM PROGRAMI</h1>', unsafe_allow_html=True)
        
        l_tab, r_tab = st.tabs(["🔑 Giriş Yap", "📝 Kaydol (Üyelik Başvurusu)"])
        
        with l_tab:
            user_input = st.text_input("Kullanıcı Adı", key="login_user")
            pass_input = st.text_input("Şifre", type="password", key="login_pass")
            if st.button("Sisteme Gir", use_container_width=True):
                login_res = check_login(user_input, pass_input)
                if isinstance(login_res, dict) and "error" in login_res:
                    st.warning(f"⏳ {login_res['error']}")
                elif login_res:
                    # Temizlik: Yeni kullanıcı için tertemiz bir sayfa
                    st.session_state.clear()
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
        
    # Sağ Alt Bilgi (Footer)
    st.markdown("""
        <div class="footer-info">
            <b>Hazırlayan&Tasarlayan : Hüseyin DUYMAZ</b><br>
            <b>Bilgi&İrtibat için : 05345435940</b>
        </div>
    """, unsafe_allow_html=True)
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
            # KRİTİK: Santral girişi anında tüm eski kullanıcı verilerini SİL ve Varsayılanları ZORLA yükle
            SessionStateInitializer.clear_all_project_state(exclude_selection=False)
            init_session_state(force=True)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Giriş yapılmış ve santral seçilmişse devam et...
user_info = st.session_state['user_info']
is_admin = user_info.get('role') in ["Admin", "SuperAdmin"]
is_super_admin = user_info.get('role') == "SuperAdmin"

# CSS: Endüstriyel İsviçre Tasarım Sistemi (UI/UX Pro Max)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Background */
    html, body, .stApp {
        font-family: 'Fira Sans', sans-serif;
        color: #334155;
    }
    
    /* Target text elements specifically, excluding icons */
    .stMarkdown p, .stText, label, div[data-testid="stMarkdownContainer"] p {
        font-family: 'Fira Sans', sans-serif !important;
    }

    /* Reset font for any potential icon containers */
    [data-testid*="Icon"], .stIcon {
        font-family: inherit !important;
    }
    
    .main { 
        background-color: #F8FAFC; 
    }

    h1, h2, h3, .stHeader {
        font-family: 'Fira Sans', sans-serif;
        font-weight: 700 !important;
        color: #1e293b !important;
        letter-spacing: -0.02em;
    }

    code, pre, .stMarkdown code {
        font-family: 'Fira Code', monospace !important;
    }

    /* Professional Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important; /* Slate-900 */
        border-right: 1px solid #1e293b;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        color: #94a3b8 !important;
        border: 1px solid #334155 !important;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-color: #64748b !important;
    }

    /* Dashboard Metric Cards */
    div.stMetric {
        background: white;
        padding: 20px !important;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease;
    }
    
    div.stMetric:hover {
        transform: translateY(-2px);
    }

    div.stMetric [data-testid="stMetricValue"] {
        font-family: 'Fira Code', monospace;
        font-size: 2rem !important;
        font-weight: 600;
        color: #0f172a;
    }

    /* Global Primary Buttons (Safety Orange) */
    div.stButton > button:first-child {
        background-color: #f97316 !important; /* Orange-500 */
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div.stButton > button:first-child:hover {
        background-color: #ea580c !important; /* Orange-600 */
        box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.3) !important;
    }

    /* Tabs Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre;
        background-color: #f1f5f9;
        border-radius: 4px 4px 0 0;
        color: #64748b;
        font-weight: 500;
        border: 1px solid #e2e8f0;
        border-bottom: none;
    }

    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #0f172a !important;
        border-top: 3px solid #f97316 !important;
    }

    /* Inputs & Selectors */
    .stTextInput input, .stSelectbox [data-baseweb="select"] {
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Footer Info */
    .footer-info {
        position: fixed;
        bottom: 20px;
        right: 20px;
        text-align: right;
        font-family: 'Fira Code', monospace;
        font-size: 11px;
        line-height: 1.4;
        color: #94a3b8;
        background: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL VERİLER ---
elek_serisi = [45.0, 40.0, 31.5, 22.4, 16.0, 11.2, 8.0, 4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.063]
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

# --- PROJE VE DENEME SEÇİMİ (TOP LEVEL) ---
active_p = st.session_state.get('active_plant', 'merkez')

# GÜVENLİ YÖNLENDİRME
if st.session_state.get('pending_proj_redirect'):
    p_req = st.session_state.pop('pending_proj_redirect')
    st.session_state[f"proj_selector_{active_p}"] = p_req
    if st.session_state.get('pending_trial_redirect'):
        t_req = st.session_state.pop('pending_trial_redirect')
        st.session_state[f"trial_selector_{active_p}_{p_req}"] = t_req

all_data = veriyi_yukle(plant_id=active_p)
project_list = sorted(list(all_data.keys()))
if not project_list: project_list = ["Yeni Proje"]

# 1. Proje Seçim Kontrolü
sel_key = f"proj_selector_{active_p}"
if sel_key not in st.session_state or st.session_state[sel_key] not in project_list:
    st.session_state[sel_key] = project_list[0]
current_sel = st.session_state[sel_key]

# 2. Deneme Seçim Kontrolü
p_data = all_data.get(current_sel, {})
trial_list = ["Ana Reçete"]
if isinstance(p_data, dict) and "trials" in p_data:
    trial_list = sorted(list(p_data["trials"].keys()))

trial_sel_key = f"trial_selector_{active_p}_{current_sel}"
if trial_sel_key not in st.session_state or st.session_state[trial_sel_key] not in trial_list:
    st.session_state[trial_sel_key] = trial_list[0]
current_trial = st.session_state[trial_sel_key]

# 3. Yükleme Tetikleyici
current_id = f"{active_p}_{current_sel}_{current_trial}"
if st.session_state.get('loaded_trial_id') != current_id:
    SessionStateInitializer.load_project_data(project_name=current_sel, trial_name=current_trial, plant_id=active_p)
    st.session_state['loaded_trial_id'] = current_id
    st.rerun()

# --- SIDEBAR & PROJE YÖNETİMİ ---
with st.sidebar:
    st.image("assets/logo.jpg", width=120)
    st.title("PROJE DETAYI")
    
    # Kullanıcı Bilgisi ve Çıkış
    st.caption(f"👤 {user_info.get('full_name', st.session_state['username'])} ({user_info.get('role', 'User')})")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    if st.button("🔄 Santral Değiştir", use_container_width=True):
        if 'active_plant' in st.session_state:
            del st.session_state['active_plant']
            from logic.state_manager import SessionStateInitializer
            SessionStateInitializer.clear_all_project_state()
            st.rerun()
        
    st.markdown("---")
    
    # API Ayarları
    with st.expander("🔑 API Ayarları"):
        google_key = st.text_input("Google API Key", type="password")
        deepseek_key = st.text_input("DeepSeek Key", type="password")
        selected_provider = st.selectbox("AI Sağlayıcı", ["Google Gemini", "DeepSeek (Beta)"])

    c_sel1, c_sel2 = st.columns([4, 1])
    
    def on_selection_change():
        # Seçim değiştiğinde tetikleyiciyi sıfırla ki yeni veri yüklensin
        if 'loaded_trial_id' in st.session_state:
            del st.session_state['loaded_trial_id']

    with c_sel1:
        # Stabilized selection widgets
        try:
            p_idx = project_list.index(st.session_state[sel_key])
        except:
            p_idx = 0
            
        proje = st.selectbox(
            "📁 Proje Seçiniz", 
            project_list, 
            index=p_idx,
            key=f"proj_sb_{active_p}",
            help="Çalışmak istediğiniz projeyi seçin."
        )
        if proje != st.session_state[sel_key]:
            st.session_state[sel_key] = proje
            if 'loaded_trial_id' in st.session_state: del st.session_state['loaded_trial_id']
            st.rerun()

        # Deneme Seçimi
        try:
            t_idx = trial_list.index(st.session_state[trial_sel_key])
        except:
            t_idx = 0
            
        deneme = st.selectbox(
            "🧪 Deneme/Versiyon", 
            trial_list, 
            index=t_idx,
            key=f"trial_sb_{active_p}_{proje}",
            help="Versiyon seçin."
        )
        if deneme != st.session_state[trial_sel_key]:
            st.session_state[trial_sel_key] = deneme
            if 'loaded_trial_id' in st.session_state: del st.session_state['loaded_trial_id']
            st.rerun()
    with c_sel2:
        if st.button("🔄", help="Projeleri Yenile"):
            st.rerun()
    
    # Yeni Deneme Girişi
    new_trial_name = st.text_input("🧬 Yeni Deneme Adı (Opsiyonel)")
    new_proj_name = st.text_input("🆕 Yeni Proje Adı (Opsiyonel)")
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("💾 Kaydet", help="Değişiklikleri mevcut veya yeni denemeye kaydeder"):
            st.session_state['trigger_save'] = True
            st.session_state['save_target_name'] = new_proj_name if new_proj_name else proje
            st.session_state['save_target_trial'] = new_trial_name if new_trial_name else deneme
            
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
    # Ocak ve Litoloji İlişkisi
    ocaklar = ocaklari_yukle()
    o_list = ["Seçiniz..."] + list(ocaklar.keys())
    selected_ocak_id = st.selectbox("🏔️ Ocak Seçimi (Opsiyonel)", options=o_list, 
                                     format_func=lambda x: ocaklar[x].get("name", x) if x != "Seçiniz..." else x)
    
    suggested_litho_idx = 0
    if selected_ocak_id != "Seçiniz...":
        o_data = ocaklar[selected_ocak_id]
        o_litho = o_data.get("lithology", "Bazalt")
        # Sidebar'daki litoloji listesiyle eşleştir
        litho_options = [
            "Bazalt (Diyarbakır/Gaziantep)",
            "Kalker (Mardin/Şanlıurfa)",
            "Dere Malzemesi (Dicle/Fırat)",
            "Kalker (Standart)",
            "Bazalt (Standart)",
            "Granit"
        ]
        for idx, opt in enumerate(litho_options):
            if o_litho in opt:
                suggested_litho_idx = idx
                break

    litoloji = st.selectbox("Agrega Litolojisi", [
        "Bazalt (Diyarbakır/Gaziantep)",
        "Kalker (Mardin/Şanlıurfa)",
        "Dere Malzemesi (Dicle/Fırat)",
        "Kalker (Standart)",
        "Bazalt (Standart)",
        "Granit"
    ], index=suggested_litho_idx)
    
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
tab_titles = ["🔍 Malzeme", "⚖️ Karışım", "🔬 Karşılaştırma", "📜 Şartname", "✅ Kontrol"]

if is_super_admin:
    tab_titles.extend(["🏢 Kurumsal", "⛰️ Ocak", "🤖 Eğitim", "👥 Kullanıcılar"])

tabs = st.tabs(tab_titles)
tab1, tab2, tab_comp, tab3, tab4 = tabs[0:5]

# Dinamik Tab Ataması
next_idx = 5
tab_corp = None
tab_ocak = None
tab_ai_train = None
tab_user_mgmt = None

if is_super_admin:
    tab_corp = tabs[next_idx]
    tab_ocak = tabs[next_idx + 1]
    tab_ai_train = tabs[next_idx + 2]
    tab_user_mgmt = tabs[next_idx + 3]

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

with tab_comp:
    st.subheader("🔬 Deneme Karşılaştırma ve Elek Analizi")
    p_data_comp = all_data.get(proje, {})
    if isinstance(p_data_comp, dict) and "trials" in p_data_comp:
        trials = p_data_comp["trials"]
        
        # 1. Grafiksel Karşılaştırma (Elek Eğrileri)
        st.write("📈 **Elek Analizi Eğrileri (TS 802)**")
        fig_comp = go.Figure()
        
        # Standart Limitleri Çiz
        d_max = st.session_state.get('dmax_val', 31.5)
        c_type = st.session_state.get('curve_type_val', 'B (İdeal)')
        alt_std, ust_std = get_std_limits(d_max, c_type, elek_serisi)
        fig_comp.add_trace(go.Scatter(x=elek_serisi, y=alt_std, name="Alt Limit", line=dict(color='red', dash='dash')))
        fig_comp.add_trace(go.Scatter(x=elek_serisi, y=ust_std, name="Üst Limit", line=dict(color='red', dash='dash')))

        all_passing_data = {}
        all_retained_data = {}
        
        for t_name, t_val in trials.items():
            # Her deneme için karışım gradasyonunu hesapla
            t_active = t_val.get("active", [True, True, True, True])
            t_ratios = t_val.get("p", [25, 25, 25, 25])
            t_ri = t_val.get("ri", {}) # Bu aslında 'kalan' gramaj verisidir
            t_m1s = t_val.get("m1s", [4000.0, 4000.0, 2000.0, 2000.0])
            t_elek = t_val.get("elek", elek_serisi) # Kaydedilmiş elek serisini kullan (Kritik!)
            
            # Her malzemenin kendi gradasyonunu (geçen %) hesapla (Kalandan Geçene Çevir)
            trial_total_passing = np.zeros(len(t_elek))
            
            for i in range(4):
                if t_active[i]:
                    # i index veya mat_name olarak saklanmış olabilir
                    mat_weights = t_ri.get(str(i)) or t_ri.get(materials[i], [0.0]*len(t_elek))
                    m1_val = t_m1s[i] if i < len(t_m1s) else 2000.0
                    
                    # Eğer kaydedilen mat_weights uzunluğu t_elek ile uyumsuzsa düzeltebilmeliyiz
                    if len(mat_weights) != len(t_elek):
                        if len(mat_weights) < len(t_elek):
                            mat_weights = list(mat_weights) + [0.0] * (len(t_elek) - len(mat_weights))
                        else:
                            mat_weights = mat_weights[:len(t_elek)]

                    # Kalandan Geçene Çevir
                    mat_passing = calculate_passing(m1_val, mat_weights)
                    
                    # Karışım gradasyonuna (oranıyla) ekle
                    trial_total_passing += np.array(mat_passing) * (t_ratios[i] / 100.0)
            
            all_passing_data[t_name] = {"passing": trial_total_passing, "elek": t_elek}
            all_retained_data[t_name] = t_ri
            fig_comp.add_trace(go.Scatter(x=t_elek, y=trial_total_passing, name=t_name, mode='lines+markers'))

        fig_comp.update_layout(xaxis_type="log", xaxis_title="Elek Göz Açıklığı (mm)", yaxis_title="Toplam Karışım Geçen %", height=500)
        st.plotly_chart(fig_comp, use_container_width=True)

        # 2. Tablo Karşılaştırma
        with st.expander("📊 Detaylı Sayısal Karşılaştırma", expanded=True):
            # Geçen % Tablosu
            st.write("📈 **Karışım Geçen Yüzdeleri (%)**")
            elek_rows = []
            for i, e_size in enumerate(elek_serisi):
                row = {"Elek (mm)": e_size}
                for t_name, t_info in all_passing_data.items():
                    t_passing = t_info["passing"]
                    t_elek = t_info["elek"]
                    
                    # Bu denemede bu elek boyutu var mı bul
                    try:
                        idx = list(t_elek).index(e_size)
                        val = t_passing[idx]
                        row[t_name] = f"%{val:.1f}"
                    except ValueError:
                        row[t_name] = "-" # Elek bu denemede yoksa
                elek_rows.append(row)
            st.dataframe(pd.DataFrame(elek_rows), use_container_width=True, hide_index=True)
            
            # Reçete tablosu
            st.divider()
            st.write("🧱 **Reçete ve Malzeme Oranları**")
            comp_rows = []
            for t_name, t_val in trials.items():
                row = {
                    "Deneme Adı": t_name,
                    "Çimento": t_val.get("cim", 0),
                    "Su": t_val.get("su", 0),
                    "W/C": round(t_val.get("su",0)/t_val.get("cim",1), 2) if t_val.get("cim") else 0,
                    "Katkı": t_val.get("kat", 0),
                    "Oranlar (%)": f"{t_val.get('p',[0,0,0,0])}"
                }
                comp_rows.append(row)
            st.table(pd.DataFrame(comp_rows))
    else:
        st.info("Bu proje için henüz birden fazla deneme kaydedilmemiş.")

with tab3:
    render_tab_3(proje, selected_provider, TS_STANDARDS_CONTEXT)

with tab4:
    TARGET_LIMITS = {
        "C25/30": {"max_wc": 0.60, "min_mpa": 30},
        "C30/37": {"max_wc": 0.55, "min_mpa": 37},
        "C35/45": {"max_wc": 0.50, "min_mpa": 45},
        "C40/50": {"max_wc": 0.45, "min_mpa": 50},
        "C50/60": {"max_wc": 0.40, "min_mpa": 60}
    }
    render_tab_4(proje, tesis_adi, TARGET_LIMITS, hedef_sinif, get_global_qc_history, is_admin=is_admin)

if tab_ocak:
    with tab_ocak:
        render_tab_ocak(is_admin=is_admin)

if is_admin and tab_corp:
    with tab_corp:
        render_tab_5(is_admin=is_admin)

if is_super_admin:
    if tab_ai_train:
        with tab_ai_train:
            st.subheader("🧠 Global AI Eğitim Merkezi")
            st.info("Bu bölümdeki veriler tüm santrallerden gelen kırım sonuçlarını içerir.")
            pool_data = havuz_yukle()
            if pool_data:
                df_pool = pd.DataFrame(pool_data)
                st.write(f"Sistemdeki Toplam Eğitim Datası: {len(df_pool)}")
                if st.button("🚀 Modeli Yeniden Eğit ve Bülten Yayınla"):
                    with st.spinner("Model optimize ediliyor ve AI Bülteni hazırlanıyor..."):
                        # 1. Eğitim
                        train_prediction_model(pool_data)
                        
                        # 2. AI Analizi ve Bülten Oluşturma
                        avg_mpa = sum([float(r.get('d28',0)) for r in pool_data]) / len(pool_data)
                        total_rec = len(pool_data)
                        
                        analysis_prompt = f"""
                        Sistemdeki tüm santrallerden gelen toplam {total_rec} adet kırım ve malzeme verisini analiz ettik.
                        Ortalama dayanım: {avg_mpa:.2f} MPa.
                        
                        KRİTİK ANALİZ TALEBİ:
                        Lütfen verilerdeki 'lithology' (Kalker, Bazalt vb.) ve 'material_chars' (Aşınma, Su Emme, MB) 
                        ilişkilerini derinlemesine incele. 
                        - Farklı litolojilerin dayanım ve su ihtiyacı üzerindeki 'karakteristik' etkilerini açıkla.
                        - Malzeme kalitesindeki (LA, MB) değişimlerin dökümlere nasıl yansıdığını yorumla.
                        - Gelecek dökümler için litoloji bazlı 'AI Düzeltme Önerileri' sun.
                        
                        Bu bülten, mühendislerin malzeme seçiminde AI'nın öğrendiği bu 'tecrübeleri' kullanmasını sağlamalıdır.
                        """
                        
                        res_text = ""
                        try:
                            if selected_provider == "Google Gemini" and model:
                                res_text = model.generate_content(analysis_prompt).text
                            elif selected_provider == "DeepSeek (Beta)" and deepseek_client:
                                res_text = deepseek_client.chat.completions.create(
                                    model="deepseek-chat", 
                                    messages=[{"role":"user","content":analysis_prompt}]
                                ).choices[0].message.content
                            
                            if res_text:
                                from logic.data_manager import shared_insight_kaydet
                                new_insight = {
                                    "author": "Merkez AI (Öğrenilmiş Bilgi)",
                                    "content": res_text,
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                shared_insight_kaydet(new_insight)
                                st.success("Model eğitildi ve AI Bülteni tüm santrallerde yayınlandı!")
                        except Exception as e:
                            st.warning(f"Model eğitildi ancak bülten oluşturulamadı: {e}")
                        
                        st.success("Yeni model başarıyla eğitildi!")
                st.dataframe(df_pool.tail(10))
            else:
                st.warning("Henüz global havuzda veri birikmemiş.")
                
    if tab_user_mgmt:
        with tab_user_mgmt:
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

# Excel Rapor Download
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

# --- TETİKLENEN KAYDETME İŞLEMİ ---
if st.session_state.get('trigger_save'):
    p_name = st.session_state.pop('save_target_name', proje)
    t_name = st.session_state.pop('save_target_trial', "Ana Reçete")
    active_p = st.session_state.get('active_plant', 'merkez')
    
    # Mevcut veriyi oku
    existing_all = veriyi_yukle(plant_id=active_p)
    proj_obj = existing_all.get(p_name, {"trials": {}, "qc_history": [], "active_trial": t_name})
    
    # 1. Migration: Eğer proje objesi eski formattaysa (trials yoksa)
    if "trials" not in proj_obj:
        old_data = proj_obj.copy()
        proj_obj = {
            "trials": {"Ana Reçete": old_data},
            "qc_history": old_data.get("qc_history", []),
            "active_trial": "Ana Reçete"
        }
        if "qc_history" in proj_obj["trials"]["Ana Reçete"]: 
            del proj_obj["trials"]["Ana Reçete"]["qc_history"]

    # 2. Yeni Deneme Verisini Hazırla
    trial_data = {
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
        "exp_class": st.session_state.get('exposure_class', 'XC3'),
        "asr_stat": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor (İnert)')
    }
    
    # 3. Güncelle ve Kaydet
    proj_obj["trials"][t_name] = trial_data
    proj_obj["active_trial"] = t_name
    veriyi_kaydet(p_name, proj_obj, plant_id=active_p)
    
    # 4. State Sync (Güvenli Yöntem: Bir sonraki run'da yakalanacak)
    st.session_state['pending_proj_redirect'] = p_name
    st.session_state['pending_trial_redirect'] = t_name
    st.session_state['trigger_save'] = False
    st.success(f"✔️ '{p_name} -> {t_name}' başarıyla kaydedildi.")
    st.rerun()
