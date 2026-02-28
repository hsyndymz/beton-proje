import streamlit as st
import pandas as pd
from logic.engineering import evaluate_core_test_ts13791

def render_tab_core_analysis():
    st.header("🧪 Karot Değerlendirme (TS EN 13791)")
    st.markdown("""
    Bu modül, şantiyeden alınan karot numunelerinin dayanım sonuçlarını **TS EN 13791** standardına göre analiz eder.
    Nem durumu ve numune sayısına göre gerekli düzeltmeleri yaparak karakteristik dayanımın uygunluğunu denetler.
    """)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("📥 Girdi Verileri")
        target_fck = st.number_input("Hedef Karakteristik Dayanım (fck)", min_value=10.0, max_value=100.0, value=30.0)
        measured_mpa = st.number_input("Karot Basınç Dayanımı (Ortalama MPa)", min_value=5.0, max_value=150.0, value=25.0)
        
        moisture = st.selectbox("Numune Nem Durumu", 
                                ["Wet", "Dry", "As-is"], 
                                format_func=lambda x: "Suda Doygun (Wet)" if x=="Wet" else "Hava Kurusu (Dry)" if x=="Dry" else "Şantiye Hali (As-is)")
        
        st.info("💡 **Düzeltme Faktörü (fR):** Suda doygun numuneler için 1.10, hava kurusu için 0.96 olarak uygulanır.")

    with col2:
        st.subheader("📊 Analiz Sonucu")
        result = evaluate_core_test_ts13791(measured_mpa, target_fck, moisture_state=moisture)
        
        # Gösterge
        status_color = "green" if result["is_compliant"] else "red"
        st.markdown(f"""
        <div style="padding: 1.5rem; border-radius: 10px; border: 2px solid {status_color}; background-color: rgba(0,0,0,0.05);">
            <h3 style="color: {status_color}; margin-top: 0;">{result['msg']}</h3>
            <p>Düzeltilmiş Karot Dayanımı: <b>{result['adjusted_mpa']} MPa</b></p>
            <p>TS EN 13791 Eşik Değeri: <b>{result['target_min']} MPa</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        if not result["is_compliant"]:
            st.warning("⚠️ **Dikkat:** Karot sonuçları hedeflenen karakteristik dayanımı (fck) doğrulamamaktadır. Yapısal bir değerlendirme veya ek numuneler gerekebilir.")
        else:
            st.success("✅ Karot sonuçları TS EN 13791 kriterlerine göre yeterli bulunmuştur.")

    # Teknik Detay Tablosu
    with st.expander("📘 Standart ve Yöntem Detayı"):
        st.write("""
        **TS EN 13791 Kriter B Uygulanmıştır:**
        - Az sayıda (3-6) numune için bireysel değer analizi baz alınmıştır.
        - **Formül:** $f_{is, min} \ge 0.85 \\times (f_{ck} - 4)$
        - Karot numunelerinin yapıdaki durumu yerinde dökülen betona göre %85 oranında temsil edici kabul edilir.
        """)
