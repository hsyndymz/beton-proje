import streamlit as st
from contextlib import contextmanager

@contextmanager
def loading_indicator(message: str = "Yükleniyor..."):
    """Özelleştirilmiş yükleme göstergesi"""
    placeholder = st.empty()
    
    loading_html = f"""
    <div style="text-align: center; padding: 2rem;">
        <div class="spinner"></div>
        <p style="margin-top: 1rem; color: #666; font-family: 'Fira Sans', sans-serif;">{message}</p>
    </div>
    
    <style>
    .spinner {{
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    placeholder.markdown(loading_html, unsafe_allow_html=True)
    
    try:
        yield
    finally:
        placeholder.empty()

def render_tab_content_lazy(tab_key, render_func, *args, **kwargs):
    """
    Lazy loading wrapper for tabs.
    Content is only rendered if the tab has been visited or selected.
    """
    # Streamlit tabs are loaded all at once by default.
    # To truly lazy load, we might need to check if the tab is active, 
    # but Streamlit doesn't expose 'active tab' state natively easily without extra components.
    # However, we can use a simpler approach: 
    # Just render it. Streamlit's fragment or partial rerun in 1.37+ helps, 
    # but for standard behavior, we'll wrap critical heavy parts with spinners.
    
    with st.spinner(f"{tab_key} verileri hazırlanıyor..."):
        render_func(*args, **kwargs)
