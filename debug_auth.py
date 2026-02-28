import hashlib
import sys
import os

# Mock the function from auth_manager to avoid importing if there are issues
def check_password_mock(plain_password, stored_password):
    print(f"DEBUG: Checking '{plain_password}' vs '{stored_password}'")
    print(f"DEBUG: Length of stored: {len(stored_password)}")
    print(f"DEBUG: '$' in stored: {'$' in stored_password}")
    
    if len(stored_password) == 64 and "$" not in stored_password:
        print("DEBUG: Detected as SHA-256 candidate")
        old_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        print(f"DEBUG: Calculated old hash: {old_hash}")
        match = old_hash == stored_password
        print(f"DEBUG: Match: {match}")
        return match, True
    
    print("DEBUG: Not an SHA-256 candidate, trying bcrypt...")
    return False, False

# Test
password = "OldPassword123"
old_hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Test Hash: {old_hash}")
res = check_password_mock(password, old_hash)
print(f"Result: {res}")
