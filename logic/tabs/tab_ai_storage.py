import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from logic.data_manager import havuz_yukle, havuz_kaydet
from logic.ai_model import train_prediction_model
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_ai_training_tab(is_admin=False):
    """🧠 Yapay Zeka Eğitim Hafızası (Global Pool) - Detaylı Sürüm"""
    st.header("🧠 Yapay Zeka Eğitim Hafızası (Global Pool)")
    st.info("Bu bölüm, yapay zekayı eğitmek için kullanılan 'evrensel tecrübe havuzudur'. Buraya eklenen veriler, sistemin tüm santrallerdeki tahmin yeteneğini doğrudan etkiler.")
    
    pool_data = havuz_yukle()
    
    # 1. DETAYLI VERİ GİRİŞ FORMU
    with st.expander("➕ Yeni Teknik Tecrübe Kaydı Ekle (Sistemli)", expanded=len(pool_data) == 0):
        with st.form("detailed_ai_form"):
            st.markdown("##### 🧱 1m³ Beton Reçete Detayları")
            c1, c2, c3 = st.columns(3)
            with c1:
                g_class = st.selectbox("Hedef Beton Sınıfı", ["C25/30", "C30/37", "C35/45", "C40/50", "C50/60", "Yol Betonu"])
                g_cem = st.number_input("Çimento (kg)", value=350, step=5)
                g_wat = st.number_input("Su (L)", value=180, step=1)
            with c2:
                g_ash = st.number_input("Uçucu Kül (kg)", value=0, step=5)
                g_chem = st.number_input("Kimyasal Katkı (kg)", value=4.0, step=0.1, format="%.2f")
                g_air = st.number_input("Hava Miktarı (%)", value=1.5, step=0.1)
            with c3:
                g_slump = st.number_input("Slump (cm)", value=18.0, step=1.0)
                g_d28 = st.number_input("28 Günlük Nihai Dayanım (MPa)", value=35.0, step=0.1)
                g_tag = st.text_input("Etiket / Not", placeholder="Örn: Yüksek Performanslı Katkı Denemesi")

            st.markdown("##### 🧪 Agrega Dağılımı ve Litoloji")
            ca1, ca2, ca3, ca4 = st.columns(4)
            p1 = ca1.number_input("No:2 %", value=25, min_value=0, max_value=100)
            p2 = ca2.number_input("No:1 %", value=25, min_value=0, max_value=100)
            p3 = ca3.number_input("K.Kum %", value=25, min_value=0, max_value=100)
            p4 = ca4.number_input("D.Kum %", value=25, min_value=0, max_value=100)
            
            if st.form_submit_button("🚀 Tecrübeyi Sisteme Kaydet"):
                # Basit doğrulama
                if (p1 + p2 + p3 + p4) != 100:
                    st.error("Agrega oranları toplamı %100 olmalıdır!")
                elif g_cem <= 0 or g_d28 <= 0:
                    st.error("Çimento ve Dayanım değerleri 0'dan büyük olmalıdır.")
                else:
                    new_entry = {
                        "id": len(pool_data) + 1,
                        "class": g_class,
                        "cement": g_cem,
                        "water": g_wat,
                        "ash": g_ash,
                        "chemical": g_chem,
                        "air": g_air,
                        "slump": g_slump,
                        "p1": p1, "p2": p2, "p3": p3, "p4": p4,
                        "d28": g_d28,
                        "tag": g_tag,
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    }
                    pool_data.append(new_entry)
                    havuz_kaydet(pool_data)
                    logger.security(f"Global havuz tecrübesi eklendi. Sınıf: {g_class}", user=st.session_state.get('username'))
                    st.success("✅ Yeni tecrübe kaydı global eğitim havuzuna başarıyla işlendi.")
                    st.rerun()

    # 2. İSTATİSTİKLER VE ANALİZLER
    if pool_data:
        df_pool = pd.DataFrame(pool_data)
        
        # Üst Metrikler (Beyin Karnesi)
        st.subheader("📊 Havuz Sağlığı ve Eğitim Karnesi")
        col_st1, col_st2, col_st3, col_st4 = st.columns(4)
        with col_st1:
            st.metric("Toplam Tecrübe", len(pool_data))
        with col_st2:
            avg_mpa = df_pool["d28"].mean()
            st.metric("Ort. Dayanım", f"{avg_mpa:.1f} MPa")
        with col_st3:
            # Model yeteneğini hesapla
            from logic.ai_model import train_prediction_model
            _, _, r2 = train_prediction_model(pool_data)
            st.metric("Tahmin Kesinliği (R²)", f"%{r2*100:.1f}")
        with col_st4:
            st.metric("Sınıf Çeşitliliği", df_pool["class"].nunique() if "class" in df_pool.columns else "-")

        # Görsel Analiz (Dağılım)
        st.markdown("---")
        c_vis1, c_vis2 = st.columns(2)
        with c_vis1:
            # Su/Çimento vs Dayanım İlişkisi
            df_pool['wc'] = df_pool['water'] / df_pool['cement']
            fig_wc = px.scatter(df_pool, x="wc", y="d28", color="class", size="cement",
                                title="W/C Oranı vs Dayanım Korelasyonu",
                                labels={"wc": "Su/Çimento Oranı", "d28": "Dayanım (MPa)"},
                                template="plotly_white")
            st.plotly_chart(fig_wc, use_container_width=True)
            
        with c_vis2:
            # Sınıf Dağılımı
            fig_class = px.histogram(df_pool, x="class", title="Tecrübe Sınıf Dağılımı", 
                                     color="class", template="plotly_white")
            st.plotly_chart(fig_class, use_container_width=True)

        # Veri Listesi
        st.subheader("📋 Havuzdaki Tüm Tecrübeler")
        st.dataframe(df_pool, use_container_width=True, hide_index=True)
        
        # Global Havuz temizleme sadece Admin yetkisindedir
        if is_admin:
            with st.expander("⚠️ Tehlikeli Alan (Havuz Yönetimi)"):
                st.warning("Buradaki verilerin silinmesi yapay zeka hafızasının bir kısmını veya tamamını yok eder.")
                if st.checkbox("Havuza sıfırla (Geri Dönüşü Yoktur!)"):
                    if st.button("🗑️ TÜM HAVUZU SİL"):
                         havuz_kaydet([])
                         logger.warning("Global AI havuzu tamamen silindi!", user=st.session_state.get('username'))
                         st.success("Havuz temizlendi.")
                         st.rerun()
        else:
            st.info("💡 Global hafıza yönetimi (silme/düzenleme) sadece Yöneticilere açıktır.")
    else:
        st.warning("Eğitim havuzu şu an boş. Sistematik veriler ekleyerek AI'yı eğitmeye başlayın.")
