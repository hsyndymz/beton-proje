import streamlit as st
import traceback
from functools import wraps
from logic.logger import logger

class BetonException(Exception):
    """Beton Tasarım Programı için özel exception"""
    pass

def handle_exceptions(show_error_to_user: bool = True, log_error: bool = True):
    """Global exception handler decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BetonException as e:
                # Özel hatalar
                if log_error:
                    user = st.session_state.get('username', 'unknown')
                    logger.error(f"BetonException in {func.__name__}: {str(e)}", user=user)
                
                if show_error_to_user:
                    st.error(f"⚠️ {str(e)}")
                return None
            except Exception as e:
                # Beklenmedik hatalar
                error_msg = f"Beklenmedik bir hata oluştu: {str(e)}"
                
                if log_error:
                    user = st.session_state.get('username', 'unknown')
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}", user=user, exception=e)
                
                if show_error_to_user:
                    st.error(f"❌ {error_msg}")
                    
                    # Debug modunda detay göster
                    if st.session_state.get('debug_mode', False):
                        with st.expander("🔍 Hata Detayları"):
                            st.code(traceback.format_exc())
                
                return None
        return wrapper
    return decorator

def safe_execute(func, *args, **kwargs):
    """Güvenli fonksiyon çalıştırıcı"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execute failed for {func.__name__}: {str(e)}", exception=e)
        return None

def validate_input(value, field_name: str, min_val=None, max_val=None, required=True):
    """Input validasyonu"""
    if required and (value is None or value == ""):
        raise BetonException(f"{field_name} alanı zorunludur.")
    
    if value is None:
        return None
    
    try:
        # Sayısal değerler için
        if min_val is not None or max_val is not None:
            num_val = float(value)
            
            if min_val is not None and num_val < min_val:
                raise BetonException(f"{field_name} minimum {min_val} olmalıdır.")
            
            if max_val is not None and num_val > max_val:
                raise BetonException(f"{field_name} maksimum {max_val} olmalıdır.")
            
            return num_val
        
        return value
    except ValueError:
        raise BetonException(f"{field_name} geçerli bir sayı olmalıdır.")

# Streamlit için global error handler
def setup_global_error_handler():
    """Streamlit için global error handler kur"""
    def handle_error(error):
        logger.error(f"Streamlit error: {str(error)}", exception=error)
        st.error("❌ Sistemde bir hata oluştu. Lütfen sayfayı yenileyin.")
    
    # Bu Streamlit'in error callback'i için kullanılabilir
    # st.set_option('logger.error', handle_error)
