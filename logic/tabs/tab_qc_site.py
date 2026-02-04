import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from logic.data_manager import veriyi_kaydet, havuz_kaydet
from logic.engineering import classify_plant

def render_tab_4(proje, tesis_adi, TARGET_LIMITS, hedef_sinif, get_global_qc_history, is_admin=False):
    st.subheader("4. Şantiye Kalite Kontrol")
    
    # QC veri giriş formu
    st.markdown("#### 📝 Yeni QC Kaydı")
    
    col_qc1, col_qc2, col_qc3 = st.columns(3)
    
    with col_qc1:
        qc_date = st.date_input("Deneme Tarihi", datetime.now())
        batch_no = st.text_input("Parti No", value=f"{datetime.now().strftime('%Y%m%d')}-001")
    
    with col_qc2:
        slump = st.number_input("Akma (mm)", min_value=50, max_value=300, value=180)
        air_content = st.number_input("Hava İçeriği (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    
    with col_qc3:
        temperature = st.number_input("Beton Sıcaklığı (°C)", min_value=5, max_value=40, value=20)
        delivery_time = st.number_input("Teslimat Süresi (dk)", min_value=0, max_value=180, value=45)
    
    # Dayanım sonuçları
    st.markdown("#### 💪 Basınç Dayanımı Sonuçları")
    
    col_str1, col_str2, col_str3 = st.columns(3)
    
    with col_str1:
        d7 = st.number_input("7 Güç (MPa)", min_value=0.0, max_value=100.0, value=25.0, step=0.1)
    
    with col_str2:
        d28 = st.number_input("28 Güç (MPa)", min_value=0.0, max_value=100.0, value=40.0, step=0.1)
    
    with col_str3:
        d56 = st.number_input("56 Güç (MPa) (Opsiyonel)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    
    # Karışım bilgileri (otomatik doldur)
    st.markdown("#### 📊 Karışım Bilgileri")
    
    col_mix1, col_mix2 = st.columns(2)
    
    with col_mix1:
        cement = st.number_input("Çimento (kg/m³)", value=st.session_state.get('cimento_val', 350), disabled=True)
        water = st.number_input("Su (lt/m³)", value=st.session_state.get('su_val', 180), disabled=True)
    
    with col_mix2:
        wc_ratio = water / cement if cement > 0 else 0
        st.metric("W/C Oranı", f"{wc_ratio:.3f}")
        admixture = st.number_input("Katkı (%)", value=st.session_state.get('katki_val', 1.0), disabled=True)
    
    # Notlar
    notes = st.text_area("Notlar", placeholder="Özel gözlemler, sorunlar vb...")
    
    # Kaydet butonu
    col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
    
    with col_save2:
        if st.button("💾 QC Kaydını Kaydet", use_container_width=True, type="primary"):
            # QC kaydı oluştur
            qc_record = {
                "date": qc_date.strftime("%Y-%m-%d"),
                "batch_no": batch_no,
                "slump": slump,
                "air_content": air_content,
                "temperature": temperature,
                "delivery_time": delivery_time,
                "d7": d7,
                "d28": d28,
                "d56": d56 if d56 > 0 else None,
                "cement": cement,
                "water": water,
                "wc_ratio": wc_ratio,
                "admixture": admixture,
                "notes": notes,
                "concrete_class": hedef_sinif,
                "plant": tesis_adi
            }
            
            # Proje verilerine ekle
            active_p = st.session_state.get('active_plant', 'merkez')
            all_data = veriyi_kaydet(proje, qc_record, plant_id=active_p, append_qc=True)
            
            # Global AI havuzuna da ekle (isteğe bağlı)
            if st.checkbox("🌐 Global AI havuzuna ekle", value=True, help="Tüm santrallerin AI modelini geliştirir"):
                pool_record = qc_record.copy()
                pool_record["plant_id"] = active_p
                pool_record["project"] = proje
                havuz_kaydet(pool_record)
            
            st.success(f"✅ QC kaydı başarıyla eklendi! Parti No: {batch_no}")
            st.rerun()
    
    # QC Geçmişi ve Analiz
    st.markdown("---")
    st.markdown("#### 📈 QC Geçmişi ve İstatistikler")
    
    # Proje QC geçmişi
    active_p = st.session_state.get('active_plant', 'merkez')
    all_data = veriyi_kaydet(proje, {}, plant_id=active_p, get_only=True)
    qc_history = all_data.get("qc_history", [])
    
    if qc_history:
        # DataFrame oluştur
        qc_df = pd.DataFrame(qc_history)
        qc_df['date'] = pd.to_datetime(qc_df['date'])
        
        # Son 20 kayıt
        st.markdown("##### 📋 Son QC Kayıtları")
        display_df = qc_df[['date', 'batch_no', 'd28', 'slump', 'wc_ratio', 'temperature']].tail(20)
        display_df['date'] = display_df['date'].dt.strftime('%d.%m.%Y')
        st.dataframe(display_df, use_container_width=True)
        
        # Dayanım grafiği
        st.markdown("##### 📊 Dayanım Gelişimi")
        
        fig_strength = go.Figure()
        
        if 'd7' in qc_df.columns:
            fig_strength.add_trace(go.Scatter(
                x=qc_df['date'], y=qc_df['d7'],
                mode='lines+markers', name='7 Güç (MPa)',
                line=dict(color='blue', width=2)
            ))
        
        if 'd28' in qc_df.columns:
            fig_strength.add_trace(go.Scatter(
                x=qc_df['date'], y=qc_df['d28'],
                mode='lines+markers', name='28 Güç (MPa)',
                line=dict(color='red', width=3)
            ))
        
        if 'd56' in qc_df.columns:
            fig_strength.add_trace(go.Scatter(
                x=qc_df['date'], y=qc_df['d56'],
                mode='lines+markers', name='56 Güç (MPa)',
                line=dict(color='green', width=2)
            ))
        
        # Hedef dayanım çizgisi
        target_mpa = TARGET_LIMITS.get(hedef_sinif, {}).get("min_mpa", 37)
        fig_strength.add_hline(y=target_mpa, line_dash="dash", line_color="red", 
                              annotation_text=f"Hedef: {target_mpa} MPa")
        
        fig_strength.update_layout(
            title="Basınç Dayanımı Gelişimi",
            xaxis_title="Tarih",
            yaxis_title="Dayanım (MPa)",
            height=400
        )
        st.plotly_chart(fig_strength, use_container_width=True)
        
        # İstatistiksel analiz
        st.markdown("##### 📈 İstatistiksel Analiz")
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            if len(qc_df) > 0:
                avg_d28 = qc_df['d28'].mean()
                std_d28 = qc_df['d28'].std()
                st.metric("Ortalama 28g", f"{avg_d28:.1f} MPa")
                st.metric("Std. Sapma", f"{std_d28:.1f} MPa")
        
        with col_stat2:
            if len(qc_df) > 0:
                # Hedefe ulaşma oranı
                success_rate = (qc_df['d28'] >= target_mpa).mean() * 100
                st.metric("Başarı Oranı", f"{success_rate:.1f}%")
                
                # Son 10 kaydın trendi
                if len(qc_df) >= 10:
                    recent_avg = qc_df['d28'].tail(10).mean()
                    overall_avg = qc_df['d28'].mean()
                    trend = "📈" if recent_avg > overall_avg else "📉"
                    st.metric("Son 10 Trend", f"{trend} {recent_avg:.1f} MPa")
        
        with col_stat3:
            if len(qc_df) > 0:
                # W/C kontrolü
                max_wc = TARGET_LIMITS.get(hedef_sinif, {}).get("max_wc", 0.55)
                wc_compliance = (qc_df['wc_ratio'] <= max_wc).mean() * 100
                st.metric("W/C Uygunluğu", f"{wc_compliance:.1f}%")
                
                # Akma kontrolü
                slump_ok = ((qc_df['slump'] >= 160) & (qc_df['slump'] <= 200)).mean() * 100
                st.metric("Akma Uygunluğu", f"{slump_ok:.1f}%")
        
        # Sınıflandırma
        if is_admin:
            st.markdown("##### 🏭 Santral Performans Sınıflandırması")
            
            global_history = get_global_qc_history(include_pool=False)
            if global_history:
                classification = classify_plant(active_p, global_history)
                
                st.info(f"**Santral Sınıfı:** {classification['class']}")
                st.json(classification)
        
        # Excel dışa aktar
        st.markdown("##### 📥 Veri Dışa Aktar")
        
        if st.button("📊 QC Verilerini İndir (Excel)"):
            excel_data = qc_df.to_excel(index=False)
            st.download_button(
                label="Excel İndir",
                data=excel_data,
                file_name=f"{proje}_QC_Verileri_{datetime.now().strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.info("ℹ️ Henüz QC kaydı bulunmuyor. İlk kaydı oluşturmak için yukarıdaki formu doldurun.")
