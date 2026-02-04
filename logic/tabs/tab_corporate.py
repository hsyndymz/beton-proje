import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logic.corporate_logic import get_corp_performance_stats, calculate_cement_efficiency_stats, generate_risk_heatmap_data
from logic.data_manager import santralleri_yukle
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_corporate_tab(is_admin=False):
    st.header("📊 Kurumsal Performans Paneli (Yönetici Özeti)")
    
    if not is_admin:
        st.warning("⚠️ Bu panel sadece yönetici yetkisine sahip kullanıcılar içindir.")
        return

    # 1. Santral Filtreleme
    plants_db = santralleri_yukle()
    all_plant_ids = list(plants_db.keys())
    
    with st.expander("🔍 Analiz Filtreleri / Santral Seçimi", expanded=True):
        selected_plants = st.multiselect(
            "Analiz Edilecek Santralleri Seçin:",
            options=all_plant_ids,
            default=all_plant_ids,
            format_func=lambda x: plants_db[x]["name"]
        )

    if not selected_plants:
        st.warning("Lütfen en az bir santral seçiniz.")
        return

    # Verileri Çek ve Filtrele
    with st.spinner("Tesis verileri analiz ediliyor..."):
        df_corp_all = get_corp_performance_stats()
        if df_corp_all.empty:
            st.info("📊 Analiz edilecek yeterli veri bulunamadı.")
            return
        
        # Seçili santrallere göre filtrele
        df_corp = df_corp_all[df_corp_all["id"].isin(selected_plants)]

    if df_corp.empty:
        st.info("Seçilen santraller için yeterli veri bulunamadı.")
        return

    # --- 1. ÜST METRİKLER ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Analiz Edilen Tesis", len(df_corp))
    m2.metric("Toplam Numune", df_corp["samples"].sum())
    m3.metric("Kurumsal Sigma (Ort)", f"{df_corp['sigma'].mean():.2f}")
    
    critical_count = len(df_corp[df_corp["status"] == "🔴 Kritik"])
    m4.metric("Kritik Tesis", critical_count, delta=critical_count, delta_color="inverse")

    # --- 2. PERFORMANS TABLOSU ---
    st.subheader("🏭 Tesis Bazlı Performans Matrisi")
    
    def highlight_status(val):
        color = 'red' if 'Kritik' in val else ('orange' if 'Riskli' in val else 'green')
        return f'color: {color}; font-weight: bold'

    styled_df = df_corp.style.applymap(highlight_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # --- 3. ANALİTİK GRAFİKLER ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📉 Standart Sapma (Sigma) Dağılımı")
        fig_sigma = go.Figure(data=[
            go.Bar(x=df_corp["name"], y=df_corp["sigma"], 
                   marker_color=['red' if s > 5 else ('orange' if s > 3.5 else 'green') for s in df_corp["sigma"]])
        ])
        fig_sigma.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Sigma (MPa)")
        st.plotly_chart(fig_sigma, use_container_width=True)

    with c2:
        st.subheader("💎 Çimento Verimliliği (kg / MPa)")
        eff_df = calculate_cement_efficiency_stats(df_corp)
        fig_eff = go.Figure(data=[
            go.Bar(x=eff_df["name"], y=eff_df["cement_eff"], marker_color="royalblue")
        ])
        fig_eff.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="kg Çimento / 1 MPa")
        st.plotly_chart(fig_eff, use_container_width=True)

    # --- 4. RİSK ISI HARİTASI ---
    st.markdown("---")
    st.subheader("🔥 Performans ve Risk Matrisi")
    
    fig_risk = go.Figure()
    fig_risk.add_trace(go.Scatter(
        x=df_corp["avg_mpa"], 
        y=df_corp["sigma"],
        mode='markers+text',
        text=df_corp["name"],
        textposition="top center",
        marker=dict(size=15, color=df_corp["sigma"], colorscale='RdYlGn', reversescale=True, showscale=True),
        hovertemplate="<b>%{text}</b><br>Ort. Dayanım: %{x} MPa<br>Sigma: %{y}<extra></extra>"
    ))
    fig_risk.update_layout(
        xaxis_title="Ortalama Dayanım (MPa)",
        yaxis_title="Standart Sapma (Sigma)",
        height=450,
        plot_bgcolor="white"
    )
    
    # Bölgeleri Belirle
    fig_risk.add_hrect(y0=0, y1=3.5, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Güvenli (A Sınıfı)")
    fig_risk.add_hrect(y0=5.0, y1=max(df_corp["sigma"].max() + 1, 8), fillcolor="red", opacity=0.1, line_width=0, annotation_text="Kritik (C Sınıfı)")
    
    st.plotly_chart(fig_risk, use_container_width=True)
    
    logger.info(f"Kurumsal analiz yapıldı. Santral sayısı: {len(selected_plants)}", user=st.session_state.get('username'))
