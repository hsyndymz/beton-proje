import json
import os
import hashlib

USERS_FILE = "users.json"

def hash_password(password):
    """Şifreyi güvenli hale getirir (SHA-256)."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
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
            return {"error": "Hesabınız henüz onaylanmamış."}
        stored_h = u_data["password"]
        if stored_h == hash_password(password) or stored_h == "hashed_placeholder":
            if stored_h == "hashed_placeholder":
                users[username]["password"] = hash_password(password)
                save_users(users)
            return u_data
    return None

def add_user(username, password, role="User", full_name="", status="active", assigned_plants=None):
    users = load_users()
    if username in users: return False, "Bu kullanıcı zaten mevcut."
    users[username] = {
        "password": hash_password(password),
        "role": role, "full_name": full_name, "status": status,
        "assigned_plants": assigned_plants if assigned_plants else ["merkez"]
    }
    save_users(users)
    return True, "Kullanıcı eklendi."

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
