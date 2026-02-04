import streamlit as st
import pandas as pd
import numpy as np
from logic.engineering import (
    calculate_theoretical_mpa, evaluate_mix_compliance, 
    classify_plant, optimize_mix
)
from logic.ai_model import predict_strength_ai, generate_suggestions

def render_tab_2(proje, tesis_adi, hedef_sinif, litoloji, elek_serisi, materials, 
                  active_mats, current_rhos, current_was, current_las, current_mbs, 
                  current_site_factor, get_global_qc_history):
    st.subheader("2. Karışım Dizaynı ve Optimizasyon")
    
    # Karışım parametreleri
    col_mix1, col_mix2 = st.columns(2)
    
    with col_mix1:
        st.markdown("#### 🎯 Temel Karışım Parametreleri")
        cimento_val = st.number_input("Çimento (kg/m³)", min_value=200, max_value=600, value=350, key="cimento_val")
        su_val = st.number_input("Su (lt/m³)", min_value=100, max_value=300, value=180, key="su_val")
        katki_val = st.number_input("Kimyasal Katkı (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1, key="katki_val")
        wc_ratio = su_val / cimento_val if cimento_val > 0 else 0
        
        st.metric("Su/Çimento Oranı", f"{wc_ratio:.3f}")
        
        # Hedef sınıfa göre uyarı
        from logic.engineering import CONCRETE_RULES
        max_wc = CONCRETE_RULES.get(hedef_sinif, {}).get("max_wc", 0.55)
        if wc_ratio > max_wc:
            st.error(f"⚠️ W/C oranı {max_wc} üzerinde! Standartlara uygun değil.")
        else:
            st.success(f"✅ W/C oranı uygun (≤ {max_wc})")
    
    with col_mix2:
        st.markdown("#### 📊 Agrega Dağılımı")
        p_values = []
        total_p = 0
        
        for i, mat in enumerate(materials):
            if active_mats[i]:
                p_val = st.number_input(f"{mat} (%)", min_value=0, max_value=100, value=25, key=f"p{i+1}")
                p_values.append(p_val)
                total_p += p_val
        
        if total_p != 100 and total_p > 0:
            st.warning(f"⚠️ Toplam agrega yüzdesi: {total_p}% (100% olmalı)")
        elif total_p == 0:
            st.warning("⚠️ Hiç agrega seçilmedi")
    
    # Hava ve uçucu madde
    st.markdown("#### 🌬️ Hava ve Uçucu Maddeler")
    col_air1, col_air2 = st.columns(2)
    
    with col_air1:
        hava_yuzde = st.number_input("Hava İçeriği (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1, key="hava_yuzde")
    
    with col_air2:
        ucucu_kul = st.number_input("Uçucu Kül (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1, key="ucucu_kul")
    
    # Teorik dayanım hesabı
    st.markdown("#### 🔬 Teorik Dayanım Analizi")
    
    if all(active_mats) and cimento_val > 0:
        # AI model tahmini
        qc_history = get_global_qc_history(include_pool=True)
        
        if qc_history and len(qc_history) >= 5:
            from logic.ai_model import train_prediction_model
            coeffs, intercept, r2 = train_prediction_model(qc_history)
            
            if coeffs is not None:
                # Model inputları
                model_inputs = np.array([
                    cimento_val, su_val, ucucu_kul, hava_yuzde, katki_val
                ])
                
                pred_mpa = predict_strength_ai(coeffs, intercept, model_inputs)
                st.metric("🤖 AI Tahmini", f"{pred_mpa:.1f} MPa", delta=f"R²={r2:.3f}")
                
                # Hedefe göre optimizasyon önerileri
                target_mpa = CONCRETE_RULES[hedef_sinif]["min_mpa"]
                if pred_mpa < target_mpa:
                    suggestions = generate_suggestions(target_mpa, pred_mpa, model_inputs, coeffs)
                    if suggestions:
                        st.warning("💡 Optimizasyon Önerileri:")
                        for suggestion in suggestions:
                            st.info(f"• {suggestion}")
        
        # Teorik hesap
        theoretical_mpa = calculate_theoretical_mpa(
            cimento_val, su_val, wc_ratio, current_rhos, current_was, 
            p_values, active_mats, litoloji, current_site_factor
        )
        
        st.metric("📈 Teorik Hesap", f"{theoretical_mpa:.1f} MPa")
        
        # Uygunluk değerlendirmesi
        compliance = evaluate_mix_compliance(
            hedef_sinif, theoretical_mpa, wc_ratio, cimento_val, 
            current_las, current_mbs, active_mats
        )
        
        # Durum göstergesi
        status_color = "🟢" if compliance["status"] == "UYGUN" else "🟡" if compliance["status"] == "KISITLI" else "🔴"
        st.markdown(f"### {status_color} Karışım Durumu: {compliance['status']}")
        
        if compliance["warnings"]:
            for warning in compliance["warnings"]:
                st.warning(f"⚠️ {warning}")
        
        if compliance["recommendations"]:
            st.info("💡 Öneriler:")
            for rec in compliance["recommendations"]:
                st.info(f"• {rec}")
    
    # Optimizasyon butonu
    st.markdown("---")
    col_opt1, col_opt2, col_opt3 = st.columns([1, 2, 1])
    
    with col_opt2:
        if st.button("🚀 Akıllı Optimizasyon", use_container_width=True, help="AI destekli karışım optimizasyonu"):
            if all(active_mats):
                with st.spinner("🧠 Optimizasyon hesaplanıyor..."):
                    optimized_mix = optimize_mix(
                        hedef_sinif, cimento_val, su_val, p_values, 
                        current_rhos, current_was, litoloji, current_site_factor
                    )
                    
                    if optimized_mix:
                        st.success("✅ Optimizasyon tamamlandı!")
                        st.json(optimized_mix)
                    else:
                        st.error("❌ Optimizasyon yapılamadı. Lütfen parametreleri kontrol edin.")
            else:
                st.error("❌ Lütfen önce malzeme verilerini girin.")
