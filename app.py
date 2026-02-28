import streamlit as st
import datetime
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
from logic.report_generator import generate_kgm_raporu
from logic.state_manager import init_session_state, SessionStateInitializer
from logic.auth_manager import check_login, register_user, check_session_timeout
from logic.ocak_manager import ocaklari_yukle
from logic.input_validator import sanitize_input
from config import Config

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Beton Tasarım Programı", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# --- GLOBAL VAR INITIALIZATION (Safety for White Screen) ---
tesis_adi = st.session_state.get('tesis_adi', 'KGM-91 Santral')
hedef_sinif = st.session_state.get('hedef_sinif', 'C30/37')
litoloji = st.session_state.get('litoloji', 'Bazalt (Standart)')
# 0. API KEY MANAGEMENT (Prioritize Session State -> Secrets -> Env)
def get_safe_api_key(key_name):
    # 1. Eğer kullanıcı bu seansta bir anahtar girdiyse onu kullan (Sidebar Key)
    sidebar_key = f"input_{key_name}"
    if sidebar_key in st.session_state and st.session_state[sidebar_key]:
        return st.session_state[sidebar_key]
    
    # Session state widget key fallback
    widget_key = f"{key_name.lower()}_field"
    if widget_key in st.session_state and st.session_state[widget_key]:
        return st.session_state[widget_key]

    # 2. Reçete/Secrets dosyasından bak
    try:
        val = st.secrets.get(key_name)
        if val: return val
    except:
        pass
    
    # 3. Environment variable'dan bak
    return os.environ.get(key_name, "")

google_key = get_safe_api_key("GOOGLE_API_KEY")
deepseek_key = get_safe_api_key("DEEPSEEK_API_KEY")
groq_key = get_safe_api_key("GROQ_API_KEY")
local_api_base = st.session_state.get('local_api_base', 'http://localhost:11434')
local_model_name = st.session_state.get('local_model_name', 'llama3')
selected_model_name = "gemini-2.5-flash"
# 1. Session Timeout Kontrolü
if st.session_state.get('authenticated'):
    last_act = st.session_state.get('last_activity')
    if check_session_timeout(last_act):
        st.session_state.clear()
        st.warning("⚠️ Oturumunuz zaman aşımına uğradı. Lütfen tekrar giriş yapın.")
        st.stop() # Rerun yerine stop edelim, kullanıcı giriş ekranını görsün
    else:
        # Aktivite zamanını güncelle
        st.session_state['last_activity'] = datetime.datetime.now()

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
                # Girdi temizliği
                safe_user = sanitize_input(user_input)
                
                login_res = check_login(safe_user, pass_input)
                if isinstance(login_res, dict) and "error" in login_res:
                    st.warning(f"⏳ {login_res['error']}")
                elif login_res:
                    # Temizlik: Yeni kullanıcı için tertemiz bir sayfa
                    st.session_state.clear()
                    st.session_state['authenticated'] = True
                    st.session_state['user_info'] = login_res
                    st.session_state['username'] = safe_user
                    st.session_state['last_activity'] = datetime.datetime.now()
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
                    # Girdi temizliği
                    safe_reg_user = sanitize_input(reg_user)
                    safe_reg_name = sanitize_input(reg_name)
                    
                    success, msg = register_user(safe_reg_user, reg_pass, safe_reg_name)
                    if success:
                        st.success("✅ Başvurunuz başarıyla alındı! SuperAdmin onayı sonrası giriş yapabilirsiniz.")
                        st.info("💡 Genellikle 24 saat içinde onaylanır.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sağ Alt Bilgi (Footer) - SADECE Giriş Ekranında
        st.markdown("""
            <div class="footer-info">
                <b>Hazırlayan&Tasarlayan : Hüseyin DUYMAZ</b><br>
                <b>Bilgi&İrtibat için    : 05345435940</b>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR NOTIFICATION ---
if 'transferred_recipe' in st.session_state:
    tr_rec_sb = st.session_state['transferred_recipe']
    st.sidebar.markdown("---")
    st.sidebar.info(f"📥 **Aktarım Bekliyor**\n\n**{tr_rec_sb.get('name')}**\n\nDizayn sekmesine gidip uygulayın.")
    
# --- SANTRAL SEÇİMİ (Multi-Plant) ---
if 'active_plant' not in st.session_state:
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    # Safety Check: If authenticated but user_info missing (weird state), reset
    if 'user_info' not in st.session_state:
        st.session_state['authenticated'] = False
        st.rerun()
        
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
    /* Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

    .stApp { background-color: #F8FAFC; }

    /* Sadece metin sınıflarına font veriyoruz. stApp'e global vermek ikonları bozuyor. */
    h1, h2, h3, button, label, .stMarkdown p, .stTabs [data-baseweb="tab"] {
        font-family: 'Fira Sans', sans-serif !important;
    }

    /* Teknik veriler için mono font */
    [data-testid="stMetricValue"], code, pre {
        font-family: 'Fira Code', monospace !important;
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

# --- GLOBAL AYARLAR (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Proje Ayarları")
    
    # Standart Seçimi (Yeni Özellik)
    st.subheader("1. Denetim Standardı")
    standard_mode = st.radio(
        "Hesaplama Modu:",
        options=["KTŞ 2023 (Yol/Köprü)", "TS EN 206 (Bina/Genel)"],
        index=0,
        help="KTŞ 2023: Yol ve sanat yapıları için katı limitler (S/Ç 0.45, Min 340kg).\nTS EN 206: Genel yapılar için esnek maruziyet limitleri."
    )
    st.session_state['standard_mode'] = "KTS" if "KTŞ" in standard_mode else "TS_EN_206"
    
    st.divider()

# --- GLOBAL VERİLER ---
# Elek Serileri (TS 802 / Excel Standart - Büyükten Küçüğe)
from logic.engineering import SIEVE_SETS, CONCRETE_RULES
hedef_sinif = st.session_state.get('hedef_sinif', 'C30/37')
dmax_val = st.session_state.get('dmax_val', 31.5)
elek_serisi = SIEVE_SETS.get(dmax_val, SIEVE_SETS[31.5])
materials = ["Kaba Elek (19-25)(15-25)", "Orta Kaba (7-19)(5-15)", "İnce No:1 (0-7)(0-5)", "İnce No:2 (0-5)(0-7)"]

# CONCRETE_RULES engineering.py'dan import edildi.

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
        input_google = st.text_input("Google API Key", value=google_key, type="password", key="google_api_key_field")
        input_deepseek = st.text_input("DeepSeek Key", value=deepseek_key, type="password", key="deepseek_api_key_field")
        input_groq = st.text_input("Groq API Key", value=groq_key, type="password", key="groq_api_key_field")
        
        # Güncelleme: Session state'e manuel ata (bazı durumlarda widget bazen gecikebilir)
        st.session_state["input_GOOGLE_API_KEY"] = input_google
        st.session_state["input_DEEPSEEK_API_KEY"] = input_deepseek
        st.session_state["input_GROQ_API_KEY"] = input_groq
        
        selected_provider = st.selectbox("AI Sağlayıcı", ["Google Gemini", "DeepSeek (Beta)", "Groq (Llama-3.3)", "Yerel (Ollama / LM Studio)"])
        
        if selected_provider == "Yerel (Ollama / LM Studio)":
            st.session_state['local_api_base'] = st.text_input(
                "Yerel veya Uzak API Adresi (Ngrok/Cloudflare)", 
                value=local_api_base, 
                help="Evdeyseniz: http://localhost:11434 | Uzaktaysanız: https://senin-adın.ngrok-free.app", 
                key="local_api_base_input"
            )
            
            # Model Keşfi (Drop-down)
            from logic.local_ai_helper import get_local_models
            available_models = get_local_models(st.session_state['local_api_base'])
            
            if available_models:
                # Kullanıcının mevcut seçimini (veya default) kontrol et
                current_model = st.session_state.get('local_model_name', 'llama3')
                # Eğer mevcut model listede yoksa ilkini seç
                try:
                    m_idx = available_models.index(current_model)
                except ValueError:
                    m_idx = 0
                
                st.session_state['local_model_name'] = st.selectbox(
                    "Mevcut Modeller (Ollama)", 
                    available_models, 
                    index=m_idx,
                    help="Bilgisayarınızda yüklü olan modeller listelenir."
                )
                if st.button("🔄 Listeyi Yenile"):
                    st.rerun()
            else:
                st.session_state['local_model_name'] = st.text_input("Model Adı (Manuel)", value=local_model_name, help="Otomatik liste alınamadı. Manuel girin (Örn: llama3)")
                st.warning("⚠️ Yerel API'ye bağlanılamadı. Model listesi alınamadı.")

        if st.button("💾 Anahtarları Kaydet", use_container_width=True):
            st.success("API anahtarları bu oturum için güncellendi.")
            st.rerun()
            
        if google_key:
            st.caption("✅ Gemini Motoru Hazır")
        else:
            st.caption("🚨 Gemini için API Key Gerekli")

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
        # Sadece seçim değiştiğinde state güncelle, rerun yapma (Streamlit zaten yapar)
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
            # Rerun gerekli çünkü dosya sisteminden yeni veri okuyacak
            santralleri_yukle.clear()
            veriyi_yukle.clear()
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
                                     format_func=lambda x: (ocaklar[x].get("name", x) if isinstance(ocaklar[x], dict) else x) if x != "Seçiniz..." else x)
    
    suggested_litho_idx = 0
    if selected_ocak_id != "Seçiniz...":
        o_data = ocaklar[selected_ocak_id]
        if isinstance(o_data, dict):
            o_litho = o_data.get("lithology", "Bazalt")
        else:
            # Handle malformed data
            o_litho = "Bazalt" # Default fallback
        # Sidebar'daki litoloji listesiyle eşleştir
        litho_options = [
            "Bazalt (Diyarbakır/Gaziantep)",
            "Kalker (Mardin/Şanlıurfa)",
            "Dere Malzemesi (Dicle/Fırat/vb.)",
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
        "Dere Malzemesi (Dicle/Fırat/vb.)",
        "Kalker (Standart)",
        "Bazalt (Standart)",
        "Granit"
    ], index=suggested_litho_idx)

    # Otomatik Fiziksel Veri Aktarımı (Yoğunluk & Su Emme)
    if selected_ocak_id != "Seçiniz...":
        if st.session_state.get('last_ocak_id') != selected_ocak_id:
            st.session_state['last_ocak_id'] = selected_ocak_id
            o_data = ocaklar[selected_ocak_id]
            o_rhos = o_data.get("rhos", [])
            o_was = o_data.get("was", [])
            if o_rhos and len(o_rhos) == 4:
                for i in range(4): st.session_state[f"rho_{i}"] = float(o_rhos[i])
            if o_was and len(o_was) == 4:
                for i in range(4): st.session_state[f"wa_{i}"] = float(o_was[i])
            st.toast(f"✅ {o_data.get('name')} verileri (Yoğunluk/Su Emme) aktarıldı.")
    
    st.info(f"**Standart:** {CONCRETE_RULES[hedef_sinif]['min_mpa']} MPa Min.")

    # Çevresel Etki ve ASR Risk Girişleri
    st.markdown("---")
    from logic.engineering import EXPOSURE_CLASSES, ASR_LITHOLOGY_RISK
    col_dur1, col_dur2 = st.columns(2)
    with col_dur1:
        if 'exposure_class' not in st.session_state:
            st.session_state['exposure_class'] = 'XC3'
        exp_class = st.selectbox("Çevresel Etki Sınıfı (TS EN 206)", list(EXPOSURE_CLASSES.keys()), key="exposure_class")
        st.caption(f"ℹ️ {EXPOSURE_CLASSES[exp_class]['desc']}")
    with col_dur2:
        # 1. Statik Litoloji Önerisi
        static_suggested_asr = ASR_LITHOLOGY_RISK.get(litoloji, "Belirtilmemiş")
        
        # 2. AI Tahminini Kontrol Et (Ocak bazlı)
        ai_asr_suggestion = None
        if selected_ocak_id != "Seçiniz...":
            o_data = ocaklar.get(selected_ocak_id, {})
            if isinstance(o_data, dict) and o_data.get("ai_geological_insight"):
                ai_asr_suggestion = o_data["ai_geological_insight"].get("risk_level")
        
        # Öncelik Sırası: AI Tahmini > Statik Öneri
        final_suggested_risk = ai_asr_suggestion if ai_asr_suggestion else static_suggested_asr
        
        # Selectbox Index Belirleme
        risk_levels = ["Düzeltme Gerekmiyor (İnert)", "Potansiyel Reaktif", "Yüksek Reaktif"]
        default_idx = 0
        if "Potansiyel" in str(final_suggested_risk): default_idx = 1
        elif "Yüksek" in str(final_suggested_risk): default_idx = 2
        
        asr_stat = st.selectbox("ASR Reaktivite (Laboratuvar/AI)", 
                                risk_levels, 
                                index=default_idx, key="asr_status")
        
        if ai_asr_suggestion:
            st.caption(f"✨ **AI Jeolojik Önerisi:** {ai_asr_suggestion}")
        else:
            st.caption(f"🔔 Litoloji Analizi: {static_suggested_asr}")

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
if google_key:
    import google.generativeai as genai
    genai.configure(api_key=google_key)
    try:
        model = genai.GenerativeModel(selected_model_name)
    except Exception as e:
        st.sidebar.error(f"Model yüklenemedi: {selected_model_name}")
        model = None
else:
    model = None

if deepseek_key or groq_key:
    from openai import OpenAI
    deepseek_client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com") if deepseek_key else None
    groq_client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1") if groq_key else None
else:
    deepseek_client = None
    groq_client = None

# Tesis Bazlı Saha Faktörü
active_p = st.session_state.get('active_plant', 'merkez')
try:
    current_site_factor = tesis_faktor_yukle(tesis_adi, plant_id=active_p)
except Exception as e:
    st.warning(f"Saha faktörü yüklenemedi: {e}")
    current_site_factor = 1.0

# --- ANA PANEL ---
tab_titles = ["🔍 Elek Veris", "⚖️ Dizayn Oranı", "🔬 Karşılaştırma", "📜 Rapor", "✅ Kırım ve Analiz verisi"]

if is_super_admin:
    tab_titles.append("⛰️ Ocak Bilgileri")

if is_super_admin:
    tab_titles.extend(["🏢 Santral Verileri", "🤖 Ai Eğitim", "👥 Kullanıcılar"])

tab_titles.insert(3, "🧠 Akıllı Reçete")
tab_titles.insert(5, "🧪 Karot Analizi")

# --- GLOBAL NOTIFICATION AREA ---
if 'transferred_recipe' in st.session_state:
    tr_rec = st.session_state['transferred_recipe']
    st.info(f"🚀 **Smart Mix Transferi:** '{tr_rec.get('name')}' reçetesi hafızada. **'Dizayn Oranı'** sekmesine geçerek uygulayabilirsiniz.")
# --------------------------------

tabs = st.tabs(tab_titles)

from logic.ui_helpers import render_tab_content_lazy

# Baz sekmeler (Sıralı indeksler)
tab1, tab2, tab_comp, tab_smart, tab_report, tab_karot, tab_qc = tabs[0:7]

# Dinamik Tab Ataması (Admin/SuperAdmin için sonradan eklenenler)
tab_ocak = None
tab_corp = None
tab_ai_train = None
tab_user_mgmt = None

_idx = 7
if is_super_admin:
    tab_ocak = tabs[_idx]
    _idx += 1

if is_super_admin:
    tab_corp = tabs[_idx]
    tab_ai_train = tabs[_idx+1]
    tab_user_mgmt = tabs[_idx+2]

with tab1:
    from logic.tabs.tab_grading import render_tab_grading
    current_rhos, current_was, current_las, current_mbs, current_moists, computed_passing, active_mats, all_ri_values = render_tab_grading(elek_serisi)

with tab2:
    from logic.tabs.tab_design import render_tab_design
    render_tab_content_lazy(
        "⚖️ Karışım Oranları",
        render_tab_design,
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
        current_moists=current_moists,
        current_site_factor=current_site_factor,
        get_global_qc_history=get_global_qc_history
    )

with tab_comp:
    # Karşılaştırma wrapper
    from logic.tabs.tab_compare import render_tab_compare
    render_tab_compare(all_data, proje, elek_serisi, target_class=hedef_sinif)

with tab_smart:
     from logic.tabs.tab_smart_mix import render_tab_smart_mix
     render_tab_smart_mix()

with tab_report:
    from logic.tabs.tab_reports import render_tab_reports
    render_tab_reports(proje, selected_provider, TS_STANDARDS_CONTEXT)

with tab_karot:
    from logic.tabs.tab_core_analysis import render_tab_core_analysis
    render_tab_core_analysis()

with tab_qc:
    from logic.tabs.tab_analysis import render_tab_analysis
    from logic.engineering import CONCRETE_RULES
    render_tab_analysis(
        proje=proje,
        tesis_adi=tesis_adi,
        TARGET_LIMITS=CONCRETE_RULES,
        hedef_sinif=hedef_sinif,
        get_global_qc_history=get_global_qc_history,
        is_admin=is_admin
    )

# --- ADMIN / SUPER-ADMIN TABS ---
if tab_ocak:
    with tab_ocak:
        from logic.tabs.tab_quarry_mgmt import render_quarry_tab_ai
        render_quarry_tab_ai(
            google_key=google_key, 
            groq_key=groq_key, 
            deepseek_key=deepseek_key
        )

if tab_corp:
    with tab_corp:
        from logic.tabs.tab_corp_perf import render_tab_corp_perf
        render_tab_corp_perf(is_admin=is_admin)

if tab_ai_train:
    with tab_ai_train:
        from logic.tabs.tab_learning import render_tab_learning
        render_tab_learning(
            is_admin=is_admin, 
            google_key=google_key, 
            groq_key=groq_key, 
            deepseek_key=deepseek_key
        )

if tab_user_mgmt:
    with tab_user_mgmt:
        from logic.tabs.tab_user_mgmt import render_user_mgmt_tab
        render_user_mgmt_tab(is_super_admin=is_super_admin)

# --- AI RAPOR TETİKLEYİCİ ---
if st.session_state.get('ai_report_prompt'):
    prompt = st.session_state.pop('ai_report_prompt')
    response_text = ""
    
    try:
        if selected_provider == "Google Gemini" and model:
            res = model.generate_content(prompt)
            response_text = res.text
        elif selected_provider == "Groq (Llama-3.3)" and groq_client:
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = res.choices[0].message.content
        elif selected_provider == "DeepSeek (Beta)" and deepseek_client:
            res = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = res.choices[0].message.content
        else:
            response_text = "🚨 Seçili AI sağlayıcı yapılandırılmamış veya anahtar eksik."
            
        st.session_state['ai_report_output'] = response_text
        st.rerun()
    except Exception as e:
        st.error(f"AI Raporu oluşturulurken hata oluştu: {e}")

def tesis_faktor_yukle_wrapper():
    # Helper to avoid repetitive lookups
    pass
    
# --- END OF TAB DEFINITIONS ---

if __name__ == "__main__":
    pass # Managed by streamlit run
# Logic previously here has been consolidated into the modular tab rendering block (Line 677-719).

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
        "slag": st.session_state.get('slag_val', 0),
        "hava": st.session_state.get('hava_yuzde', 1.5), 
        "plant_name": tesis_adi,
        "exp_class": st.session_state.get('exposure_class', 'XC3'),
        "asr_stat": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor (İnert)'),
        "pred_mpa": st.session_state.get('predicted_mpa_val', 0.0),
        "passing": st.session_state.get('computed_passing', {})
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
