import os
from typing import Optional
from cryptography.fernet import Fernet

class Config:
    """Uygulama yapılandırma sınıfı (Güvenli)"""
    
    # Encryption key (production'da environment'tan al)
    _ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "beton-tasarim-secret-key-2024")
    
    # Sayfa zaman aşımı (dakika)
    SESSION_TIMEOUT_MINUTES = 60
    
    # Database
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def _get_cipher(cls):
        """Şifreleme nesnesini döndürür. Key yoksa oluşturur (Dev modu için)."""
        if not cls._ENCRYPTION_KEY:
            # Development için otomatik key oluştur ve uyar
            key = Fernet.generate_key()
            cls._ENCRYPTION_KEY = key.decode()
            if cls.DEBUG:
                print(f"UYARI: ENCRYPTION_KEY bulunamadı. Geçici key oluşturuldu: {cls._ENCRYPTION_KEY}")
        return Fernet(cls._ENCRYPTION_KEY.encode())

    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """
        API key'i güvenli şekilde döndürür.
        Önce şifreli env var'a bakar, yoksa düz metin env var'a bakar.
        """
        provider = provider.upper()
        
        # 1. Şifreli Key Kontrolü
        encrypted_key = os.getenv(f"{provider}_API_KEY_ENCRYPTED")
        if encrypted_key:
            try:
                cipher = cls._get_cipher()
                return cipher.decrypt(encrypted_key.encode()).decode()
            except Exception as e:
                print(f"HATA: {provider} şifreli anahtar çözülemedi: {e}")
        
        # 2. Düz Metin Kontrolü (Fallback)
        return os.getenv(f"{provider}_API_KEY")
    
    @classmethod
    def encrypt_value(cls, value: str) -> str:
        """Herhangi bir hassas veriyi şifreler."""
        if not value: return ""
        cipher = cls._get_cipher()
        return cipher.encrypt(value.encode()).decode()

    @classmethod
    def validate(cls):
        """Gerekli environment variables'ı kontrol et"""
        try:
            from dotenv import load_dotenv
            # load_dotenv() # Streamlit usually handles this or system envs
            dotenv_available = True
        except ImportError:
            dotenv_available = False
        
        if not dotenv_available:
            pass # Sessiz ol, streamlit cloud vs olabilir.
            
        missing = []
        if not cls.GOOGLE_API_KEY and not os.getenv("GOOGLE_API_KEY_ENCRYPTED"):
            missing.append("GOOGLE_API_KEY")
        
        if missing and cls.DEBUG:
            print(f"UYARI: Eksik Environment Variables: {', '.join(missing)}")
        
        return len(missing) == 0
