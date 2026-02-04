"""
🔐 Encryption - تشفير البيانات
==============================
نظام تشفير البيانات الحساسة في قاعدة البيانات.
"""

import os
import base64
import json
from typing import Any, Optional

# محاولة استيراد مكتبة التشفير
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed. Run: pip install cryptography")


class DataEncryption:
    """مدير التشفير"""
    
    def __init__(self, password: str = None):
        """
        تهيئة التشفير.
        
        Args:
            password: كلمة مرور للتشفير (اختياري - سيتم إنشاء مفتاح تلقائي)
        """
        self._key = None
        self._fernet = None
        self._key_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "data", 
            ".encryption_key"
        )
        
        if CRYPTO_AVAILABLE:
            if password:
                self._key = self._derive_key(password)
            else:
                self._key = self._load_or_create_key()
            
            self._fernet = Fernet(self._key)
    
    def _derive_key(self, password: str) -> bytes:
        """اشتقاق مفتاح من كلمة مرور"""
        salt = b'jarvis_ai_salt_2024'  # ثابت للبساطة
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _load_or_create_key(self) -> bytes:
        """تحميل المفتاح أو إنشاء جديد"""
        if os.path.exists(self._key_file):
            with open(self._key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self._key_file), exist_ok=True)
            with open(self._key_file, 'wb') as f:
                f.write(key)
            print(f"🔐 تم إنشاء مفتاح تشفير جديد")
            return key
    
    def is_available(self) -> bool:
        """فحص توفر التشفير"""
        return CRYPTO_AVAILABLE and self._fernet is not None
    
    def encrypt(self, data: str) -> str:
        """
        تشفير نص.
        
        Args:
            data: النص للتشفير
            
        Returns:
            النص المشفر (base64)
        """
        if not self.is_available():
            return data  # إرجاع بدون تشفير
        
        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('ascii')
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        فك تشفير نص.
        
        Args:
            encrypted_data: النص المشفر
            
        Returns:
            النص الأصلي
        """
        if not self.is_available():
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('ascii'))
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            # قد يكون النص غير مشفر أصلاً
            return encrypted_data
    
    def encrypt_dict(self, data: dict) -> str:
        """تشفير dictionary كـ JSON"""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """فك تشفير dictionary"""
        try:
            json_str = self.decrypt(encrypted_data)
            return json.loads(json_str)
        except:
            return {}


# Singleton
_encryption = None

def get_encryption() -> DataEncryption:
    """جلب مدير التشفير"""
    global _encryption
    if _encryption is None:
        _encryption = DataEncryption()
    return _encryption


# دوال مختصرة
def encrypt(data: str) -> str:
    """تشفير نص"""
    return get_encryption().encrypt(data)

def decrypt(data: str) -> str:
    """فك تشفير نص"""
    return get_encryption().decrypt(data)
