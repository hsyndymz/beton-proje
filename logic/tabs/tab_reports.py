import streamlit as st
from logic.report_generator import generate_kgm_raporu
from logic.data_manager import veriyi_yukle
import datetime

def render_tab_3(proje, selected_provider, TS_STANDARDS_CONTEXT):
    st.subheader("3. Raporlar & Çıktılar")
    
    # Proje verilerini yükle
    active_p = st.session_state.get('active_plant', 'merkez')
    all_data = veriyi_yukle(plant_id=active_p)
    project_data = all_data.get(proje, {})
    
    # Rapor tipi seçimi
    col_r1, col_r2 = st.columns([2, 1])
    
    with col_r1:
        report_type = st.selectbox(
            "📄 Rapor Tipi Seçin",
            ["KGM Teknik Raporu", "Karışım Kartı", "Malzeme Analiz Raporu", "QC Geçmişi"]
        )
    
    with col_r2:
        if st.button("🔄 Verileri Yenile", help="Proje verilerini güncelle"):
            st.rerun()
    
    if report_type == "KGM Teknik Raporu":
        st.markdown("#### 🏗️ KGM Teknik Raporu")
        
        # Rapor metadatası
        col_meta1, col_meta2 = st.columns(2)
        
        with col_meta1:
            employer = st.text_input("İdare", value="T.C. ULAŞTIRMA VE ALTYAPI BAKANLIĞI")
            contractor = st.text_input("Yüklenici", value="YÜKLENİCİ FİRMA A.Ş.")
        
        with col_meta2:
            revision = st.text_input("Revizyon", value="R0")
            report_date = st.date_input("Rapor Tarihi", datetime.datetime.now())
        
        # Rapor önizleme
        if st.button("📋 Rapor Önizleme", use_container_width=True):
            if project_data:
                snapshot = {
                    "project_name": proje,
                    "plant_name": project_data.get("plant_name", "BETON SANTRALİ"),
                    "employer": employer,
                    "contractor": contractor,
                    "revision": revision,
                    "mix_data": {
                        "class": st.session_state.get('hedef_sinif', 'C30/37'),
                        "lithology": st.session_state.get('litoloji', 'Bilinmiyor'),
                        "asr_status": st.session_state.get('asr_status', 'Belirtilmemiş'),
                        "exposure_class": st.session_state.get('exposure_class', 'XC3')
                    },
                    "material_data": {
                        "rhos": project_data.get("rhos", []),
                        "was": project_data.get("was", []),
                        "las": project_data.get("las", []),
                        "mbs": project_data.get("mbs", [])
                    },
                    "recipe": {
                        "cement": st.session_state.get('cimento_val', 350),
                        "water": st.session_state.get('su_val', 180),
                        "admixture": st.session_state.get('katki_val', 1.0),
                        "air": st.session_state.get('hava_yuzde', 1.5),
                        "fly_ash": st.session_state.get('ucucu_kul', 0)
                    },
                    "decision": {
                        "status": "GREEN",  # Bu dinamik olmalı
                        "pred_mpa": 40.0  # Bu hesaplanmalı
                    }
                }
                
                # HTML rapor oluştur
                html_report = generate_kgm_raporu(snapshot)
                st.components.v1.html(html_report, height=1000, scrolling=True)
                
                # İndirme butonu
                st.download_button(
                    label="📥 Raporu İndir (HTML)",
                    data=html_report,
                    file_name=f"{proje}_KGM_Raporu_{report_date.strftime('%d%m%Y')}.html",
                    mime="text/html"
                )
            else:
                st.error("❌ Rapor oluşturmak için önce proje verilerini kaydedin!")
    
    elif report_type == "Karışım Kartı":
        st.markdown("#### 📋 Karışım Kartı")
        
        if project_data:
            # Karışım kartı tablosu
            mix_data = {
                "Bileşen": ["Çimento", "Su", "Kum 0-5mm", "Kum 0-7mm", "Çakıl 5-15mm", "Çakıl 15-25mm", "Kimyasal Katkı", "Hava"],
                "Miktar (kg/m³)": [
                    st.session_state.get('cimento_val', 350),
                    st.session_state.get('su_val', 180),
                    0,  # Bu değerler dinamik olmalı
                    0,
                    0,
                    0,
                    st.session_state.get('katki_val', 1.0),
                    st.session_state.get('hava_yuzde', 1.5)
                ]
            }
            
            df_mix = pd.DataFrame(mix_data)
            st.dataframe(df_mix, use_container_width=True)
            
            # Karışım bilgileri
            st.markdown("#### 📊 Karışım Özellikleri")
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.metric("Su/Çimento", f"{st.session_state.get('su_val', 180) / st.session_state.get('cimento_val', 350):.3f}")
                st.metric("Çimento Sınıfı", "CEM I 42.5 R")
            
            with col_info2:
                st.metric("Beton Sınıfı", st.session_state.get('hedef_sinif', 'C30/37'))
                st.metric("Akma", "180 ± 20 mm")
        else:
            st.warning("⚠️ Karışım kartı için önce proje verilerini girin.")
    
    elif report_type == "Malzeme Analiz Raporu":
        st.markdown("#### 🔬 Malzeme Analiz Raporu")
        
        if project_data and project_data.get("rhos"):
            # Malzeme özellikleri tablosu
            materials = ["No:2 (15-25)", "No:1 (5-15)", "K.Kum (0-5)", "D.Kum (0-7)"]
            
            material_df = pd.DataFrame({
                "Malzeme": materials,
                "Özgül Ağırlık (t/m³)": project_data.get("rhos", []),
                "Su Emme (%)": project_data.get("was", []),
                "LA Aşınma (%)": project_data.get("las", []),
                "MB Değeri": project_data.get("mbs", [])
            })
            
            st.dataframe(material_df, use_container_width=True)
            
            # Uygunluk kontrolü
            st.markdown("#### ✅ Standart Uygunluğu")
            
            for i, mat in enumerate(materials):
                if i < len(project_data.get("las", [])):
                    la_val = project_data["las"][i]
                    if la_val > 40:
                        st.error(f"❌ {mat}: LA aşınma değeri yüksek ({la_val}%)")
                    else:
                        st.success(f"✅ {mat}: LA aşınma değeri uygun ({la_val}%)")
        else:
            st.warning("⚠️ Malzeme analizi için laboratuvar verileri girin.")
    
    elif report_type == "QC Geçmişi":
        st.markdown("#### 📈 Kalite Kontrol Geçmişi")
        
        qc_history = project_data.get("qc_history", [])
        
        if qc_history:
            qc_df = pd.DataFrame(qc_history)
            
            # Tarih formatı
            if 'date' in qc_df.columns:
                qc_df['date'] = pd.to_datetime(qc_df['date']).dt.strftime('%d.%m.%Y')
            
            st.dataframe(qc_df.tail(10), use_container_width=True)
            
            # Grafik
            if 'd28' in qc_df.columns:
                st.markdown("#### 📊 28 Güç Dayanımı Grafiği")
                st.line_chart(qc_df[['d28']].tail(20))
        else:
            st.info("ℹ️ Henüz QC kaydı bulunmuyor.")
    
    # AI Destekli Rapor
    st.markdown("---")
    st.markdown("#### 🤖 AI Destekli Teknik Değerlendirme")
    
    ai_prompt = st.text_area(
        "Rapor için teknik sorunuz veya analiz talebiniz:",
        placeholder="Örn: Bu karışımın donma-çözüme dayanımını değerlendir...",
        height=100
    )
    
    if st.button("🧠 AI Raporu Oluştur", use_container_width=True):
        if ai_prompt.strip():
            st.session_state['ai_report_prompt'] = f"""
            {TS_STANDARDS_CONTEXT}
            
            Proje: {proje}
            Beton Sınıfı: {st.session_state.get('hedef_sinif', 'C30/37')}
            Çimento: {st.session_state.get('cimento_val', 350)} kg/m³
            Su: {st.session_state.get('su_val', 180)} lt/m³
            W/C: {st.session_state.get('su_val', 180) / st.session_state.get('cimento_val', 350):.3f}
            
            Soru: {ai_prompt}
            
            Lütfen teknik ve standartlara uygun cevap verin.
            """
            st.rerun()
        else:
            st.error("❌ Lütfen bir soru girin.")
    
    # AI rapor çıktısı
    if 'ai_report_output' in st.session_state:
        st.markdown("#### 🤖 AI Teknik Cevabı")
        st.info(st.session_state['ai_report_output'])
        
        if st.button("🗑️ Temizle"):
            del st.session_state['ai_report_output']
            st.rerun()
