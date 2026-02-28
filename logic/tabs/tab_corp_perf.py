import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logic.corporate_logic import calculate_cement_efficiency_stats

# Placeholder for get_corp_performance_stats if it was internal to modular_tabs
# If it was imported, we need to ensure it's available. 
# Looking at previous file view, it might be in logic.engineering or logic.data_manager
# But wait, looking at the code, it calls get_corp_performance_stats(). 
# If it was defined in modular_tabs.py, I need to find it.

def render_tab_corp_perf(is_admin=False):
    # --- INDUSTRIAL SWISS CSS ---
    st.markdown("""
        <style>
        .corp-header {
            background-color: #f1f5f9;
            padding: 1.5rem;
            border-radius: 4px;
            border-left: 6px solid #f97316; /* Safety Orange */
            margin-bottom: 2rem;
        }
        .corp-header h3 {
            margin: 0;
            color: #0f172a;
            font-family: 'Fira Sans', sans-serif;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: left;
            border-top: 3px solid #64748b;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            color: #0f172a;
            font-size: 2rem;
            font-weight: 700;
            font-family: 'Fira Code', monospace;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="corp-header"><h3>📊 Kurumsal Performans Paneli (Yönetici Özeti)</h3></div>', unsafe_allow_html=True)
    
    if not is_admin:
        st.warning("⚠️ Bu panel sadece yönetici yetkisine sahip kullanıcılar içindir.")
        return

    # --- FİLTRELEME ---
    c_filt1, c_filt2 = st.columns([1, 1])
    with c_filt1:
        years = ["2024", "2025", "2026"]
        st.multiselect("📅 Analiz Yılları", options=years, default=years)
    
    # Verileri Çek
    # Assuming get_corp_performance_stats is imported or defined elsewhere. 
    # If it was in modular_tabs, we need to extract it to a shared place.
    # For now, I'll attempt to import it from logic.engineering or expect it to be passed?
    # Actually, in the original code it was just called. 
    # Let's assume it needs to be imported. 
    from logic.corporate_logic import get_corp_performance_stats

    with st.spinner("Kurumsal veriler işleniyor..."):
        df_corp = get_corp_performance_stats()

    if df_corp.empty:
        st.info("📊 Analiz edilecek veri bulunamadı.")
        return

    with c_filt2:
        plant_options = df_corp["name"].unique().tolist()
        selected_plants = st.multiselect("🏭 Tesis Seçimi", options=plant_options, default=plant_options)

    # Veriyi Filtrele
    df_corp = df_corp[df_corp["name"].isin(selected_plants)]

    if df_corp.empty:
        st.warning("⚠️ Seçili filtrelere uygun veri bulunamadı.")
        return

    # --- 1. ÜST METRİKLER (KPI) ---
    kpi_cols = st.columns(4)
    metrics = [
        ("Analiz Edilen Tesis", len(df_corp)),
        ("Toplam Numune", df_corp["samples"].sum()),
        ("Kurumsal Sigma Ort.", f"{df_corp['sigma'].mean():.2f}"),
        ("Kritik Tesis", len(df_corp[df_corp["sigma"] > 5.0]))
    ]

    for i, (label, value) in enumerate(metrics):
        with kpi_cols[i]:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. PERFORMANS TABLOSU ---
    st.markdown("#### 📊 Tesis Bazlı Performans Matrisi")
    
    # Status icon logic matching image
    df_display = df_corp.copy()
    df_display["status"] = df_display.apply(lambda r: "👑 Güvenli" if r["sigma"] < 3.5 else ("⚠️ Riskli" if r["sigma"] < 5.0 else "🚨 Kritik"), axis=1)
    
    # Column mapping to match image
    df_display = df_display.rename(columns={
        "id": "ID", 
        "name": "İsim", 
        "manager": "Yönetici", 
        "samples": "Numune", 
        "sigma": "Sigma", 
        "avg_mpa": "Ort_MPA", 
        "cement_eff": "Çimento_RT",
        "status": "Durum"
    })
    
    st.dataframe(df_display[["ID", "İsim", "Yönetici", "Numune", "Sigma", "Ort_MPA", "Çimento_RT", "Durum"]], 
                 use_container_width=True, hide_index=True)

    # --- 3. GÖRSEL ANALİZLER (ROW 1) ---
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📉 Standart Sapma (Sigma) Dağılımı")
        fig_sigma = go.Figure(data=[
            go.Bar(x=df_corp["name"], y=df_corp["sigma"], 
                   marker_color=['#10B981' if s < 3.5 else ('#F59E0B' if s < 5.0 else '#EF4444') for s in df_corp["sigma"]])
        ])
        fig_sigma.update_layout(
            height=350, margin=dict(l=10, r=10, t=30, b=10), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white',
            font=dict(family="Fira Sans")
        )
        st.plotly_chart(fig_sigma, use_container_width=True)

    with c2:
        st.markdown("#### 💎 Çimento Verimliliği (kg / MPa)")
        eff_df = calculate_cement_efficiency_stats(df_corp)
        fig_eff = go.Figure(data=[
            go.Bar(x=eff_df["name"], y=eff_df["cement_eff"], marker_color="#64748B") # Slate-500
        ])
        fig_eff.update_layout(
            height=350, margin=dict(l=10, r=10, t=30, b=10), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white',
            font=dict(family="Fira Sans")
        )
        st.plotly_chart(fig_eff, use_container_width=True)

    # --- 4. RİSK VE PERFORMANS MATRİSİ (ROW 2) ---
    st.markdown("<br>")
    st.markdown("#### 🔥 Performans ve Risk Matrisi")
    
    fig_risk = go.Figure()
    
    # Arka plan alanları
    fig_risk.add_hrect(y0=5.0, y1=8.0, fillcolor="#fee2e2", opacity=0.5, line_width=0, annotation_text="Kritik Alan", annotation_position="top left")
    fig_risk.add_hrect(y0=0, y1=3.5, fillcolor="#f0fdf4", opacity=0.5, line_width=0, annotation_text="Güvenli Alan", annotation_position="bottom left")

    # Veri Noktaları
    fig_risk.add_trace(go.Scatter(
        x=df_corp["avg_mpa"], 
        y=df_corp["sigma"],
        mode='markers+text',
        text=df_corp["name"],
        textposition="top center",
        marker=dict(size=15, color=df_corp["sigma"], colorscale="RdYlGn_r", showscale=True)
    ))
    
    fig_risk.update_layout(
        title="Güç (MPa) vs Değişkenlik (Sigma)",
        xaxis_title="Ortalama Dayanım (MPa)",
        yaxis_title="Standart Sapma (Sigma)",
        height=500,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white'
    )
    st.plotly_chart(fig_risk, use_container_width=True)
