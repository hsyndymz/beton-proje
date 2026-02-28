import streamlit as st
import pandas as pd
from logic.engineering import suggest_smart_recipes, CONCRETE_RULES, EXPOSURE_CLASSES
from logic.ocak_manager import ocaklari_yukle
from logic.data_manager import havuz_yukle
from logic.ai_model import (
    derive_local_engineering_constants, find_similar_recipes,
    get_local_knowledge_stats, train_prediction_model, get_model_insights
)

def render_tab_smart_mix():
    st.header("🧪 Akıllı Karışım (Smart Mix)")
    st.info("Bu modül, seçilen ocaktaki malzemeleri kullanarak hedef beton sınıfı için en uygun karışım reçetelerini otomatik olarak türetir.")

    # Yerel Otonom Zeka Verileri
    pool_data = havuz_yukle()
    local_const = derive_local_engineering_constants(pool_data)
    local_stats = get_local_knowledge_stats(pool_data)

    # --- AI BİLGİ VİTRİNİ (BANNER) ---
    with st.container():
        st.markdown("""
        <div style="background-color: #f8fafc; padding: 15px; border-radius: 10px; border-left: 5px solid #6366f1; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #1e293b;">🏛️ AI Bilgi Vitrini: Yerel Tecrübe Analizi</h4>
            <p style="margin: 5px 0; color: #64748b; font-size: 0.9rem;">Sistem, geçmiş onaylı dökümlerinizden öğrenerek mühendislik katsayılarını optimize eder.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c_ai1, c_ai2, c_ai3 = st.columns(3)
        with c_ai1:
            if local_const:
                st.success(f"📈 **Yerel Katsayılar Aktif**\n\nA:{local_const['A']} | B:{local_const['B']}")
            else:
                st.info("ℹ️ Standart TS 802 kullanılıyor.")
        with c_ai2:
            if local_stats:
                st.metric("💪 En İyi Verimlilik", f"{local_stats['best_efficiency']} kg/MPa")
        with c_ai3:
            st.metric("🎓 Toplam Tecrübe", len(pool_data))

        # Detaylı Korelasyon Analizi (Universal Görünürlük)
        coeffs, _, _ = train_prediction_model(pool_data)
        if coeffs is not None:
            feature_names = ["Çimento", "Su", "Kül", "Cüruf", "Hava", "Katkı"]
            insights = get_model_insights(coeffs, feature_names)
            with st.expander("🔍 Detaylı AI Korelasyon Analizi (Sistem Neleri Öğrendi?)", expanded=False):
                st.info("Bu analiz, havuzdaki verilerin birbiriyle olan matematiksel ilişkisini gösterir.")
                for ins in insights:
                    st.write(ins)

    # 1. Giriş Parametreleri
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Beton Sınıfı
        target_class = st.selectbox("Hedef Beton Sınıfı", list(CONCRETE_RULES.keys()), index=2) # Default C30/37
    
    with c2:
        # Çevresel Etki
        exposure_class = st.selectbox("Çevresel Etki Sınıfı", list(EXPOSURE_CLASSES.keys()), index=3) # Default XC3
        
    with c3:
        # Dmax
        dmax_opts = [31.5, 22.4, 16.0]
        dmax = st.selectbox("Maksimum Tane Çapı (Dmax)", dmax_opts, index=0)

    # 1.1 Mineral Katkı Seçenekleri (Yeni)
    with st.expander("💡 Mineral Katkı Kullanımı (YFC / Uçucu Kül)", expanded=False):
        mc1, mc2 = st.columns(2)
        with mc1:
            slag_pct = st.slider("Cüruf (YFC) Oranı (%)", 0, 70, 0, help="Toplam bağlayıcı içindeki cüruf yüzdesi.")
        with mc2:
            ash_pct = st.slider("Uçucu Kül Oranı (%)", 0, 40, 0, help="Toplam bağlayıcı içindeki uçucu kül yüzdesi.")

    # 2. Ocak ve Malzeme Kaynağı Seçimi
    ocaklar = ocaklari_yukle()
    if not ocaklar:
        st.warning("⚠️ Sistemde tanımlı ocak bulunamadı. Lütfen 'Ocak Yönetimi' sekmesinden ocak ekleyin.")
        return

    ocak_options = list(ocaklar.keys())
    
    selected_quarry_id = st.selectbox(
        "Hammadde Kaynağı (Ocak Seçimi)", 
        ocak_options,
        format_func=lambda x: (ocaklar[x].get("name", x) if isinstance(ocaklar[x], dict) else str(ocaklar[x]))
    )

    if selected_quarry_id:
        # Safe data retrieval
        q_data = ocaklar[selected_quarry_id]
        if not isinstance(q_data, dict):
             st.error("Seçilen ocak verisi bozuk.")
             return

        # Gradasyon verilerini çek
        quarry_materials = q_data.get("material_gradations", {})
        
        if not quarry_materials:
            st.warning(f"⚠️ '{q_data.get('name', selected_quarry_id)}' ocağı için malzeme gradasyon verisi girilmemiş.")
            st.info("Git: Ocak Yönetimi > Elek Analizi Yönetimi")
            
            # --- TESTING SHORTCUT ---
            if st.button("🧪 Test İçin Örnek Veri Yükle (Otomatik)", type="secondary"):
                # Standart test verileri (Passing % - Geçen Yüzdeler)
                # Kaba: İnce eleklerde az geçer -> 0'a yaklaşır.
                # İnce: İnce eleklerde çok geçer -> 100'e yakın.
                mock_grads = {
                    "Kaba Agrega": [100, 95, 55, 10, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                    "Orta Agrega": [100, 100, 100, 85, 35, 5, 0, 0, 0, 0, 0, 0, 0],
                    "İnce Agrega": [100, 100, 100, 100, 95, 70, 40, 15, 5, 0, 0, 0, 0],
                    "Kırma Kum":   [100, 100, 100, 100, 100, 95, 75, 45, 25, 10, 2, 0, 0]
                }
                # Veriyi tersine çevir (Geçen -> Kalan dönüşümü gerekebilir ama burada geçen olarak kaydediyoruz)
                # Sistem "Geçen" bekliyor.
                q_data["material_gradations"] = mock_grads
                from logic.ocak_manager import ocak_kaydet
                ocak_kaydet(selected_quarry_id, q_data)
                st.success("Örnek veriler yüklendi! Sayfa yenileniyor...")
                st.rerun()
            
            return
            
        # --- MALİYET YÖNETİMİ ---
        with st.expander("💰 Malzeme Birim Maliyetleri (TL/ton)", expanded=False):
            st.caption("Reçete maliyetini hesaplamak için birim fiyatları giriniz.")
            costs = {}
            c_cost1, c_cost2 = st.columns(2)
            
            # Agrega Maliyetleri
            with c_cost1:
                st.markdown("**Agrega Fiyatları**")
                for mat in quarry_materials.keys():
                    # Varsayılan fiyatlar
                    def_price = 150.0 if "Kum" in mat else 120.0
                    costs[mat] = st.number_input(f"{mat}", value=def_price, step=10.0, key=f"cost_{mat}")
            
            # Bağlayıcı ve Su Maliyetleri
            with c_cost2:
                st.markdown("**Diğer Fiyatlar**")
                costs["Cement"] = st.number_input("Çimento (TL/ton)", value=2500.0, step=50.0, key="cost_cem")
                costs["Slag"] = st.number_input("Cüruf (TL/ton)", value=1800.0, step=50.0, key="cost_slag")
                costs["Ash"] = st.number_input("Uçucu Kül (TL/ton)", value=1200.0, step=50.0, key="cost_ash")
                costs["Water"] = st.number_input("Su (TL/ton)", value=25.0, step=5.0, key="cost_wat")
                costs["Admixture"] = st.number_input("Katkı (TL/kg)", value=45.0, step=5.0, key="cost_chem") # Katkı kg fiyatı

        if st.button("🚀 Akıllı Reçeteyi Hesapla", type="primary"):
            with st.spinner("Mühendislik motoru ve maliyet algoritmaları çalışıyor..."):
                results = suggest_smart_recipes(
                    target_class=target_class,
                    quarry_materials=quarry_materials,
                    dmax=dmax,
                    exposure_class=exposure_class,
                    slag_pct=slag_pct,
                    fly_ash_pct=ash_pct,
                    local_constants=local_const
                )
            
            if results:
                st.success(f"✅ {len(results)} farklı reçete alternatifi analiz edildi.")
                
                # Maliyet Hesabı Ekle
                for r in results:
                    total_cost = 0.0
                    total_cost += (r.get('cement', 0) / 1000) * costs["Cement"]
                    total_cost += (r.get('slag', 0) / 1000) * costs["Slag"]
                    total_cost += (r.get('ash', 0) / 1000) * costs["Ash"]
                    total_cost += (r.get('water', 0) / 1000) * costs["Water"]
                    
                    aggs = r.get("aggregates", {})
                    for mat, amount in aggs.items():
                        price = costs.get(mat, 0)
                        total_cost += (amount / 1000) * price
                        
                    r["cost_per_m3"] = round(total_cost, 2)
                
                # Sonuçları Sırala (En düşük maliyetten en yükseğe)
                results.sort(key=lambda x: x["cost_per_m3"])
                
                # --- GRAFİKSEL KARŞILAŞTIRMA ---
                st.markdown("### 📊 Reçete Karşılaştırma Analizi")
                
                # Basit Bar Chart: Maliyet
                chart_data = pd.DataFrame([{
                    "Reçete": r.get('name'), 
                    "Maliyet (TL/m³)": r.get('cost_per_m3'),
                    "Çimento (kg)": r.get('cement'),
                    "Su/Çimento": r.get('wc_ratio')
                } for r in results])
                
                c_chart1, c_chart2 = st.columns(2)
                with c_chart1:
                    st.markdown("**Maliyet Analizi**")
                    st.bar_chart(chart_data, x="Reçete", y="Maliyet (TL/m³)", color="#10B981") # Green
                
                with c_chart2:
                    st.markdown("**Çimento Tüketimi**")
                    st.bar_chart(chart_data, x="Reçete", y="Çimento (kg)", color="#6366f1") # Indigo

                # Detaylı Kartlar
                st.markdown("### 🧬 Reçete Detayları")
                for i, res in enumerate(results):
                    # En ucuz olana "Ekonomik Seçim" etiketi
                    badge = "🏆 EN EKONOMİK" if i == 0 else f"Alternatif #{i+1}"
                    
                    with st.expander(f"{badge} | {res.get('name')} | 💰 {res.get('cost_per_m3')} TL/m³", expanded=(i==0)):
                        rc1, rc2, rc3 = st.columns([1, 1, 1])
                        
                        with rc1:
                            st.markdown("#### 💧 Karışım (1 m³)")
                            st.write(f"**Çimento:** {res.get('cement')} kg")
                            if res.get('slag', 0) > 0: st.write(f"**Cüruf (YFC):** {res.get('slag')} kg")
                            if res.get('ash', 0) > 0: st.write(f"**Uçucu Kül:** {res.get('ash')} kg")
                            st.write(f"**Su:** {res.get('water')} kg")
                            st.write(f"**S/Ç Oranı:** {res.get('wc_ratio')}")
                            
                            st.markdown("#### 📈 Dayanım Tahmini")
                            st.write(f"**28 Günlük (TS 802):** {res.get('pred_mpa')} MPa")
                            st.write(f"**90 Günlük (Puzolan):** {res.get('pred_90d')} MPa")
                            
                            st.metric("Birim Maliyet", f"{res.get('cost_per_m3')} TL")
                            
                        with rc2:
                            st.markdown("#### 🪨 Agrega (kg)")
                            aggs = res.get("aggregates", {})
                            for k, v in aggs.items():
                                st.write(f"**{k}:** {v}")
                        
                            st.markdown("#### ⚙️ Aksiyonlar")
                            if st.button("🧪 Laboratuvara Gönder", key=f"btn_send_lab_{i}"):
                                # Session State'e kaydet ve kullanıcıyı uyar
                                st.session_state['transferred_recipe'] = res
                                st.success("Reçete kopyalandı! Sol menüden '2. Karışım Oranları' sekmesine geçiniz.")
                                st.toast("Reçete Transfer Edildi! 🚀", icon="✅")
                                st.rerun()

                        # --- YENİ: BENZER REÇETE ANALİZİ (API BAĞIMSIZ) ---
                        with rc3:
                            st.markdown("#### 📖 Benzer Tecrübeler")
                            st.caption("Veri havuzundaki yerel benzerler")
                            
                            # Mevcut reçetenin girdilerini topla
                            cur_inputs = [
                                res.get('cement', 0), res.get('water', 0),
                                res.get('ash', 0), res.get('slag', 0),
                                2.0, 4.0 # Hava ve Katkı (Varsayılan)
                            ]
                            similar = find_similar_recipes(cur_inputs, pool_data, top_n=2)
                            
                            if similar:
                                for s in similar:
                                    rec = s['record']
                                    sim_score = s['similarity']
                                    st.info(f"**Uyum: %{sim_score}**\n\n"
                                            f"**ID:** {rec.get('id', 'N/A')}\n"
                                            f"**Dayanım:** {rec.get('d28')} MPa\n"
                                            f"**S/Ç:** {round(rec.get('water',0)/rec.get('cement',1), 2)}")
                            else:
                                st.write("Henüz benzer onaylı kayıt yok.")

            else:
                st.error("😔 Uygun bir reçete bulunamadı. Malzeme gradasyonları standart eğrilerle uyumsuz olabilir.")
