import streamlit as st
import time
import json
from typing import Any, Optional, Dict, Callable
from functools import wraps
from logic.logger import logger

class SimpleCache:
    """Basit bir cache sistemi için"""
    
    def __init__(self, ttl: int = 300):  # 5 dakika default TTL
        self.ttl = ttl
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache'e veri yaz"""
        self._cache[key] = (value, time.time())
    
    def clear(self, pattern: Optional[str] = None):
        """Cache'i temizle"""
        if pattern:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()
    
    def size(self) -> int:
        """Cache boyutu"""
        return len(self._cache)

# Global cache instance
cache = SimpleCache()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Cache decorator"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache key oluştur
            cache_key = f"{key_prefix}_{func.__name__}_{str(args)}_{str(kwargs)}"
            cache_key = cache_key.replace(" ", "_").replace("/", "_")
            
            # Cache'den kontrol et
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Fonksiyonu çalıştır ve sonucu cache'e yaz
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"Cache set for {func.__name__}")
            
            return result
        return wrapper
    return decorator

# Session state cache utilities
def session_cache(key: str, default_value=None, ttl: int = 300):
    """Session state tabanlı cache"""
    cache_key = f"cache_{key}"
    
    # Cache kontrolü
    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        if time.time() - cached_data['timestamp'] < ttl:
            return cached_data['value']
    
    # Default değer döndür
    return default_value

def session_cache_set(key: str, value: Any):
    """Session state cache'e yaz"""
    cache_key = f"cache_{key}"
    st.session_state[cache_key] = {
        'value': value,
        'timestamp': time.time()
    }

def session_cache_clear(pattern: Optional[str] = None):
    """Session state cache temizle"""
    keys_to_delete = []
    for key in st.session_state.keys():
        if key.startswith("cache_"):
            if pattern is None or pattern in key:
                keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]

# Veri yönetimi için cache yardımcıları
def cache_project_data(plant_id: str, project_name: str, data: Dict):
    """Proje verisini cache'le"""
    cache_key = f"project_{plant_id}_{project_name}"
    cache.set(cache_key, data)

def get_cached_project_data(plant_id: str, project_name: str) -> Optional[Dict]:
    """Cache'den proje verisi al"""
    cache_key = f"project_{plant_id}_{project_name}"
    return cache.get(cache_key)

def cache_qc_history(plant_id: str, qc_data: list):
    """QC geçmişini cache'le"""
    cache_key = f"qc_history_{plant_id}"
    cache.set(cache_key, qc_data)

def get_cached_qc_history(plant_id: str) -> Optional[list]:
    """Cache'den QC geçmişi al"""
    cache_key = f"qc_history_{plant_id}"
    return cache.get(cache_key)

# Cache yönetimi için Streamlit widget'ları
def render_cache_controls():
    """Cache kontrol paneli"""
    if st.sidebar.checkbox("🔧 Cache Controls", help="Cache yönetimi"):
        st.sidebar.markdown("#### Cache Bilgileri")
        st.sidebar.metric("Cache Boyutu", cache.size())
        
        col_clear1, col_clear2 = st.sidebar.columns(2)
        
        with col_clear1:
            if st.button("🗑️ Tümünü Temizle", key="clear_all_cache"):
                cache.clear()
                session_cache_clear()
                st.success("✅ Cache temizlendi!")
                st.rerun()
        
        with col_clear2:
            if st.button("🔄 Sadece Projeler", key="clear_project_cache"):
                cache.clear(pattern="project_")
                session_cache_clear("project_")
                st.success("✅ Proje cache temizlendi!")
                st.rerun()
        
        # Cache istatistikleri
        if st.sidebar.checkbox("📊 Cache Stats"):
            st.sidebar.json({
                "memory_cache_size": cache.size(),
                "session_cache_keys": len([k for k in st.session_state.keys() if k.startswith("cache_")])
            })

# Cache invalidation için event handlers
def invalidate_project_cache(plant_id: str, project_name: str):
    """Proje cache'ini geçersiz kıl"""
    cache_key = f"project_{plant_id}_{project_name}"
    if cache_key in cache._cache:
        del cache._cache[cache_key]
    
    session_cache_clear(f"project_{plant_id}_{project_name}")
    logger.info(f"Invalidated cache for project: {project_name}", plant=plant_id)

def invalidate_qc_cache(plant_id: str):
    """QC cache'ini geçersiz kıl"""
    cache.clear(pattern="qc_history_")
    session_cache_clear("qc_history_")
    logger.info(f"Invalidated QC cache for plant: {plant_id}", plant=plant_id)
