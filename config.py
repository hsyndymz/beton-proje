import os
from typing import Optional

class Config:
    """Uygulama yapılandırma sınıfı"""
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "beton-tasarim-secret-key-2024")
    
    # Database
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Gerekli environment variables'ı kontrol et"""
        try:
            from dotenv import load_dotenv
            dotenv_available = True
        except ImportError:
            dotenv_available = False
        
        if not dotenv_available:
            print("WARNING: python-dotenv yuklu degil. .env dosyasi kullanilamayacak.")
            return False
            
        missing = []
        if not cls.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        if not cls.DEEPSEEK_API_KEY:
            missing.append("DEEPSEEK_API_KEY")
        
        if missing:
            print(f"WARNING: Eksik Environment Variables: {', '.join(missing)}")
            print("API anahtarları olmadan AI ozellikleri calismayacaktır.")
            print("INFO: .env dosyasi olusturun veya environment variables'i ayarlayin.")
        
        return len(missing) == 0
