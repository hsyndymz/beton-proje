import logging
import os
from datetime import datetime
from typing import Optional

class BetonLogger:
    """Beton Tasarım Programı için özel logger"""
    
    def __init__(self, name: str = "beton_tasarim"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Log dosyası yoksa oluştur
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Log handler'ları kur"""
        # Log dosyası
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f"beton_{datetime.now().strftime('%Y%m%d')}.log")
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # DEBUG seviyesinde
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Logger seviyesini DEBUG olarak ayarla
        self.logger.setLevel(logging.DEBUG)
    
    def info(self, message: str, user: Optional[str] = None, plant: Optional[str] = None):
        """Bilgi log'u"""
        extra_info = []
        if user:
            extra_info.append(f"User:{user}")
        if plant:
            extra_info.append(f"Plant:{plant}")
        
        if extra_info:
            message = f"[{' '.join(extra_info)}] {message}"
        
        self.logger.info(message)
    
    def debug(self, message: str, user: Optional[str] = None, plant: Optional[str] = None):
        """Debug log'u"""
        extra_info = []
        if user:
            extra_info.append(f"User:{user}")
        if plant:
            extra_info.append(f"Plant:{plant}")
        
        if extra_info:
            message = f"[{' '.join(extra_info)}] {message}"
        
        self.logger.debug(message)
    
    def warning(self, message: str, user: Optional[str] = None):
        """Uyarı log'u"""
        if user:
            message = f"[User:{user}] {message}"
        self.logger.warning(message)
    
    def error(self, message: str, user: Optional[str] = None, exception: Optional[Exception] = None):
        """Hata log'u"""
        if user:
            message = f"[User:{user}] {message}"
        
        if exception:
            message = f"{message} - Exception: {str(exception)}"
        
        self.logger.error(message)
    
    def security(self, message: str, user: Optional[str] = None, ip: Optional[str] = None):
        """Güvenlik log'u"""
        extra_info = ["SECURITY"]
        if user:
            extra_info.append(f"User:{user}")
        if ip:
            extra_info.append(f"IP:{ip}")
        
        message = f"[{' '.join(extra_info)}] {message}"
        self.logger.warning(message)

# Global logger instance
logger = BetonLogger()
