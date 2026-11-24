
import hashlib

class Hasher:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash mật khẩu sử dụng SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Xác minh mật khẩu"""
        return Hasher.hash_password(plain_password) == hashed_password