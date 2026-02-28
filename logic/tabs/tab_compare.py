import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logic.engineering import calculate_theoretical_mpa, evaluate_mix_compliance
from logic.data_manager import havuz_yukle
from logic.ai_model import calculate_match_score, find_similar_recipes, derive_local_engineering_constants

def render_tab_compare(all_data, proje, elek_serisi, target_class="C30/37"):
    st.header("🔬 Dizayn ve Deneme Karşılaştırma")
    
    # Yerel Otonom Zeka Verileri
    pool_data = havuz_yukle()
    local_const = derive_local_engineering_constants(pool_data)
    st.markdown("""
    Bu bölümdeki araçlar, mevcut projenizdeki farklı denemeleri (versiyonları) ve 
    hafızadaki diğer başarılı dizaynları birbiriyle kıyaslamanıza olanak tanır.
    """)
    
    if not proje or proje not in all_data:
        st.warning("Analiz için geçerli bir proje seçilmedi.")
        return
        
    proj_data = all_data[proje]
    trials = proj_data.get("trials", {})
    
    if not trials:
        st.info("Bu projede henüz kayıtlı deneme bulunmuyor.")
        return
        
    # 1. DENEME SEÇİMİ
    st.subheader("📊 Deneme Karşılaştırma Matrisi")
    selected_trials = st.multiselect(
        "Karşılaştırılacak Denemeleri Seçin:",
        options=list(trials.keys()),
        default=list(trials.keys())[:3] # İlk 3 taneyi varsayılan seç
    )
    
    if not selected_trials:
        st.warning("Lütfen en az bir deneme seçiniz.")
        return
        
    # Tablo Verisi Hazırla
    comp_records = []
    for t_name in selected_trials:
        t_data = trials[t_name]
        mix = t_data.get("mix_data", {})
        
        # Temel verileri çek
        record = {
            "Deneme": t_name,
            "Çimento (kg)": t_data.get("cim", 0),
            "S/Ç Oranı": round(t_data.get("su", 0) / t_data.get("cim", 1), 3) if t_data.get("cim", 0) > 0 else 0,
            "Uçucu Kül (kg)": t_data.get("ucucu", 0),
            "Katkı (kg)": t_data.get("kat", 0),
            "Hava (%)": t_data.get("hava", 1.5),
            "D28 (Tahmin)": t_data.get("pred_mpa", 0)
        }
        comp_records.append(record)
        
    df_comp = pd.DataFrame(comp_records)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
    
    # 2. GÖRSEL ANALİZ (Radar veya Bar)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📉 Dayanım Karşılaştırması")
        fig_mpa = go.Figure()
        for t_name in selected_trials:
            t_data = trials[t_name]
            fig_mpa.add_trace(go.Bar(
                x=[t_name], 
                y=[t_data.get("pred_mpa", 0)],
                name=t_name
            ))
        fig_mpa.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
        st.plotly_chart(fig_mpa, use_container_width=True)
        
    with col2:
        st.subheader("💰 Göreli Maliyet Analizi")
        # Maliyet verisi (Basit tahmin)
        fig_cost = go.Figure()
        for t_name in selected_trials:
            t_data = trials[t_name]
            # Basit bir maliyet indeksi: Çimento * 1 + Katkı * 5 + Kül * 0.5
            cost_idx = t_data.get("cim", 0) * 1.0 + t_data.get("kat", 0) * 5.0 + t_data.get("ucucu", 0) * 0.5
            fig_cost.add_trace(go.Bar(
                x=[t_name], 
                y=[cost_idx],
                name=t_name,
                marker_color='orange'
            ))
        fig_cost.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
        st.plotly_chart(fig_cost, use_container_width=True)

    # 3. KGM ARŞİVİ İLE KIYASLAMA
    st.markdown("---")
    st.subheader("🏛️ KGM Arşiv Uyumluluk Analizi")
    st.write("Mevcut dizaynınızın KGM 'Altın Standart' kütüphanesindeki onaylı reçetelerle benzerlik skoru.")
    
    active_trial = st.selectbox("Arşivle Kıyaslanacak Deneme:", options=selected_trials)
    t_mix = trials[active_trial]
    
    if pool_data:
        # Inputs listesi: [cem, wat, ash, slag, air, chem]
        cur_inputs = [
            t_mix.get("cim", 0), t_mix.get("su", 0), 
            t_mix.get("ucucu", 0), t_mix.get("slag", 0),
            t_mix.get("hava", 1.5), t_mix.get("kat", 0)
        ]
        
        score = calculate_match_score(cur_inputs, pool_data, target_class)
        st.metric("Uyumluluk Skoru (Pattern Match)", f"%{score}")
        
        # Benzerleri Getir
        with st.expander("📚 Arşivdeki En Yakın Onaylı Reçeteler", expanded=True):
            similar = find_similar_recipes(cur_inputs, pool_data, top_n=3)
            if similar:
                for s in similar:
                    rec = s['record']
                    st.info(f"**Uyum: %{s['similarity']}** | {rec.get('target_class')} | {rec.get('d28')} MPa | S/Ç: {round(rec.get('water',0)/rec.get('cement',1), 2)}")
            else:
                st.write("Benzer kayıt bulunamadı.")
        
        if score > 85:
            st.success("✅ Mevcut dizayn, KGM tarafından onaylanmış geçmiş reçetelerle yüksek oranda örtüşmektedir.")
        elif score > 70:
            st.warning("⚠️ Dizayn standartlara yakın ancak bazı sapmalar içeriyor.")
        else:
            st.error("🚨 Mevcut dizayn daha önce onaylanmış başarılı örneklerden ciddi oranda sapmaktadır. Lütfen parametreleri gözden geçirin.")
    else:
        st.info("Kıyaslama yapılacak arşiv verisi bulunamadı.")
