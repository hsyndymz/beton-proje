import sys
import os
import hashlib

# Add project root to path
sys.path.append(os.getcwd())

try:
    from logic.auth_manager import check_password
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("Successfully imported check_password")

password = "OldPassword123"
old_hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Generated Hash: {old_hash}")
print(f"Hash Length: {len(old_hash)}")

is_valid, migration = check_password(password, old_hash)
print(f"Result: {is_valid}, {migration}")

if is_valid and migration:
    print("SUCCESS")
else:
    print("FAILURE")
