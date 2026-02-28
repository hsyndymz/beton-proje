import html
import re

def sanitize_input(user_input: str, max_length: int = 500) -> str:
    """
    Kullanıcı girdisini XSS ve diğer saldırılara karşı temizler.
    
    Args:
        user_input (str): Temizlenecek metin.
        max_length (int): İzin verilen maksimum karakter sayısı.
        
    Returns:
        str: Temizlenmiş metin.
    """
    if not user_input:
        return ""
        
    # 1. HTML Karakterlerini Escape Et (XSS Koruması)
    # <script> -> &lt;script&gt;
    sanitized = html.escape(str(user_input))
    
    # 2. Tehlikeli Karakterleri Kaldır (Opsiyonel, duruma göre esnetilebilir)
    # Sadece temel güvenli karakterlere izin ver (Harf, Rakam, Noktalama, Boşluk)
    # Bu regex çok katı olabilir, proje ihtiyacına göre gevşetilebilir.
    # Şimdilik sadece bariz tehlikeli olabilecek karakterleri filtreleyelim.
    # SQL Injection için basit bir önlem olarak ' ve " işaretlerini kontrol edebiliriz ama
    # JSON veritabanı kullandığımız için SQLi riski düşük.
    
    # 3. Uzunluk Kontrolü
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        
    return sanitized

def validate_username(username: str) -> tuple[bool, str]:
    """Kullanıcı adı validasyonu"""
    if not username or len(username) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalıdır."
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Kullanıcı adı sadece harf, rakam, - ve _ içerebilir."
    
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    """Şifre karmaşıklık kontrolü"""
    if len(password) < 6:
        return False, "Şifre en az 6 karakter olmalıdır."
    
    # İsteğe bağlı: Daha katı kurallar eklenebilir
    # if not re.search(r"[A-Z]", password): ...
    # if not re.search(r"[0-9]", password): ...
    
    return True, ""
