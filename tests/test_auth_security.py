import unittest
import time
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.auth_manager import hash_password, check_password, check_session_timeout, SESSION_TIMEOUT_MINUTES
from logic.input_validator import sanitize_input, validate_username
import hashlib

class TestSecurity(unittest.TestCase):
    def test_bcrypt_hashing(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ or $2a$
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        self.assertNotEqual(hashed, password)
        
        # Verify correct password
        is_valid, migration = check_password(password, hashed)
        self.assertTrue(is_valid)
        self.assertFalse(migration) # No migration needed for new hash
        
        # Verify wrong password
        is_valid, _ = check_password("WrongPass", hashed)
        self.assertFalse(is_valid)

    def test_migration_logic(self):
        password = "OldPassword123"
        # Simulate old SHA-256 hash
        old_hash = hashlib.sha256(password.encode()).hexdigest()
        
        is_valid, migration = check_password(password, old_hash)
        self.assertTrue(is_valid)
        self.assertTrue(migration) # Migration SHOULD be needed

    def test_input_sanitization(self):
        script_input = "<script>alert('xss')</script>"
        clean = sanitize_input(script_input)
        # html.escape escapes single quotes by default in Python 3
        expected = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        self.assertEqual(clean, expected)
        
        normal_input = "Hello World"
        self.assertEqual(sanitize_input(normal_input), "Hello World")

    def test_session_timeout(self):
        # Current activity -> Valid
        now = datetime.now()
        self.assertFalse(check_session_timeout(now))
        
        # Old activity -> Timeout
        old = now - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 5)
        self.assertTrue(check_session_timeout(old))
        
        # None -> Timeout
        self.assertTrue(check_session_timeout(None))

if __name__ == '__main__':
    unittest.main()
