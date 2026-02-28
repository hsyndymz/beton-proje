import unittest
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit before importing logic modules to test @st.cache_data behavior
import streamlit as st
from unittest.mock import MagicMock

# Mock st.cache_data decorator
def mock_cache_data(ttl=None):
    def decorator(func):
        cache = {}
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            wrapper.cache = cache # Expose cache for inspection
            return result
        
        wrapper.clear = lambda: cache.clear()
        return wrapper
    return decorator

# Patch st.cache_data
st.cache_data = mock_cache_data

from logic.data_manager import santralleri_yukle, santral_kaydet, veriyi_yukle, veriyi_kaydet
from logic.ocak_manager import ocaklari_yukle, ocak_kaydet

class TestPerformance(unittest.TestCase):
    def setUp(self):
        # Clear caches before each test
        santralleri_yukle.clear()
        veriyi_yukle.clear()
        ocaklari_yukle.clear()

    def test_santral_caching(self):
        # First call should load data
        data1 = santralleri_yukle()
        
        # Modify the file bypass (simulate external change, though here we test logic flow)
        # Verify second call returns cached object
        data2 = santralleri_yukle()
        self.assertIs(data1, data2, "Should return cached object reference")
        
        # Modify via manager should clear cache
        santral_kaydet("test_id", {"name": "Test"})
        
        data3 = santralleri_yukle()
        self.assertIsNot(data1, data3, "Should reload after save (cache cleared)")

    def test_ocak_caching(self):
        data1 = ocaklari_yukle()
        data2 = ocaklari_yukle() 
        self.assertIs(data1, data2)
        
        ocak_kaydet("ocak_1", "Test Ocak")
        data3 = ocaklari_yukle()
        self.assertIsNot(data1, data3)

if __name__ == '__main__':
    unittest.main()
