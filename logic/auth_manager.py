import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import bcrypt
try:
    from logic.input_validator import validate_username, validate_password
except ImportError:
    # Fallback if file not found during migration
    def validate_username(u): return True, ""
    def validate_password(p): return True, ""

USERS_FILE = "users.json"
SESSION_TIMEOUT_MINUTES = 60

def hash_password(password):
    """
    Şifreyi güvenli hale getirir (bcrypt).
    Salt otomatik olarak oluşturulur ve hash'in içine gömülür.
    """
    # bcrypt bytes ister, bu yüzden encode ediyoruz
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_password, stored_password):
    """
    Şifre doğrulama (bcrypt veya eski SHA-256).
    """
    # 1. Eski SHA-256 Hash Kontrolü (Migration için)
    # Eski hash'ler hex string (64 karakter) formatındadır ve $ içermez
    if len(stored_password) == 64 and "$" not in stored_password:
        old_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return old_hash == stored_password, True # True = Migration gerekli
        
    # 2. Bcrypt Kontrolü
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8')), False
    except ValueError:
        return False, False

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                return {}
                
            # Backward compatibility
            modified = False
            for u in users:
                if "status" not in users[u]:
                    users[u]["status"] = "active"
                    modified = True
                if "assigned_plants" not in users[u]:
                    # Varsayılan olarak Merkez santrali ata
                    users[u]["assigned_plants"] = ["merkez"]
                    modified = True
            if modified: save_users(users)
            return users
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def check_login(username, password):
    users = load_users()
    if username in users:
        u_data = users[username]
        if u_data.get("status") != "active":
            return {"error": "Hesabınız henüz onaylanmamış veya pasif durumda."}
            
        stored_h = u_data["password"]
        
        # Geçici placeholder kontrolü
        if stored_h == "hashed_placeholder":
            users[username]["password"] = hash_password(password)
            save_users(users)
            return u_data
            
        is_valid, migration_needed = check_password(password, stored_h)
        
        if is_valid:
            # Otomatik Migration: Eğer eski hash ise, yenisiyle güncelle
            if migration_needed:
                print(f"INFO: Kullanıcı '{username}' için şifre güvenliği yükseltiliyor (SHA256 -> Bcrypt)...")
                users[username]["password"] = hash_password(password)
                save_users(users)
                
            return u_data
            
    return None

def add_user(username, password, role="User", full_name="", status="active", assigned_plants=None):
    valid, msg = validate_username(username)
    if not valid: return False, msg
    
    valid, msg = validate_password(password)
    if not valid: return False, msg

    users = load_users()
    if username in users: return False, "Bu kullanıcı zaten mevcut."
    
    users[username] = {
        "password": hash_password(password),
        "role": role, 
        "full_name": full_name, 
        "status": status,
        "assigned_plants": assigned_plants if assigned_plants else ["merkez"]
    }
    save_users(users)
    return True, "Kullanıcı başarıyla eklendi."

def register_user(username, password, full_name):
    return add_user(username, password, role="User", full_name=full_name, status="pending")

def update_user(username, role=None, status=None, full_name=None, assigned_plants=None):
    """Mevcut bir kullanıcının bilgilerini günceller."""
    users = load_users()
    if username not in users:
        return False, "Kullanıcı bulunamadı."
    
    if role: users[username]["role"] = role
    if status: users[username]["status"] = status
    if full_name: users[username]["full_name"] = full_name
    if assigned_plants is not None: users[username]["assigned_plants"] = assigned_plants
    
    save_users(users)
    return True, f"{username} başarıyla güncellendi."

def delete_user(username):
    users = load_users()
    if username in users:
        if username == "hsyndymz": # Ana admin silinemez
            return False, "Ana yönetici silinemez!"
        del users[username]
        save_users(users)
        return True, "Kullanıcı silindi."
    return False, "Kullanıcı bulunamadı."

# --- Session Management ---

def create_session_token():
    return secrets.token_urlsafe(32)

def check_session_timeout(last_activity_timestamp):
    if not last_activity_timestamp:
        return True
    
    now = datetime.now()
    # Eğer timestamp string gelirse (json load durumunda) datetime'a çevir
    if isinstance(last_activity_timestamp, str):
        try:
            last_activity_timestamp = datetime.fromisoformat(last_activity_timestamp)
        except ValueError:
            return True 
            
    diff = now - last_activity_timestamp
    if diff > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        return True
    return False
