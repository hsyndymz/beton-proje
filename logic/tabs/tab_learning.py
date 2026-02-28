import streamlit as st
import pandas as pd
from logic.data_manager import havuz_yukle, havuz_kaydet, kgm_arsiv_yukle, kgm_arsiv_kaydet
from logic.ai_model import (
    train_prediction_model, get_model_insights, 
    derive_local_engineering_constants, get_local_knowledge_stats
)
from logic.pdf_processor import extract_text_from_pdf, parse_concrete_design_with_ai

def render_tab_learning(is_admin=False, google_key=None, groq_key=None, deepseek_key=None):
    st.header("🧠 Yapay Zeka Eğitim Hafızası (Global Pool)")
    st.info("Bu sekme, yapay zekayı eğitmek için projelerden bağımsız tecrübeleri ve KGM onaylı tarihsel verileri yönetmeyi sağlar.")
    
    pool_data = havuz_yukle()
    
    # 1. Veri Giriş Formu (Yeni)
    with st.expander("➕ Yeni Tecrübe Kaydı Ekle", expanded=len(pool_data) == 0):
        c_cem, c2, c3 = st.columns(3)
        with c_cem:
            g_class = st.selectbox("Beton Sınıfı", ["C25/30", "C30/37", "C35/45", "C40/50", "Yol Betonu"], index=1, key="g_class_learning")
            g_cem = st.number_input("Çimento (kg)", value=350, key="g_cem_learning")
            g_wat = st.number_input("Su (L)", value=180, key="g_wat_learning")
        with c2:
            g_ash = st.number_input("Uçucu Kül (kg)", value=0, key="g_ash")
            g_slag = st.number_input("Cüruf (YFC) (kg)", value=0, key="g_slag")
        with c3:
            g_air = st.number_input("Hava (%)", value=1.5, key="g_air")
            g_chem = st.number_input("Katkı (KG - Bir Metreküpteki Toplam)", value=4.0, key="g_chem")
            
        g_d28 = st.number_input("28 Günlük Dayanım (MPa)", value=35.0, key="g_d28")
        is_official = st.checkbox("🏛️ Onaylı KGM Reçetesi Olarak İşaretle (10x Ağırlık)", value=False)
        
        if st.button("📥 Havuza Ekle"):
            new_entry = {
                "target_class": g_class,
                "cement": g_cem, "water": g_wat, "ash": g_ash, "slag": g_slag,
                "air": g_air, "admixture": g_chem, "d28": g_d28,
                "is_approved": is_official,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d")
            }
            pool_data.append(new_entry)
            havuz_kaydet(pool_data)
            st.success("Veri global havuza eklendi.")
            st.rerun()

    # --- YENİ: TOPLU PDF AI AKTARIM ---
    st.markdown("---")
    with st.expander("📚 Toplu PDF AI Aktarım Motoru (KGM Arşivi)", expanded=False):
        st.info("Bu modül, elinizdeki teknik PDF'leri okuyarak verileri otomatik ayıklar ve KGM arşivine işler.")
        uploaded_files = st.file_uploader("KGM Onaylı PDF'leri Seçin (Çoklu)", type=['pdf'], accept_multiple_files=True)
        
        if uploaded_files:
            if not google_key and not groq_key and not deepseek_key:
                st.error("🚨 PDF tarama işlemi için en az bir API anahtarı gereklidir. Lütfen sol taraftaki 'API Ayarları' kısmından anahtar girip kaydedin.")
            elif st.button("🚀 AI ile Tara ve Analiz Et"):
                st.session_state['pdf_extraction_results'] = []
                progress_bar = st.progress(0)
                
                for i, pdf_file in enumerate(uploaded_files):
                    # Progress update
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    with st.spinner(f"İşleniyor: {pdf_file.name}..."):
                        # 1. Metin Ayıkla
                        raw_text = extract_text_from_pdf(pdf_file)
                        # 2. AI ile Parçala (Fallback Destekli)
                        parsed_data = parse_concrete_design_with_ai(
                            raw_text, 
                            google_key=google_key, 
                            groq_key=groq_key, 
                            deepseek_key=deepseek_key
                        )
                        
                        if "error" not in parsed_data:
                            parsed_data["filename"] = pdf_file.name
                            st.session_state['pdf_extraction_results'].append(parsed_data)
                        else:
                            st.error(f"{pdf_file.name}: {parsed_data['error']}")
                            # Diagnostik Bilgi
                            with st.expander(f"🔍 Teşhis: {pdf_file.name} neden başarısız oldu?"):
                                st.write("**Ham AI Yanıtı:**")
                                st.code(st.session_state.get('last_ai_response', 'Yanıt yok.'))
                                st.write("**PDF'den Okunan Metin (İlk 500 Karakter):**")
                                st.code(raw_text[:500])
                
                st.success(f"Analiz tamamlandı. {len(st.session_state['pdf_extraction_results'])} dosya başarıyla okundu.")

            # Ayıklanan verileri tabloda göster ve onay al
            if st.session_state.get('pdf_extraction_results'):
                st.markdown("##### 📋 Ayıklanan Veri Önizleme")
                results_df = pd.DataFrame(st.session_state['pdf_extraction_results'])
                st.dataframe(results_df, use_container_width=True)
                
                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if st.button("✅ Hepsini Onayla ve Arşive Aktar", type="primary"):
                        current_pool = havuz_yukle()
                        for res in st.session_state['pdf_extraction_results']:
                            res["is_approved"] = True
                            res["source"] = f"AI-PDF Import: {res.get('filename')}"
                            # Temizlik: null/None değerleri 0'a çek
                            for k in ["cement", "water", "ash", "slag", "air", "admixture", "d28"]:
                                if res.get(k) is None: res[k] = 0.0
                            current_pool.append(res)
                        
                        havuz_kaydet(current_pool)
                        st.session_state.pop('pdf_extraction_results')
                        st.success("Tüm veriler 'Altın Standart' olarak başarıyla Arşive kaydedildi! 🚀")
                        st.rerun()
                with c_act2:
                    if st.button("🗑️ Listeyi Temizle"):
                        st.session_state.pop('pdf_extraction_results')
                        st.rerun()

    # 2. Mevcut Veriler ve AI Analizi
    if pool_data:
        st.subheader(f"📊 Mevcut Eğitim Havuzu ({len(pool_data)} Kayıt)")
        df_pool = pd.DataFrame(pool_data)
        
        # BEYİN SAĞLIĞI (İstatistikler)
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            avg_d28 = df_pool["d28"].mean()
            st.metric("Ortalama Dayanım", f"{avg_d28:.1f} MPa")
        with col_st2:
            # Model Eğit ve R2 al
            coeffs, intercept, r2 = train_prediction_model(pool_data)
            st.metric("AI Tahmin Hassasiyeti (R²)", f"%{r2*100:.1f}")
        with col_st3:
            st.metric("Toplam Tecrübe", len(pool_data))

        # --- AI SHOWCASE (BİLGİ VİTRİNİ) ---
        st.markdown("### 🏛️ AI Bilgi Vitrini: Verilerden Öğrenilen Kurallar")
        
        # Yerel Otonom Zeka: Katsayı Türetme
        local_const = derive_local_engineering_constants(pool_data)
        local_stats = get_local_knowledge_stats(pool_data)
        
        col_inf1, col_inf2 = st.columns([1, 1])
        with col_inf1:
            if local_const:
                st.success(f"📈 **Yerel Mühendislik Katsayıları Aktif**\n\n"
                           f"Sizin verilerinize özel Bolomey denklemi:\n"
                           f"**fcm = {local_const['A']} * e^(-{local_const['B']} * S/Ç)**\n\n"
                           f"*{local_const['count']} onaylı tecrübeden öğrenildi.*")
            else:
                st.info("ℹ️ Yerel katsayıların hesaplanması için havuzda en az 20 onaylı tecrübe gereklidir. Şu an standart TS 802 katsayıları kullanılıyor.")
        
        with col_inf2:
            if local_stats:
                st.metric("💪 En İyi Çimento Verimliliği", f"{local_stats['best_efficiency']} kg/MPa")
                st.caption(f"Ortalama verimlilik: {local_stats.get('avg_efficiency', 'N/A')} kg/MPa")

        if coeffs is not None:
            feature_names = ["Çimento", "Su", "Kül", "Cüruf", "Hava", "Katkı"]
            insights = get_model_insights(coeffs, feature_names)
            with st.expander("🔍 Detaylı AI Korelasyon Analizi", expanded=True):
                for ins in insights:
                    st.write(ins)
        else:
            st.caption("ℹ️ Yeterli veri biriktiğinde detaylı AI korelasyonları burada sergilenecek.")

        # Pool Dataframe (Renklendirmeli)
        st.markdown("#### 🧪 Havuz Detayları")
        def color_approved(row):
            return ['background-color: #dcfce7' if row.is_approved else '' for _ in row]
            
        st.dataframe(df_pool.style.apply(color_approved, axis=1), use_container_width=True)
        
        # --- KGM ARŞİVİ (ÖZEL BÖLÜM) ---
        kgm_data = kgm_arsiv_yukle()
        if kgm_data:
            with st.expander(f"📚 KGM Tarihsel Arşiv (2011-2026) - {len(kgm_data)} Kayıt", expanded=False):
                st.dataframe(pd.DataFrame(kgm_data), use_container_width=True)
        
        st.markdown("---")
        # Global Havuz temizleme sadece Admin yetkisindedir
        user_info = st.session_state.get('user_info', {})
        if user_info.get('role') == "Admin" or is_admin:
            if st.checkbox("Havuza sıfırla (Tehlikeli!)"):
                if st.button("🗑️ TÜM HAVUZU SİL"):
                     havuz_kaydet([])
                     st.success("Havuz temizlendi.")
                     st.rerun()
        else:
            st.info("💡 Global hafıza yönetimi sadece Yöneticilere açıktır.")
    else:
        st.warning("Eğitim havuzu şu an boş. Veri ekleyerek başlayın.")
